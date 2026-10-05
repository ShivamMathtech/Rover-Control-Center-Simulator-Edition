import time
import pytest
from app.controller import Controller,Rejected
from app.schemas import Command,Settings

class Clock:
    def __init__(self):self.now=100.
    def __call__(self):return self.now
    def advance(self,dt):self.now+=dt

def setup():
    clock=Clock();c=Controller(clock=clock);c.acquire('operator');return c,clock

def command(n=1,v=1):return Command(linear=v,angular=0,sequence=n,issued_at=time.time())

def test_deadman_stops_after_release():
    c,t=setup();c.command(command());c.tick(.1);assert c.driver.speed>0
    t.advance(.7);c.tick(.1);assert c.driver.speed==0 and c.state=='IDLE'

def test_estop_requires_reset_and_does_not_resume():
    c,t=setup();c.command(command());c.stop('emergency',True)
    with pytest.raises(Rejected):c.command(command(2))
    c.reset();c.tick(.1);assert c.driver.speed==0 and not c.latched

@pytest.mark.parametrize('fault',['obstacle','gps','battery','network','sensor','motor'])
def test_faults_stop_motion(fault):
    c,t=setup();c.command(command());c.tick(.1);c.faults[fault]=True;c.tick(.1)
    assert c.latched and c.driver.speed==0
    with pytest.raises(Rejected):c.reset()
    c.faults[fault]=False;c.tick(.1);assert c.driver.speed==0 and c.latched

def test_stale_and_reordered_commands_rejected():
    c,t=setup();c.command(command(5))
    with pytest.raises(Rejected):c.command(command(4))
    old=command(6);old.issued_at-=3
    with pytest.raises(Rejected):c.command(old)

def test_only_one_operator():
    c,t=setup()
    with pytest.raises(Rejected):c.acquire('other')
    t.advance(3);c.acquire('other');assert c.owner=='other' and c.driver.speed==0

def test_mission_completes_and_dwells():
    c,t=setup();c.change_mode('AUTONOMOUS')
    c.start({'id':'test','name':'test','speed':.8,'waypoints':[{'x':0,'y':2,'wait':1},{'x':1,'y':2,'wait':0}]})
    for _ in range(800):
        t.advance(.05);c.heartbeat('operator');c.tick(.05)
        if c.mission_state=='COMPLETED':break
    assert c.mission_state=='COMPLETED' and c.driver.speed==0

def test_link_loss_aborts_mission():
    c,t=setup();c.change_mode('AUTONOMOUS');c.start({'id':'t','name':'t','speed':1,'waypoints':[{'x':0,'y':10,'wait':0}]})
    t.advance(3);c.tick(.1);assert c.latched and c.mission_state=='ABORTED'

def test_geofence_prediction_stops():
    c,t=setup();c.driver.y=c.settings.fence_radius-.05;c.command(command());c.tick(.1)
    assert c.latched and c.driver.y<c.settings.fence_radius

def test_invalid_waypoint_and_speed():
    c,t=setup()
    with pytest.raises(Rejected):c.validate_mission({'speed':1,'waypoints':[{'x':60,'y':1}]})
    with pytest.raises(Rejected):c.command(command(v=2))

def test_pause_resume_and_mode_change():
    c,t=setup();c.change_mode('AUTONOMOUS');c.start({'id':'t','name':'t','speed':.8,'waypoints':[{'x':0,'y':10,'wait':0}]})
    c.mission_action('pause');c.tick(.1);assert c.driver.speed==0
    c.mission_action('resume');c.tick(.1);assert c.driver.speed>0
    c.change_mode('MANUAL');assert c.driver.speed==0 and c.mission_state=='ABORTED'
