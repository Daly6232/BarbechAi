from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

DATABASE_URL = settings.DATABASE_URL

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

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

    enrichments = relationship(
        "Enrichment",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    leads = relationship(
        "Lead",
        back_populates="business",
        cascade="all, delete-orphan",
    )


class Enrichment(Base):
    __tablename__ = "enrichment"

    id = Column(String, primary_key=True)

    business_id = Column(
        String,
        ForeignKey("businesses.id"),
        nullable=False,
    )

    website = Column(String)
    facebook = Column(String)
    instagram = Column(String)
    phone = Column(String)
    email = Column(String)
    address = Column(String)
    opening_hours = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow)

    business = relationship(
        "Business",
        back_populates="enrichments",
    )


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String, primary_key=True)
    business_id = Column(
        String,
        ForeignKey("businesses.id"),
        nullable=False,
    )

    score = Column(Integer)
    opportunity_level = Column(String)
    status = Column(String, default="NEW")
    assigned_agent = Column(String)
    assigned_agent_name = Column(String)
    in_crm = Column(String, default="false")
    crm_status = Column(String, default="NEW")
    crm_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship(
        "Business",
        back_populates="leads",
    )

    pipeline = relationship(
        "CRMPipeline",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan",
    )

    activities = relationship(
        "AgentActivity",
        back_populates="lead",
        cascade="all, delete-orphan",
    )

    pipeline = relationship(
        "CRMPipeline",
        back_populates="lead",
        uselist=False,
        cascade="all, delete-orphan",
    )

    activities = relationship(
        "AgentActivity",
        back_populates="lead",
        cascade="all, delete-orphan",
    )


class CRMPipeline(Base):
    __tablename__ = "crm_pipeline"

    id = Column(String, primary_key=True)

    lead_id = Column(
        String,
        ForeignKey("leads.id"),
        nullable=False,
    )

    status = Column(String, default="NEW")
    appointment_date = Column(DateTime)
    notes = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)

    lead = relationship(
        "Lead",
        back_populates="pipeline",
    )


class AgentActivity(Base):
    __tablename__ = "agent_activity"

    id = Column(String, primary_key=True)

    agent_id = Column(String)

    lead_id = Column(
        String,
        ForeignKey("leads.id"),
        nullable=False,
    )

    action = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    notes = Column(Text)

    lead = relationship(
        "Lead",
        back_populates="activities",
    )


def init_db():
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")
