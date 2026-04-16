from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from src.models import LeadCandidate


def is_account_within_limits(
    db: Session,
    account_alias: str,
    max_per_hour: int,
    max_per_day: int,
) -> tuple[bool, str]:
    # В MVP считаем отправленными lead_candidates со статусом sent:<alias>
    now = datetime.utcnow()
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)

    hour_count = (
        db.query(func.count(LeadCandidate.id))
        .filter(LeadCandidate.status == f"sent:{account_alias}")
        .filter(LeadCandidate.created_at >= hour_ago)
        .scalar()
        or 0
    )
    day_count = (
        db.query(func.count(LeadCandidate.id))
        .filter(LeadCandidate.status == f"sent:{account_alias}")
        .filter(LeadCandidate.created_at >= day_ago)
        .scalar()
        or 0
    )

    if hour_count >= max_per_hour:
        return False, "Превышен лимит отправок в час"
    if day_count >= max_per_day:
        return False, "Превышен лимит отправок в день"
    return True, "OK"
