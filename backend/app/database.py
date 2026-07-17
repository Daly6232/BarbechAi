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
    text,  # Added to execute raw SQL for safe startup migrations
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
    category = Column(String, index=True)
    city = Column(String, index=True)
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
    status = Column(String, default="NEW", index=True)

    # Storage column for lead opportunity tags
    service_opportunities = Column(Text, nullable=True)

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
    # Step 1: Standard SQLAlchemy tables setup
    Base.metadata.create_all(bind=engine)

    # Step 2: Automated inline schema checks.
    # IMPORTANT: "ADD COLUMN IF NOT EXISTS" is Postgres-only syntax. SQLite (the
    # local/dev default from DATABASE_URL) throws a syntax error on it every
    # single time, which used to be swallowed by the except below — meaning the
    # column never actually got added locally, and every lead insert that wrote
    # service_opportunities would then crash with "no such column".
    is_sqlite = engine.dialect.name == "sqlite"

    if is_sqlite:
        with engine.begin() as conn:
            existing_cols = {
                row[1] for row in conn.execute(text("PRAGMA table_info(leads)")).fetchall()
            }
            if "service_opportunities" not in existing_cols:
                try:
                    conn.execute(text("ALTER TABLE leads ADD COLUMN service_opportunities TEXT"))
                    logger.info("Startup Migration Success (sqlite): added service_opportunities")
                except Exception as e:
                    logger.warning("Startup Migration Failed (sqlite): %s", str(e))

            agent_activity_cols = {
                row[1] for row in conn.execute(text("PRAGMA table_info(agent_activity)")).fetchall()
            }
            if agent_activity_cols and "user_id" not in agent_activity_cols:
                try:
                    conn.execute(text("ALTER TABLE agent_activity ADD COLUMN user_id TEXT"))
                    logger.info("Startup Migration Success (sqlite): added agent_activity.user_id")
                except Exception as e:
                    logger.warning("Startup Migration Failed (sqlite): %s", str(e))

            # SQLite creates indexes via CREATE INDEX IF NOT EXISTS fine, no dialect issue there.
            migrations = [
                "CREATE INDEX IF NOT EXISTS ix_leads_status ON leads (status);",
                "CREATE INDEX IF NOT EXISTS ix_businesses_category ON businesses (category);",
                "CREATE INDEX IF NOT EXISTS ix_businesses_city ON businesses (city);",
            ]
    else:
        migrations = [
            "ALTER TABLE leads ADD COLUMN IF NOT EXISTS service_opportunities TEXT;",
            "ALTER TABLE agent_activity ADD COLUMN IF NOT EXISTS user_id TEXT;",
            "CREATE INDEX IF NOT EXISTS ix_leads_status ON leads (status);",
            "CREATE INDEX IF NOT EXISTS ix_businesses_category ON businesses (category);",
            "CREATE INDEX IF NOT EXISTS ix_businesses_city ON businesses (city);",
        ]

    # Each statement gets its OWN connection/transaction. Previously these all
    # shared one transaction — the first timeout (e.g. a slow cross-region link
    # to the DB) left Postgres in "aborted transaction" state, so every single
    # statement after it failed too, even harmless ones like CREATE INDEX.
    for cmd in migrations:
        try:
            with engine.begin() as conn:
                conn.execute(text(cmd))
            logger.info("Startup Migration Success: %s", cmd)
        except Exception as e:
            logger.warning("Startup Migration Skipped/Failed: %s - Error: %s", cmd, str(e))

    logger.info("Database initialization and migration check completed successfully.")
