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

    # --- Security hardening additions ---
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime, nullable=True)
    last_login_ip = Column(String, nullable=True)
    last_login_device = Column(String, nullable=True)
    mfa_secret = Column(String, nullable=True)
    mfa_enabled = Column(Boolean, default=False)

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
    # GDPR legal basis for holding this contact data. Public B2B business
    # contact info discovered via the scraping pipeline generally sits on
    # "legitimate interest" (Art. 6(1)(f)) rather than requiring opt-in
    # consent — this field exists so that changes (e.g. individually
    # consented contacts) can be tracked per-record instead of assumed.
    data_basis = Column(String, default="legitimate_interest_b2b")

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
    # "Every lead must always have a next action" — from the original spec,
    # never actually built. callback_date already existed but was unused
    # anywhere in the codebase; next_action pairs a short label with it
    # (Call Again, Send Email, Schedule Meeting, etc.)
    next_action = Column(String, nullable=True)

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


class AuditLog(Base):
    """Privileged/admin action trail — account changes, permission changes,
    login events. Distinct from AgentActivity, which only tracks lead
    contact history. This is what SOC 2-style audits actually ask for:
    who did what to the *system*, not just to a lead."""
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True)
    actor_id = Column(String, nullable=True)       # null = system/unauthenticated event
    actor_name = Column(String, nullable=True)
    actor_role = Column(String, nullable=True)
    action = Column(String, nullable=False)         # e.g. USER_CREATED, LOGIN_FAILED, MFA_ENABLED
    target_type = Column(String, nullable=True)     # e.g. "user", "lead"
    target_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)
    ip = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


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


class SchemaMigration(Base):
    """Tracks which named migrations have already run, so each one executes
    exactly once instead of being re-attempted (and silently failing) on
    every single backend restart."""
    __tablename__ = "schema_migrations"

    name = Column(String, primary_key=True)
    applied_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    logger.info("Initializing database...")
    # Step 1: Standard SQLAlchemy tables setup — creates any brand-new
    # tables (including schema_migrations itself) but never alters existing
    # ones, hence the registry below for anything added after go-live.
    Base.metadata.create_all(bind=engine)

    with engine.begin() as conn:
        try:
            already_applied = {row[0] for row in conn.execute(text("SELECT name FROM schema_migrations")).fetchall()}
        except Exception:
            already_applied = set()

    for name, migration_fn in MIGRATIONS:
        if name in already_applied:
            continue
        try:
            with engine.begin() as conn:
                migration_fn(conn)
                conn.execute(
                    text("INSERT INTO schema_migrations (name, applied_at) VALUES (:name, :ts)"),
                    {"name": name, "ts": datetime.utcnow()},
                )
            logger.info("Migration applied: %s", name)
        except Exception as e:
            # Each migration gets its own transaction — one failure (e.g. a
            # slow cross-region connection timing out) can't poison every
            # migration after it the way a single shared transaction did.
            logger.warning("Migration failed, will retry next startup: %s - %s", name, str(e))

    logger.info("Database initialization and migration check completed successfully.")


def _column_exists(conn, table: str, column: str) -> bool:
    if engine.dialect.name == "sqlite":
        cols = {row[1] for row in conn.execute(text(f"PRAGMA table_info({table})")).fetchall()}
    else:
        cols = {
            row[0] for row in conn.execute(
                text("SELECT column_name FROM information_schema.columns WHERE table_name = :t"),
                {"t": table},
            ).fetchall()
        }
    return column in cols


def _add_column_if_missing(conn, table: str, column: str, sqlite_type: str, postgres_type: str):
    if _column_exists(conn, table, column):
        return
    coltype = sqlite_type if engine.dialect.name == "sqlite" else postgres_type
    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}"))


def _migration_service_opportunities(conn):
    _add_column_if_missing(conn, "leads", "service_opportunities", "TEXT", "TEXT")


def _migration_agent_activity_user_id(conn):
    _add_column_if_missing(conn, "agent_activity", "user_id", "TEXT", "TEXT")


def _migration_business_data_basis(conn):
    _add_column_if_missing(conn, "businesses", "data_basis",
                            "TEXT DEFAULT 'legitimate_interest_b2b'",
                            "TEXT DEFAULT 'legitimate_interest_b2b'")


def _migration_user_security_columns(conn):
    _add_column_if_missing(conn, "users", "failed_login_attempts", "INTEGER DEFAULT 0", "INTEGER DEFAULT 0")
    _add_column_if_missing(conn, "users", "locked_until", "DATETIME", "TIMESTAMP")
    _add_column_if_missing(conn, "users", "last_login_ip", "TEXT", "TEXT")
    _add_column_if_missing(conn, "users", "last_login_device", "TEXT", "TEXT")
    _add_column_if_missing(conn, "users", "mfa_secret", "TEXT", "TEXT")
    _add_column_if_missing(conn, "users", "mfa_enabled", "BOOLEAN DEFAULT 0", "BOOLEAN DEFAULT FALSE")


def _migration_performance_indexes(conn):
    # CREATE INDEX IF NOT EXISTS is valid on both SQLite and Postgres, so
    # this one needs no dialect branching. Adds indexes on columns that
    # were being filtered on with no index at all (crm_status,
    # assigned_field_agent, agent_activity lookups by lead/user).
    for stmt in [
        "CREATE INDEX IF NOT EXISTS ix_leads_status ON leads (status);",
        "CREATE INDEX IF NOT EXISTS ix_leads_crm_status ON leads (crm_status);",
        "CREATE INDEX IF NOT EXISTS ix_leads_assigned_field_agent ON leads (assigned_field_agent);",
        "CREATE INDEX IF NOT EXISTS ix_leads_in_crm ON leads (in_crm);",
        "CREATE INDEX IF NOT EXISTS ix_businesses_category ON businesses (category);",
        "CREATE INDEX IF NOT EXISTS ix_businesses_city ON businesses (city);",
        "CREATE INDEX IF NOT EXISTS ix_audit_log_timestamp ON audit_log (timestamp);",
        "CREATE INDEX IF NOT EXISTS ix_audit_log_actor ON audit_log (actor_id);",
        "CREATE INDEX IF NOT EXISTS ix_agent_activity_lead_id ON agent_activity (lead_id);",
        "CREATE INDEX IF NOT EXISTS ix_agent_activity_user_id ON agent_activity (user_id);",
    ]:
        conn.execute(text(stmt))


def _migration_next_action(conn):
    _add_column_if_missing(conn, "leads", "next_action", "TEXT", "TEXT")
    conn.execute(text("CREATE INDEX IF NOT EXISTS ix_leads_callback_date ON leads (callback_date);"))


# Ordered, named, idempotent. Add new entries to the END of this list —
# never reorder or rename existing ones, since names are how the tracking
# table knows what's already run.
MIGRATIONS = [
    ("2024_add_service_opportunities", _migration_service_opportunities),
    ("2024_add_agent_activity_user_id", _migration_agent_activity_user_id),
    ("2026_add_business_data_basis", _migration_business_data_basis),
    ("2026_add_user_security_columns", _migration_user_security_columns),
    ("2026_add_performance_indexes", _migration_performance_indexes),
    ("2026_add_next_action", _migration_next_action),
]
