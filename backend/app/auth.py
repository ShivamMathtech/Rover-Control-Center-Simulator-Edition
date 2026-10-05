import hashlib, secrets, time
from fastapi import HTTPException, Request

def password_hash(password,salt=None):
    salt=salt or secrets.token_hex(16)
    digest=hashlib.scrypt(password.encode(),salt=bytes.fromhex(salt),n=16384,r=8,p=1).hex()
    return salt+':'+digest

def verify(password,stored):
    return secrets.compare_digest(password_hash(password,stored.split(':')[0]),stored)

class Auth:
    def __init__(self,store):self.store=store;self.sessions={};self.attempts={}
    def login(self,username,password,ip):
        now=time.monotonic();attempts=[t for t in self.attempts.get(ip,[]) if now-t<60]
        if len(attempts)>=10:raise HTTPException(429,'Too many login attempts; wait one minute')
        self.attempts[ip]=attempts+[now]
        user=self.store.get('user:'+username)
        if not user or not verify(password,user['hash']):raise HTTPException(401,'Invalid credentials')
        self.sessions={k:v for k,v in self.sessions.items() if v['expires']>time.time()}
        token=secrets.token_urlsafe(32)
        self.sessions[token]={'username':username,'role':user['role'],'expires':time.time()+8*3600}
        return token
    def user(self,token):
        user=self.sessions.get(token or '')
        if not user or user['expires']<time.time():raise HTTPException(401,'Login required')
        return user
    def require(self,request:Request,roles=None):
        user=self.user(request.cookies.get('rover_session'))
        if roles and user['role'] not in roles:raise HTTPException(403,'Role not authorized')
        if request.method not in ('GET','HEAD','OPTIONS'):
            if not secrets.compare_digest(request.headers.get('X-CSRF-Token',''),request.cookies.get('rover_csrf','')) or not request.cookies.get('rover_csrf'):
                raise HTTPException(403,'CSRF token missing')
        return user
