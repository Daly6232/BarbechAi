from datetime import datetime, timedelta
from collections import OrderedDict

from app.core.logging import get_logger
from app.database import SessionLocal, Lead, User, AgentActivity

logger = get_logger(__name__)


def _month_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m")


def conversion_and_revenue_trends(months: int = 6):
    """Monthly conversion rate (won / total created that month) and revenue
    (sum of deal_value for leads closed that month), for the last N months.
    Uses created_at for the conversion denominator and contract_sent_at as
    the closing-date proxy for revenue, since there's no dedicated
    'won_at' column — contract_sent_at is the same signal get_agent_stats
    already uses to mean 'deal closed'."""
    db = SessionLocal()
    try:
        cutoff = datetime.utcnow() - timedelta(days=31 * months)
        leads = db.query(Lead).filter(Lead.created_at >= cutoff).all()

        buckets = OrderedDict()
        today = datetime.utcnow()
        for i in range(months - 1, -1, -1):
            marker = today - timedelta(days=30 * i)
            buckets[_month_key(marker)] = {"month": _month_key(marker), "total": 0, "won": 0, "revenue": 0}

        for lead in leads:
            if not lead.created_at:
                continue
            key = _month_key(lead.created_at)
            if key in buckets:
                buckets[key]["total"] += 1
                if lead.crm_status == "WON":
                    buckets[key]["won"] += 1

        # Revenue bucketed by close date, not creation date — a lead created
        # in March but closed in May should count as May's revenue.
        closed_leads = db.query(Lead).filter(Lead.contract_sent_at.isnot(None)).filter(Lead.contract_sent_at >= cutoff).all()
        for lead in closed_leads:
            key = _month_key(lead.contract_sent_at)
            if key in buckets:
                buckets[key]["revenue"] += lead.deal_value or 0

        series = list(buckets.values())
        for b in series:
            b["conversion_rate"] = round(b["won"] / b["total"] * 100, 1) if b["total"] else 0

        return {"months": series}
    except Exception as exc:
        logger.exception(exc)
        return {"months": [], "error": str(exc)}
    finally:
        db.close()


def agent_leaderboard():
    """Same metrics as get_agent_stats, computed for every active field
    agent in one pass instead of one query-per-agent (which is what
    TeamPage currently does client-side via N sequential fetches)."""
    db = SessionLocal()
    try:
        agents = db.query(User).filter(User.role == "field_agent").filter(User.is_active == True).all()  # noqa: E712
        results = []
        for agent in agents:
            leads = db.query(Lead).filter(Lead.assigned_field_agent == agent.id).all()
            deals_closed = sum(1 for l in leads if l.contract_sent_at is not None)
            total_deal_value = sum(l.deal_value or 0 for l in leads)
            activity_count = db.query(AgentActivity).filter(AgentActivity.agent_id == agent.id).count()
            results.append({
                "agent_id": agent.id,
                "name": agent.name,
                "total_assigned": len(leads),
                "deals_closed": deals_closed,
                "total_deal_value": total_deal_value,
                "total_actions": activity_count,
            })
        results.sort(key=lambda r: r["deals_closed"], reverse=True)
        return {"agents": results}
    except Exception as exc:
        logger.exception(exc)
        return {"agents": [], "error": str(exc)}
    finally:
        db.close()
