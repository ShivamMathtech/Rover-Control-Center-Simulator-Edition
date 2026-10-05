"""Single-writer simulator and safety state machine; coordinates are metres from home."""
import math, time
from .drivers import SimulatorDriver
from .schemas import Settings

class Rejected(ValueError): pass
class Controller:
    def __init__(self,settings=None,clock=time.monotonic,event=None):
        self.settings=settings or Settings();self.clock=clock
        self.event=event or (lambda action,detail:None)
        self.driver=SimulatorDriver();self.mode='MANUAL';self.state='IDLE'
        self.latched=False;self.reason='';self.owner=None
        self.last_link=self.last_command=clock();self.last_sequence=-1
        self.faults={k:False for k in ['obstacle','gps','camera','battery','network','sensor','motor']}
        self.battery=96.0;self.mission=None;self.index=0;self.wait_until=None
        self.mission_state='IDLE';self.trail=[]
    def stop(self,reason='Operator stop',latch=False):
        self.driver.stop();self.reason=reason;self.latched=self.latched or latch
        self.state='SAFE_STOP' if self.latched else 'IDLE'
        if self.mission_state in ('RUNNING','PAUSED'):self.mission_state='ABORTED'
        self.event('safety.stop',{'reason':reason,'latched':self.latched})
    def check(self):
        if self.latched:raise Rejected('Safety stop is latched; clear faults and explicitly reset')
        if self.faults['network']:raise Rejected('Rover link unavailable')
        if self.faults['sensor'] or self.faults['motor']:raise Rejected('Critical sensor or motor unavailable')
        if self.faults['gps']:raise Rejected('GPS unavailable')
        if self.faults['battery'] or self.battery<=self.settings.low_battery:raise Rejected('Low battery')
        if self.faults['obstacle']:raise Rejected('Obstacle inside stop zone')
        if math.hypot(self.driver.x,self.driver.y)>self.settings.fence_radius:raise Rejected('Outside geofence')
    def acquire(self,owner):
        if self.owner and self.owner!=owner and self.clock()-self.last_link<self.settings.link_timeout:
            raise Rejected('Another operator holds control')
        if self.owner!=owner:
            self.stop('Control acquired');self.last_sequence=-1
        self.owner=owner;self.last_link=self.clock()
    def owned(self,owner):
        if owner!=self.owner:raise Rejected('Acquire control first')
        if self.clock()-self.last_link>self.settings.link_timeout:raise Rejected('Control lease expired; acquire again')
    def heartbeat(self,owner):
        self.owned(owner);self.last_link=self.clock()
    def change_mode(self,mode):
        self.check();self.stop('Mode changed');self.mode=mode
    def command(self,cmd):
        self.check()
        if self.mode not in ('MANUAL','ASSISTED'):raise Rejected('Manual command requires manual or assisted mode')
        if cmd.sequence<=self.last_sequence:raise Rejected('Stale or reordered command')
        if abs(time.time()-cmd.issued_at)>1.5:raise Rejected('Command timestamp expired')
        if abs(cmd.linear)>self.settings.max_speed:raise Rejected('Configured speed limit exceeded')
        self.last_sequence=cmd.sequence;self.last_command=self.clock()
        self.driver.set_velocity(cmd.linear,cmd.angular);self.state=self.mode
    def reset(self):
        was=self.latched;self.latched=False
        try:self.check()
        except Rejected:self.latched=was;raise
        self.stop('Safety reset; movement requires new input')
    def start(self,mission):
        self.check()
        if self.mode!='AUTONOMOUS':raise Rejected('Select autonomous mode first')
        if self.mission_state in ('RUNNING','PAUSED'):raise Rejected('Abort existing mission first')
        self.validate_mission(mission)
        self.mission=mission;self.index=0;self.wait_until=None
        self.mission_state='RUNNING';self.state='AUTONOMOUS'
    def validate_mission(self,m):
        if m['speed']>self.settings.max_speed:raise Rejected('Mission exceeds configured speed')
        if any(math.hypot(w['x'],w['y'])>self.settings.fence_radius-1 for w in m['waypoints']):
            raise Rejected('Waypoint outside geofence safety margin')
    def mission_action(self,action):
        if action=='pause' and self.mission_state=='RUNNING':
            self.mission_state='PAUSED';self.driver.stop();self.state='PAUSED';self.wait_until=None
        elif action=='resume' and self.mission_state=='PAUSED':
            self.check();self.mission_state='RUNNING';self.state='AUTONOMOUS'
        elif action=='abort' and self.mission_state in ('RUNNING','PAUSED'):self.stop('Mission aborted')
        else:raise Rejected('Invalid mission transition')
    def tick(self,dt):
        now=self.clock()
        if self.state in ('MANUAL','ASSISTED','AUTONOMOUS','RETURNING_HOME','PAUSED'):
            try:
                self.check()
                if now-self.last_link>self.settings.link_timeout:raise Rejected('Operator link timeout')
            except Rejected as exc:self.stop(str(exc),True)
        if self.state in ('MANUAL','ASSISTED') and now-self.last_command>self.settings.command_timeout:
            self.driver.stop();self.state='IDLE';self.reason='Dead-man command timeout'
        if self.mission_state=='RUNNING':
            w=self.mission['waypoints'][self.index]
            dx=w['x']-self.driver.x;dy=w['y']-self.driver.y;dist=math.hypot(dx,dy)
            if dist<0.35:
                self.driver.stop()
                if self.wait_until is None:self.wait_until=now+w.get('wait',0)
                if now>=self.wait_until:
                    self.index+=1;self.wait_until=None
                    if self.index==len(self.mission['waypoints']):
                        self.mission_state='COMPLETED';self.state='IDLE';self.event('mission.completed',{'id':self.mission['id']})
            else:
                error=(math.atan2(dx,dy)-self.driver.heading+math.pi)%(2*math.pi)-math.pi
                self.driver.set_velocity(min(self.mission['speed'],dist)*max(0,math.cos(error)),max(-1.2,min(1.2,error*2)))
        # Predict boundary crossing before applying a step; hard stop beats acceleration ramp.
        margin=abs(self.driver.speed)*dt+self.settings.max_speed*dt
        if (abs(self.driver.target)>0 or abs(self.driver.speed)>0) and math.hypot(self.driver.x,self.driver.y)+margin>=self.settings.fence_radius:
            self.stop('Geofence boundary',True)
        self.driver.step(dt,self.settings.acceleration)
        self.battery=max(0,self.battery-dt*(0.0003+abs(self.driver.speed)*0.001))
        p=[round(self.driver.x,2),round(self.driver.y,2)]
        if not self.trail or self.trail[-1]!=p:self.trail=(self.trail+[p])[-1000:]
    def snapshot(self):
        d=self.driver.get_state();speed=abs(d['speed']);battery=4.0 if self.faults['battery'] else self.battery
        sensors={'gps':{'latitude':30.3165+d['y']/111320,'longitude':78.0322+d['x']/(111320*math.cos(math.radians(30.3165))), 'fix':'NO FIX' if self.faults['gps'] else 'SIM FIX','satellites':0 if self.faults['gps'] else 16,'accuracy_m':0.12},
        'imu':{'roll':math.sin(d['distance'])*speed,'pitch':math.cos(d['distance'])*speed,'yaw':d['heading']},
        'battery':{'percent':battery,'voltage':22+battery/25,'current':1+speed*3,'temperature':29+speed*2},
        'motors':{'rpm':speed*190,'temperature':31+speed*5,'left_encoder':int(d['distance']*1000),'right_encoder':int(d['distance']*1000)},
        'range':{k:0.4 if self.faults['obstacle'] else 12.0 for k in ['front','rear','left','right']},
        'network':{'latency_ms':None if self.faults['network'] else 8,'rssi':-48,'packet_loss':100 if self.faults['network'] else 0},
        'lidar':{'scan_hz':10,'points':360,'online':not self.faults['sensor']}}
        return {'id':'rover-01','name':'MATHTECH / ROVER-01','source':'SIMULATION','timestamp':time.time(),
        'connected':not self.faults['network'],'mode':self.mode,'state':self.state,'latched':self.latched,'reason':self.reason,
        'position':d,'sensors':sensors,'faults':self.faults,'settings':self.settings.model_dump(),
        'mission':{'id':self.mission['id'] if self.mission else None,'name':self.mission['name'] if self.mission else 'No mission',
        'state':self.mission_state,'index':self.index,'count':len(self.mission['waypoints']) if self.mission else 0,
        'waypoints':self.mission['waypoints'] if self.mission else []},'trail':self.trail[-250:]}
