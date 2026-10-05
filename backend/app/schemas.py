from typing import Literal
from pydantic import BaseModel, Field, ConfigDict

class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)

class Login(Strict):
    username: str = Field(min_length=1, max_length=80)
    password: str = Field(min_length=1, max_length=200)

class UserCreate(Login):
    password: str = Field(min_length=12, max_length=200)
    role: Literal['ADMIN','OPERATOR','VIEWER'] = 'VIEWER'

class Command(Strict):
    linear: float = Field(ge=-2, le=2)
    angular: float = Field(ge=-1.5, le=1.5)
    sequence: int = Field(ge=0)
    issued_at: float

class Mode(Strict):
    mode: Literal['MANUAL','ASSISTED','AUTONOMOUS']

class Waypoint(Strict):
    x: float = Field(ge=-1000,le=1000)
    y: float = Field(ge=-1000,le=1000)
    wait: float = Field(default=0,ge=0,le=600)

class Mission(Strict):
    name: str = Field(min_length=1,max_length=80)
    speed: float = Field(default=0.8,gt=0,le=2)
    waypoints: list[Waypoint] = Field(min_length=1,max_length=100)

class Fault(Strict):
    name: Literal['obstacle','gps','camera','battery','network','sensor','motor']
    enabled: bool

class Settings(Strict):
    max_speed: float = Field(default=1.5,ge=0.1,le=2)
    acceleration: float = Field(default=0.7,ge=0.1,le=2)
    command_timeout: float = Field(default=0.6,ge=0.2,le=1)
    link_timeout: float = Field(default=2,ge=1,le=5)
    fence_radius: float = Field(default=60,ge=5,le=200)
    obstacle_stop: float = Field(default=1.2,ge=0.5,le=5)
    low_battery: float = Field(default=15,ge=5,le=30)
