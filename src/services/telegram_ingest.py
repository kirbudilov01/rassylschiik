from sqlalchemy.orm import Session

from src.config import settings
from src.models import LeadCandidate, Project
from src.services.keyword_pack_loader import load_keyword_pack
from src.services.message_templates import choose_template
from src.services.prompt_builder import build_system_prompt, build_user_prompt
from src.services.selection_engine import evaluate_candidate


def ingest_candidate(
    db: Session,
    project: Project,
    source_chat: str,
    source_user: str,
    source_message: str,
) -> LeadCandidate:
    keyword_pack = load_keyword_pack(settings.keyword_pack_file)
    target_keywords = keyword_pack["target_keywords"] or settings.target_keywords
    target_phrases = keyword_pack["target_phrases"] or settings.target_phrases
    stop_phrases = keyword_pack["stop_phrases"] or settings.stop_phrases

    selection = evaluate_candidate(
        source_message=source_message,
        target_keywords=target_keywords,
        target_phrases=target_phrases,
        stop_phrases=stop_phrases,
        min_score=project.min_score,
    )

    llm_payload = {
        "source_user": source_user,
        "source_chat": source_chat,
        "source_message": source_message,
        "matched_keywords": selection.matched_keywords,
        "matched_phrases": selection.matched_phrases,
        "system_prompt": build_system_prompt(),
        "user_prompt": build_user_prompt(
            source_chat=source_chat,
            source_user=source_user,
            source_message=source_message,
            matched_keywords=selection.matched_keywords,
            matched_phrases=selection.matched_phrases,
        ),
    }

    if not selection.is_selected:
        lead = LeadCandidate(
            project_id=project.id,
            source_chat=source_chat,
            source_user=source_user,
            source_message=source_message,
            lead_score=selection.score,
            lead_reason=(
                f"Selection reject: {selection.reason}; "
                f"matched_stop={selection.matched_stop_phrases}; payload={llm_payload}"
            ),
            status="rejected_selection",
            drafted_message="",
        )
        db.add(lead)
        db.commit()
        db.refresh(lead)
        return lead

    drafted_message = choose_template(source_user=source_user, source_message=source_message)
    status = "queued_review"

    lead = LeadCandidate(
        project_id=project.id,
        source_chat=source_chat,
        source_user=source_user,
        source_message=source_message,
        lead_score=selection.score,
        lead_reason=(
            f"Selection pass: {selection.reason}; keyword_hits={selection.matched_keywords}; "
            f"phrase_hits={selection.matched_phrases}; payload={llm_payload}"
        ),
        status=status,
        drafted_message=drafted_message,
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead
