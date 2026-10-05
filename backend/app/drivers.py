"""Hardware boundary. Only the simulated driver is enabled in this release."""
from typing import Protocol
import math

class RoverDriver(Protocol):
    def set_velocity(self, linear: float, angular: float) -> None: ...
    def stop(self) -> None: ...
    def step(self, dt: float, acceleration: float) -> None: ...
    def get_state(self) -> dict: ...

class SimulatorDriver:
    def __init__(self):
        self.x=self.y=self.heading=self.speed=self.angular=0.0
        self.target=self.turn=self.distance=0.0
    def set_velocity(self,linear,angular):self.target=linear;self.turn=angular
    def stop(self):self.target=self.speed=self.angular=self.turn=0.0
    def step(self,dt,acceleration):
        self.speed+=max(-acceleration*dt,min(acceleration*dt,self.target-self.speed))
        self.angular=self.turn
        self.heading=(self.heading+self.angular*dt)%(2*math.pi)
        self.x+=math.sin(self.heading)*self.speed*dt
        self.y+=math.cos(self.heading)*self.speed*dt
        self.distance+=abs(self.speed)*dt
    def get_state(self):
        return {'x':self.x,'y':self.y,'heading':math.degrees(self.heading),'speed':self.speed,'angular':self.angular,'distance':self.distance}

class PerceptionEngine(Protocol):
    def detect(self, frame) -> list[dict]: ...

class SimulationPerception:
    def detect(self,frame=None):
        return [{'label':'synthetic obstacle','confidence':1.0,'track_id':'SIM-1','source':'simulation','box':[0.4,0.4,0.2,0.3]}]
