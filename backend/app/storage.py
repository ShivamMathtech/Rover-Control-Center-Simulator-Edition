"""Small SQLAlchemy store: SQLite locally, PostgreSQL through DATABASE_URL."""
import json, os, time
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, select, delete
from sqlalchemy.orm import DeclarativeBase, Session

class Base(DeclarativeBase): pass
class Document(Base):
    __tablename__='documents'
    key=Column(String(160),primary_key=True)
    data=Column(Text,nullable=False)
class Event(Base):
    __tablename__='events'
    id=Column(Integer,primary_key=True)
    timestamp=Column(Float,nullable=False,index=True)
    data=Column(Text,nullable=False)
class Sample(Base):
    __tablename__='telemetry'
    id=Column(Integer,primary_key=True)
    timestamp=Column(Float,nullable=False,index=True)
    data=Column(Text,nullable=False)

class Store:
    def __init__(self,url=None):
        url=url or os.getenv('DATABASE_URL','sqlite:///./rover.db')
        self.engine=create_engine(url,connect_args={'check_same_thread':False} if url.startswith('sqlite') else {})
        Base.metadata.create_all(self.engine)
    def get(self,key,default=None):
        with Session(self.engine) as s:
            row=s.get(Document,key)
            return json.loads(row.data) if row else default
    def set(self,key,value):
        with Session(self.engine) as s:
            s.merge(Document(key=key,data=json.dumps(value)));s.commit()
    def remove(self,key):
        with Session(self.engine) as s:
            row=s.get(Document,key)
            if row:s.delete(row);s.commit()
    def list(self,prefix):
        with Session(self.engine) as s:
            return [json.loads(r.data) for r in s.scalars(select(Document).where(Document.key.startswith(prefix))).all()]
    def append(self,table,data):
        cls=Event if table=='events' else Sample
        with Session(self.engine) as s:
            s.add(cls(timestamp=time.time(),data=json.dumps(data)));s.commit()
    def history(self,table,seconds=3600,limit=3600):
        cls=Event if table=='events' else Sample
        with Session(self.engine) as s:
            rows=s.scalars(select(cls).where(cls.timestamp>=time.time()-seconds).order_by(cls.id.desc()).limit(limit)).all()
            return [{'timestamp':r.timestamp,**json.loads(r.data)} for r in reversed(rows)]
    def prune(self):
        with Session(self.engine) as s:
            s.execute(delete(Sample).where(Sample.timestamp < time.time()-int(os.getenv('TELEMETRY_RETENTION_DAYS','7'))*86400))
            s.execute(delete(Event).where(Event.timestamp < time.time()-int(os.getenv('EVENT_RETENTION_DAYS','90'))*86400));s.commit()
