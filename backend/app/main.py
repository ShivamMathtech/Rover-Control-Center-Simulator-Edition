import asyncio, csv, io, json, os, secrets, time, uuid
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Response, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from .storage import Store
from .auth import Auth, password_hash
from .schemas import Login, UserCreate, Command, Mode, Mission, Fault, Settings
from .controller import Controller, Rejected
from .drivers import SimulationPerception

ROOT=Path(__file__).resolve().parents[2]

def create_app(db_url=None):
    @asynccontextmanager
    async def lifespan(app):
        if os.getenv('MODE','simulation')!='simulation':
            raise RuntimeError('Hardware mode is not implemented. Configure and validate a real driver before enabling it.')
        app.state.store=Store(db_url);store=app.state.store
        if not store.list('user:'):
            password=os.getenv('ADMIN_PASSWORD','')
            if len(password)<12:raise RuntimeError('Set ADMIN_PASSWORD to at least 12 characters before first launch')
            store.set('user:admin',{'username':'admin','role':'ADMIN','hash':password_hash(password)})
        app.state.auth=Auth(store)
        def event(action,detail):store.append('events',{'user':'system','action':action,'detail':detail})
        app.state.controller=Controller(Settings(**store.get('settings',{})),event=event)
        for mission in store.list('mission:'):
            if mission.get('state') in ('RUNNING','PAUSED'):
                mission['state']='ABORTED';store.set('mission:'+mission['id'],mission)
        if not store.list('mission:'):
            store.set('mission:demo',{'id':'demo','name':'Inspection loop','speed':0.8,'state':'READY','waypoints':[{'x':0,'y':10,'wait':1},{'x':10,'y':10,'wait':1},{'x':10,'y':0,'wait':1},{'x':0,'y':0,'wait':0}]})
        app.state.rates={}
        async def loop():
            last=time.monotonic();sample=0;prune=0;previous=None
            while True:
                await asyncio.sleep(0.05)
                now=time.monotonic();app.state.controller.tick(min(now-last,0.2));last=now
                c=app.state.controller
                status=(c.mission['id'],c.mission_state) if c.mission else None
                if status and status!=previous:
                    m=store.get('mission:'+status[0])
                    if m:m['state']=status[1];store.set('mission:'+m['id'],m)
                    previous=status
                if now-sample>=1:store.append('telemetry',c.snapshot());sample=now
                if now-prune>=60:store.prune();prune=now
        task=asyncio.create_task(loop())
        yield
        task.cancel()
        try:await task
        except asyncio.CancelledError:pass
        app.state.controller.driver.stop();store.engine.dispose()
    app=FastAPI(title='MathTech Rover Control Center',version='1.0.0-simulator',lifespan=lifespan)
    @app.exception_handler(Rejected)
    async def rejected(request,exc):return JSONResponse(status_code=409,content={'detail':str(exc)})
    def actor(request,write=False,admin=False):
        user=app.state.auth.require(request,['ADMIN'] if admin else ['ADMIN','OPERATOR'] if write else None)
        if write:
            key=request.cookies.get('rover_session');now=time.monotonic()
            times=[t for t in app.state.rates.get(key,[]) if now-t<1]
            if len(times)>=30:raise HTTPException(429,'Command rate exceeded')
            app.state.rates[key]=times+[now]
        return user
    def controlled(request):
        u=actor(request,True);app.state.controller.owned(request.cookies.get('rover_session'));return u
    def audit(user,action,detail=None):app.state.store.append('events',{'user':user['username'],'action':action,'detail':detail or {}})
    def result():return app.state.controller.snapshot()
    @app.get('/api/healthz')
    def health():return {'ok':True,'mode':'simulation'}
    @app.post('/api/auth/login')
    def login(data:Login,request:Request,response:Response):
        # JSON-only body plus Origin checking stops cross-site form login.
        origin=request.headers.get('origin')
        if origin and origin.rstrip('/')!=str(request.base_url).rstrip('/'):
            raise HTTPException(403,'Cross-origin login rejected')
        token=app.state.auth.login(data.username,data.password,request.client.host if request.client else 'local')
        secure=os.getenv('COOKIE_SECURE','false').lower()=='true'
        response.set_cookie('rover_session',token,httponly=True,samesite='strict',secure=secure,max_age=28800)
        response.set_cookie('rover_csrf',secrets.token_urlsafe(24),httponly=False,samesite='strict',secure=secure,max_age=28800)
        user=app.state.auth.user(token);audit(user,'auth.login');return user
    @app.get('/api/auth/me')
    def me(request:Request):return actor(request)
    @app.post('/api/auth/logout')
    def logout(request:Request,response:Response):
        u=actor(request);token=request.cookies.get('rover_session')
        if app.state.controller.owner==token:
            app.state.controller.stop('Operator logged out',True);app.state.controller.owner=None
        app.state.auth.sessions.pop(token,None);audit(u,'auth.logout')
        response.delete_cookie('rover_session');response.delete_cookie('rover_csrf');return {'ok':True}
    @app.post('/api/users',status_code=201)
    def users(data:UserCreate,request:Request):
        u=actor(request,True,True)
        if app.state.store.get('user:'+data.username):raise HTTPException(409,'User already exists')
        app.state.store.set('user:'+data.username,{'username':data.username,'role':data.role,'hash':password_hash(data.password)})
        audit(u,'user.created',{'username':data.username,'role':data.role});return {'username':data.username,'role':data.role}
    @app.get('/api/users')
    def list_users(request:Request):
        actor(request,admin=True);return [{k:u[k] for k in ('username','role')} for u in app.state.store.list('user:')]
    @app.get('/api/rovers')
    def rovers(request:Request):actor(request);return [result()]
    @app.get('/api/rovers/rover-01')
    @app.get('/api/rovers/rover-01/telemetry')
    def rover(request:Request):actor(request);return result()
    @app.get('/api/rovers/rover-01/sensors')
    def sensors(request:Request):actor(request);return result()['sensors']
    @app.get('/api/rovers/rover-01/health')
    def rover_health(request:Request):actor(request);return {k:'FAULT' if v else 'SIMULATED / OK' for k,v in app.state.controller.faults.items()}
    @app.post('/api/control/acquire')
    def acquire(request:Request):
        u=actor(request,True);app.state.controller.acquire(request.cookies.get('rover_session'));audit(u,'control.acquire');return result()
    @app.post('/api/control/heartbeat')
    def heartbeat(request:Request):actor(request,True);app.state.controller.heartbeat(request.cookies.get('rover_session'));return {'ok':True}
    @app.post('/api/rovers/rover-01/command')
    def command(data:Command,request:Request):
        u=controlled(request);c=app.state.controller;was_idle=c.state=='IDLE';c.command(data)
        if was_idle:audit(u,'control.manual_activation')
        return {'ok':True}
    @app.post('/api/rovers/rover-01/mode')
    def mode(data:Mode,request:Request):
        u=controlled(request);app.state.controller.change_mode(data.mode);audit(u,'mode.changed',data.model_dump());return result()
    @app.post('/api/rovers/rover-01/stop')
    def stop(request:Request):u=actor(request,True);app.state.controller.stop();audit(u,'control.stop');return result()
    @app.post('/api/rovers/rover-01/emergency-stop')
    def emergency(request:Request):u=actor(request,True);app.state.controller.stop('Emergency stop',True);audit(u,'safety.emergency_stop');return result()
    @app.post('/api/rovers/rover-01/reset')
    def reset(request:Request):u=controlled(request);app.state.controller.reset();audit(u,'safety.reset');return result()
    @app.get('/api/missions')
    def missions(request:Request):actor(request);return app.state.store.list('mission:')
    @app.post('/api/missions',status_code=201)
    def create_mission(data:Mission,request:Request):
        u=actor(request,True);m={'id':str(uuid.uuid4()),'state':'READY',**data.model_dump()};app.state.controller.validate_mission(m)
        app.state.store.set('mission:'+m['id'],m);audit(u,'mission.created',{'id':m['id']});return m
    def fetch_mission(id):
        m=app.state.store.get('mission:'+id)
        if not m:raise HTTPException(404,'Mission not found')
        return m
    def editable(id):
        c=app.state.controller
        if c.mission and c.mission['id']==id and c.mission_state in ('RUNNING','PAUSED'):raise HTTPException(409,'Abort the mission before editing')
    @app.put('/api/missions/{id}')
    def edit_mission(id:str,data:Mission,request:Request):
        u=actor(request,True);fetch_mission(id);editable(id)
        m={'id':id,'state':'READY',**data.model_dump()};app.state.controller.validate_mission(m);app.state.store.set('mission:'+id,m);audit(u,'mission.updated',{'id':id});return m
    @app.delete('/api/missions/{id}')
    def delete_mission(id:str,request:Request):
        u=actor(request,True);fetch_mission(id);editable(id);app.state.store.remove('mission:'+id);audit(u,'mission.deleted',{'id':id});return {'ok':True}
    @app.post('/api/missions/{id}/{action}')
    def mission_action(id:str,action:str,request:Request):
        u=controlled(request);m=fetch_mission(id);c=app.state.controller
        if action=='start':c.start(m)
        elif action in ('pause','resume','abort'):
            if not c.mission or c.mission['id']!=id:raise HTTPException(409,'Mission is not active')
            c.mission_action(action)
        else:raise HTTPException(404,'Unknown action')
        m['state']=c.mission_state;app.state.store.set('mission:'+id,m);audit(u,'mission.'+action,{'id':id});return result()
    @app.post('/api/rovers/rover-01/return-home')
    def home(request:Request):
        u=controlled(request);c=app.state.controller;c.check();c.stop('Return home requested');c.mode='AUTONOMOUS'
        m={'id':str(uuid.uuid4()),'name':'Return home','speed':min(0.8,c.settings.max_speed),'state':'READY','waypoints':[{'x':0,'y':0,'wait':0}]}
        app.state.store.set('mission:'+m['id'],m);c.start(m);c.state='RETURNING_HOME';audit(u,'control.return_home');return result()
    @app.get('/api/settings')
    def settings(request:Request):actor(request);return app.state.controller.settings.model_dump()
    @app.put('/api/settings')
    def set_settings(data:Settings,request:Request):
        u=actor(request,True,True);c=app.state.controller
        if c.state not in ('IDLE','SAFE_STOP'):raise HTTPException(409,'Stop rover before changing settings')
        if (c.driver.x**2+c.driver.y**2)**0.5>data.fence_radius:raise HTTPException(409,'Rover would be outside new fence')
        c.settings=data;app.state.store.set('settings',data.model_dump());audit(u,'settings.changed',data.model_dump());return data
    @app.post('/api/simulator/fault')
    def fault(data:Fault,request:Request):
        u=actor(request,True);c=app.state.controller;c.faults[data.name]=data.enabled
        if data.enabled and data.name!='camera':c.stop('Simulated '+data.name+' fault',True)
        audit(u,'simulator.fault',data.model_dump());return result()
    @app.get('/api/cameras')
    def cameras(request:Request):
        actor(request);return [{'id':n,'source':'SIMULATION','transport':'synthetic-canvas','status':'OFFLINE' if app.state.controller.faults['camera'] else 'SIMULATED','recording':False} for n in ['front','rear','left','right']]
    @app.get('/api/perception')
    def perception(request:Request):
        actor(request);return {'source':'SIMULATION','model_loaded':False,'detections':SimulationPerception().detect() if app.state.controller.faults['obstacle'] else []}
    @app.get('/api/logs')
    def logs(request:Request):actor(request);return app.state.store.history('events',86400,500)
    @app.get('/api/telemetry/history')
    def history(request:Request,seconds:int=300):actor(request);return app.state.store.history('telemetry',max(1,min(seconds,86400)),3600)
    @app.get('/api/telemetry/export')
    def export(request:Request,format:str='json',seconds:int=3600):
        actor(request);rows=app.state.store.history('telemetry',max(1,min(seconds,86400)),86400)
        if format=='json':return Response(json.dumps(rows),media_type='application/json',headers={'Content-Disposition':'attachment; filename="telemetry.json"'})
        if format!='csv':raise HTTPException(422,'Use csv or json')
        out=io.StringIO();w=csv.writer(out);w.writerow(['timestamp','x_m','y_m','heading_deg','speed_m_s','battery_pct','state','source'])
        for r in rows:w.writerow([r['timestamp'],r['position']['x'],r['position']['y'],r['position']['heading'],r['position']['speed'],r['sensors']['battery']['percent'],r['state'],r['source']])
        return Response(out.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="telemetry.csv"'})
    @app.websocket('/ws')
    async def websocket(ws:WebSocket):
        origin=ws.headers.get('origin');host=ws.headers.get('host')
        if origin and origin not in ('http://'+host,'https://'+host):await ws.close(code=1008);return
        try:app.state.auth.user(ws.cookies.get('rover_session'))
        except HTTPException:await ws.close(code=1008);return
        await ws.accept()
        try:
            while True:
                app.state.auth.user(ws.cookies.get('rover_session'))
                await ws.send_json({'type':'rover.telemetry','data':result()});await asyncio.sleep(0.2)
        except (WebSocketDisconnect,RuntimeError,HTTPException):
            try:await ws.close(code=1008)
            except RuntimeError:pass
    dist=ROOT/'frontend'/'dist'
    if dist.exists():
        app.mount('/assets',StaticFiles(directory=dist/'assets'),name='assets')
        @app.get('/{path:path}')
        def frontend(path:str):
            if path.startswith('api/'):raise HTTPException(404,'Unknown API route')
            return FileResponse(dist/'index.html')
    return app

app=create_app()
