import os
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = os.environ.get("DATABASE_URL", "")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Business(Base):
    __tablename__ = "businesses"
    id = Column(String, primary_key=True)
    name = Column(String)
    category = Column(String)
    city = Column(String)
    region = Column(String)
    address = Column(String)
    lat = Column(Float)
    lng = Column(Float)
    source = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class Enrichment(Base):
    __tablename__ = "enrichment"
    id = Column(String, primary_key=True)
    business_id = Column(String)
    website = Column(String)
    facebook = Column(String)
    instagram = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

class Lead(Base):
    __tablename__ = "leads"
    id = Column(String, primary_key=True)
    business_id = Column(String)
    score = Column(Integer)
    opportunity_level = Column(String)
    status = Column(String, default="NEW")
    assigned_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class CRMPipeline(Base):
    __tablename__ = "crm_pipeline"
    id = Column(String, primary_key=True)
    lead_id = Column(String)
    status = Column(String, default="NEW")
    appointment_date = Column(DateTime)
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

class AgentActivity(Base):
    __tablename__ = "agent_activity"
    id = Column(String, primary_key=True)
    agent_id = Column(String)
    lead_id = Column(String)
    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

def init_db():
    Base.metadata.create_all(bind=engine)
