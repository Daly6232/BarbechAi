from datetime import datetime, timedelta

from app.core.logging import get_logger
from app.core.security import generate_uuid
from app.core.config import settings
from app.database import SessionLocal, AuditLog

logger = get_logger(__name__)


def log_audit_event(action: str, actor: dict = None, target_type: str = None,
                     target_id: str = None, details: str = "", ip: str = None):
    """Record a privileged/system action. Uses its own DB session so a
    logging failure or the caller's later rollback never affects the audit
    record — accountability logs shouldn't disappear just because the
    action they're describing failed partway through."""
    db = SessionLocal()
    try:
        entry = AuditLog(
            id=generate_uuid(),
            actor_id=actor.get("id") if actor else None,
            actor_name=actor.get("name") if actor else None,
            actor_role=actor.get("role") if actor else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            details=details or "",
            ip=ip,
            timestamp=datetime.utcnow(),
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        db.rollback()
        logger.exception(e)
    finally:
        db.close()


def get_audit_log(limit: int = 100, offset: int = 0):
    db = SessionLocal()
    try:
        rows = (
            db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        return {
            "count": len(rows),
            "entries": [
                {
                    "id": r.id,
                    "actor_name": r.actor_name or "Système",
                    "actor_role": r.actor_role,
                    "action": r.action,
                    "target_type": r.target_type,
                    "target_id": r.target_id,
                    "details": r.details,
                    "ip": r.ip,
                    "timestamp": r.timestamp.isoformat() if r.timestamp else None,
                }
                for r in rows
            ],
        }
    finally:
        db.close()


def prune_old_audit_logs():
    """Best-effort retention cleanup, run at backend startup."""
    cutoff = datetime.utcnow() - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
    db = SessionLocal()
    try:
        deleted = db.query(AuditLog).filter(AuditLog.timestamp < cutoff).delete()
        db.commit()
        if deleted:
            logger.info("Audit log retention: pruned %s entries older than %s days", deleted, settings.AUDIT_LOG_RETENTION_DAYS)
    except Exception as e:
        db.rollback()
        logger.exception(e)
    finally:
        db.close()
