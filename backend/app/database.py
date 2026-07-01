from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
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


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False, default="back_office")
    # roles: master_admin, admin, back_office, field_agent
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

    activities = relationship(
        "AgentActivity",
        back_populates="user",
        cascade="all, delete-orphan",
    )


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
    # status: NEW, CONFIRMED, APPOINTMENT_SET, CALLBACK_SET (back office)
    # PENDING_MEETING, MEETING_COMPLETED, PROPOSAL_SENT, NEGOTIATION,
    # CONTRACT_SENT, CLOSED_WON, CLOSED_LOST, FOLLOW_UP (field agent)

    in_crm = Column(String, default="false")
    crm_status = Column(String, default="NEW")
    crm_notes = Column(Text)

    # Back Office fields
    confirmed_by = Column(String)
    confirmed_at = Column(DateTime)
    callback_date = Column(DateTime)
    client_requests = Column(Text)

    # Assignment
    assigned_back_office = Column(String)
    assigned_field_agent = Column(String)
    assigned_agent_name = Column(String)

    # Appointment
    appointment_date = Column(DateTime)
    appointment_location = Column(String)

    # Field Agent / Deal fields
    meeting_completed_at = Column(DateTime)
    proposal_sent_at = Column(DateTime)
    contract_sent_at = Column(DateTime)
    deal_value = Column(Float)
    decline_reason = Column(Text)

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
    user_id = Column(String, ForeignKey("users.id"))

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

    user = relationship(
        "User",
        back_populates="activities",
    )


def init_db():
    logger.info("Initializing database...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database initialized.")
