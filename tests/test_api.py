import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD','test-password-12345')
    monkeypatch.setenv('MODE','simulation')
    with TestClient(create_app('sqlite:///'+str(tmp_path/'test.db'))) as c:yield c

def login(c,username='admin',password='test-password-12345'):
    r=c.post('/api/auth/login',json={'username':username,'password':password});assert r.status_code==200
    c.headers['X-CSRF-Token']=c.cookies['rover_csrf']

def test_auth_rbac_csrf(client):
    c=client;assert c.get('/api/rovers').status_code==401;login(c)
    c.headers.pop('X-CSRF-Token');assert c.post('/api/control/acquire').status_code==403
    c.headers['X-CSRF-Token']=c.cookies['rover_csrf']
    assert c.post('/api/users',json={'username':'viewer','password':'viewer-password-123','role':'VIEWER'}).status_code==201
    c.post('/api/auth/logout');login(c,'viewer','viewer-password-123')
    assert c.get('/api/rovers').status_code==200
    assert c.post('/api/control/acquire').status_code==403
    assert c.post('/api/rovers/rover-01/emergency-stop').status_code==403

def test_mission_crud_and_control(client):
    c=client;login(c);assert c.post('/api/control/acquire').status_code==200
    assert c.post('/api/rovers/rover-01/mode',json={'mode':'AUTONOMOUS'}).status_code==200
    body={'name':'Test route','speed':.8,'waypoints':[{'x':0,'y':5,'wait':0}]}
    r=c.post('/api/missions',json=body);assert r.status_code==201;id=r.json()['id']
    assert c.post(f'/api/missions/{id}/start').status_code==200
    assert c.put(f'/api/missions/{id}',json=body).status_code==409
    assert c.post(f'/api/missions/{id}/pause').status_code==200
    assert c.post(f'/api/missions/{id}/resume').status_code==200
    assert c.post('/api/rovers/rover-01/emergency-stop').json()['latched']
    assert c.post('/api/rovers/rover-01/reset').json()['position']['speed']==0
    assert c.delete(f'/api/missions/{id}').status_code==200

def test_validation(client):
    c=client;login(c)
    assert c.post('/api/missions',json={'name':'bad','speed':.8,'waypoints':[{'x':100,'y':0}]}).status_code==409
    assert c.post('/api/missions',json={'name':'bad','speed':.8,'waypoints':[]}).status_code==422
    assert c.post('/api/rovers/rover-01/command',json={'linear':50,'angular':0,'sequence':0,'issued_at':0}).status_code==422

def test_websocket_auth_and_reconnect(client):
    c=client;login(c)
    for _ in range(2):
        with c.websocket_connect('/ws') as ws:
            event=ws.receive_json();assert event['type']=='rover.telemetry';assert event['data']['source']=='SIMULATION'
    assert c.post('/api/control/heartbeat').status_code==409

def test_exports_and_audit(client):
    c=client;login(c)
    assert c.get('/api/telemetry/export?format=csv').text.startswith('timestamp,')
    assert c.get('/api/telemetry/export?format=unknown').status_code==422
    assert any(x['action']=='auth.login' for x in c.get('/api/logs').json())

def test_persistence_after_restart(tmp_path,monkeypatch):
    monkeypatch.setenv('ADMIN_PASSWORD','test-password-12345');url='sqlite:///'+str(tmp_path/'persist.db')
    with TestClient(create_app(url)) as c:
        login(c);r=c.post('/api/missions',json={'name':'Persisted','speed':.8,'waypoints':[{'x':1,'y':1}]});assert r.status_code==201
    with TestClient(create_app(url)) as c:
        login(c);assert any(m['name']=='Persisted' for m in c.get('/api/missions').json())

def test_hardware_mode_fails_closed(tmp_path,monkeypatch):
    monkeypatch.setenv('MODE','hardware')
    with pytest.raises(RuntimeError,match='Hardware mode'):
        with TestClient(create_app('sqlite:///'+str(tmp_path/'hw.db'))):pass
