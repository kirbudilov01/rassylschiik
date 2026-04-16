from sqlalchemy.orm import Session

from src.models import Account, LeadCandidate
from src.services.limiter import is_account_within_limits


def pick_account(db: Session, project_id: int) -> Account | None:
    return (
        db.query(Account)
        .filter(Account.project_id == project_id)
        .filter(Account.is_active == 1)
        .order_by(Account.id.asc())
        .first()
    )


def approve_and_mark_sent(db: Session, lead_id: int) -> tuple[bool, str]:
    lead = db.query(LeadCandidate).filter(LeadCandidate.id == lead_id).first()
    if not lead:
        return False, "Lead not found"

    if lead.status not in {"queued_review", "ready_to_send"}:
        return False, f"Lead status {lead.status} is not sendable"

    lead.status = "ready_to_send"
    db.commit()
    return True, "Marked as ready_to_send"


def process_ready_queue(db: Session, batch_size: int = 20) -> dict:
    ready = (
        db.query(LeadCandidate)
        .filter(LeadCandidate.status == "ready_to_send")
        .order_by(LeadCandidate.id.asc())
        .limit(batch_size)
        .all()
    )

    sent_count = 0
    blocked_count = 0
    skipped_count = 0

    for lead in ready:
        account = pick_account(db, lead.project_id)
        if not account:
            lead.status = "blocked_no_account"
            blocked_count += 1
            continue

        allowed, reason = is_account_within_limits(
            db=db,
            account_alias=account.alias,
            max_per_hour=account.max_per_hour,
            max_per_day=account.max_per_day,
        )
        if not allowed:
            lead.status = "blocked_by_limit"
            lead.lead_reason = f"{lead.lead_reason}; limiter_reason={reason}"
            blocked_count += 1
            continue

        # Telegram sender integration point: replace status-only transition with real send call.
        lead.status = f"sent:{account.alias}"
        sent_count += 1

    db.commit()
    skipped_count = max(0, len(ready) - sent_count - blocked_count)
    return {
        "ready_scanned": len(ready),
        "sent_count": sent_count,
        "blocked_count": blocked_count,
        "skipped_count": skipped_count,
    }


def try_send_single_ready_lead(db: Session, lead_id: int) -> tuple[bool, str]:
    lead = db.query(LeadCandidate).filter(LeadCandidate.id == lead_id).first()
    if not lead:
        return False, "Lead not found"

    if lead.status != "ready_to_send":
        return False, f"Lead status {lead.status} is not ready_to_send"

    account = pick_account(db, lead.project_id)
    if not account:
        return False, "No active account"

    allowed, reason = is_account_within_limits(
        db=db,
        account_alias=account.alias,
        max_per_hour=account.max_per_hour,
        max_per_day=account.max_per_day,
    )
    if not allowed:
        lead.status = "blocked_by_limit"
        db.commit()
        return False, reason

    lead.status = f"sent:{account.alias}"
    db.commit()
    return True, f"Sent by {account.alias}"
