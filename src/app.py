from datetime import datetime, timedelta
import csv
import io

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.config import settings
from src.database import Base, SessionLocal, engine
from src.models import Account, LeadCandidate, Project
from src.schemas import AccountCreate, LeadIngest, ProjectCreate
from src.services.keyword_filter import analyze_message
from src.services.keyword_pack_loader import load_keyword_pack
from src.services.outreach_engine import approve_and_mark_sent, process_ready_queue
from src.services.telegram_ingest import ingest_candidate

Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.app_name)
templates = Jinja2Templates(directory="web/templates")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "env": settings.app_env}


@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    projects = db.query(Project).order_by(Project.id.desc()).all()
    return templates.TemplateResponse("index.html", {"request": request, "projects": projects})


@app.post("/projects")
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    exists = db.query(Project).filter(Project.name == payload.name).first()
    if exists:
        raise HTTPException(status_code=400, detail="Project already exists")

    project = Project(
        name=payload.name,
        offer_text=payload.offer_text,
        destination_link=payload.destination_link,
        min_score=payload.min_score,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"id": project.id, "name": project.name}


@app.post("/projects/form")
def create_project_form(
    name: str = Form(...),
    offer_text: str = Form(...),
    destination_link: str = Form(...),
    min_score: float = Form(0.65),
    db: Session = Depends(get_db),
):
    payload = ProjectCreate(
        name=name,
        offer_text=offer_text,
        destination_link=destination_link,
        min_score=min_score,
    )
    create_project(payload, db)
    return RedirectResponse(url="/", status_code=303)


@app.get("/projects/{project_id}", response_class=HTMLResponse)
def project_page(project_id: int, request: Request, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    accounts = db.query(Account).filter(Account.project_id == project.id).all()
    leads = (
        db.query(LeadCandidate)
        .filter(LeadCandidate.project_id == project.id)
        .order_by(LeadCandidate.id.desc())
        .limit(100)
        .all()
    )

    now = datetime.utcnow()
    today_start = datetime(now.year, now.month, now.day)
    range_start = today_start - timedelta(days=13)

    total_leads = db.query(func.count(LeadCandidate.id)).filter(LeadCandidate.project_id == project.id).scalar() or 0
    queued_review_count = (
        db.query(func.count(LeadCandidate.id))
        .filter(LeadCandidate.project_id == project.id)
        .filter(LeadCandidate.status.in_(["queued_review", "ready_to_send"]))
        .scalar()
        or 0
    )
    selected_total_count = (
        db.query(func.count(LeadCandidate.id))
        .filter(LeadCandidate.project_id == project.id)
        .filter(LeadCandidate.status.in_(["queued_review", "ready_to_send"]))
        .scalar()
        or 0
    )
    sent_total_count = (
        db.query(func.count(LeadCandidate.id))
        .filter(LeadCandidate.project_id == project.id)
        .filter(LeadCandidate.status.like("sent:%"))
        .scalar()
        or 0
    )
    sent_today_count = (
        db.query(func.count(LeadCandidate.id))
        .filter(LeadCandidate.project_id == project.id)
        .filter(LeadCandidate.status.like("sent:%"))
        .filter(LeadCandidate.created_at >= today_start)
        .scalar()
        or 0
    )

    daily_selected_rows = (
        db.query(func.date(LeadCandidate.created_at), func.count(LeadCandidate.id))
        .filter(LeadCandidate.project_id == project.id)
        .filter(LeadCandidate.status.in_(["queued_review", "ready_to_send"]))
        .filter(LeadCandidate.created_at >= range_start)
        .group_by(func.date(LeadCandidate.created_at))
        .all()
    )
    daily_sent_rows = (
        db.query(func.date(LeadCandidate.created_at), func.count(LeadCandidate.id))
        .filter(LeadCandidate.project_id == project.id)
        .filter(LeadCandidate.status.like("sent:%"))
        .filter(LeadCandidate.created_at >= range_start)
        .group_by(func.date(LeadCandidate.created_at))
        .all()
    )

    daily_selected_map = {row[0]: row[1] for row in daily_selected_rows}
    daily_sent_map = {row[0]: row[1] for row in daily_sent_rows}
    daily_status_stats = []
    for i in range(14):
        day = range_start + timedelta(days=i)
        key = day.strftime("%Y-%m-%d")
        daily_status_stats.append(
            {
                "day": key,
                "selected": daily_selected_map.get(key, 0),
                "sent": daily_sent_map.get(key, 0),
            }
        )

    selected_leads = (
        db.query(LeadCandidate)
        .filter(LeadCandidate.project_id == project.id)
        .filter(LeadCandidate.status.in_(["queued_review", "ready_to_send"]))
        .order_by(LeadCandidate.id.desc())
        .limit(50)
        .all()
    )

    sent_leads = (
        db.query(LeadCandidate)
        .filter(LeadCandidate.project_id == project.id)
        .filter(LeadCandidate.status.like("sent:%"))
        .order_by(LeadCandidate.id.desc())
        .limit(50)
        .all()
    )

    metrics = {
        "accounts_count": len(accounts),
        "total_leads": total_leads,
        "queued_review_count": queued_review_count,
        "selected_total_count": selected_total_count,
        "sent_total_count": sent_total_count,
        "sent_today_count": sent_today_count,
    }

    return templates.TemplateResponse(
        "project.html",
        {
            "request": request,
            "project": project,
            "accounts": accounts,
            "leads": leads,
            "selected_leads": selected_leads,
            "sent_leads": sent_leads,
            "metrics": metrics,
            "daily_status_stats": daily_status_stats,
        },
    )


def _project_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _build_leads_csv(leads: list[LeadCandidate]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id",
        "created_at",
        "source_chat",
        "source_user",
        "source_message",
        "drafted_message",
        "score",
        "status",
    ])
    for lead in leads:
        writer.writerow(
            [
                lead.id,
                lead.created_at.isoformat() if lead.created_at else "",
                lead.source_chat,
                lead.source_user,
                lead.source_message,
                lead.drafted_message,
                lead.lead_score,
                lead.status,
            ]
        )
    return output.getvalue()


@app.get("/projects/{project_id}/exports/selected.csv")
def export_selected_csv(project_id: int, db: Session = Depends(get_db)):
    _project_or_404(db, project_id)
    leads = (
        db.query(LeadCandidate)
        .filter(LeadCandidate.project_id == project_id)
        .filter(LeadCandidate.status.in_(["queued_review", "ready_to_send"]))
        .order_by(LeadCandidate.id.desc())
        .all()
    )
    content = _build_leads_csv(leads)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=project_{project_id}_selected.csv"},
    )


@app.get("/projects/{project_id}/exports/sent.csv")
def export_sent_csv(project_id: int, db: Session = Depends(get_db)):
    _project_or_404(db, project_id)
    leads = (
        db.query(LeadCandidate)
        .filter(LeadCandidate.project_id == project_id)
        .filter(LeadCandidate.status.like("sent:%"))
        .order_by(LeadCandidate.id.desc())
        .all()
    )
    content = _build_leads_csv(leads)
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=project_{project_id}_sent.csv"},
    )


@app.post("/projects/{project_id}/analyze-message")
def analyze_message_route(
    project_id: int,
    source_message: str = Form(...),
    db: Session = Depends(get_db),
):
    _project_or_404(db, project_id)
    keyword_pack = load_keyword_pack(settings.keyword_pack_file)
    target_keywords = keyword_pack["target_keywords"] or settings.target_keywords
    target_phrases = keyword_pack["target_phrases"] or settings.target_phrases
    stop_phrases = keyword_pack["stop_phrases"] or settings.stop_phrases

    match_result = analyze_message(
        message=source_message,
        keywords_csv=target_keywords,
        phrases_csv=target_phrases,
        stop_phrases_csv=stop_phrases,
    )
    return {
        "is_candidate": match_result.is_candidate,
        "score": match_result.score,
        "matched_keywords": match_result.matched_keywords,
        "matched_phrases": match_result.matched_phrases,
        "matched_stop_phrases": match_result.matched_stop_phrases,
    }


@app.post("/projects/{project_id}/accounts")
def add_account(project_id: int, payload: AccountCreate, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    account = Account(project_id=project.id, **payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return {"id": account.id, "alias": account.alias}


@app.post("/projects/{project_id}/accounts/form")
def add_account_form(
    project_id: int,
    alias: str = Form(...),
    phone_masked: str = Form("hidden"),
    max_per_hour: int = Form(3),
    max_per_day: int = Form(5),
    db: Session = Depends(get_db),
):
    payload = AccountCreate(
        alias=alias,
        phone_masked=phone_masked,
        max_per_hour=max_per_hour,
        max_per_day=max_per_day,
    )
    add_account(project_id, payload, db)
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@app.post("/projects/{project_id}/ingest")
def ingest(project_id: int, payload: LeadIngest, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    lead = ingest_candidate(
        db=db,
        project=project,
        source_chat=payload.source_chat,
        source_user=payload.source_user,
        source_message=payload.source_message,
    )
    return {
        "lead_id": lead.id,
        "status": lead.status,
        "score": lead.lead_score,
        "reason": lead.lead_reason,
    }


@app.post("/projects/{project_id}/ingest/form")
def ingest_form(
    project_id: int,
    source_chat: str = Form(...),
    source_user: str = Form(...),
    source_message: str = Form(...),
    db: Session = Depends(get_db),
):
    payload = LeadIngest(
        source_chat=source_chat,
        source_user=source_user,
        source_message=source_message,
    )
    ingest(project_id, payload, db)
    return RedirectResponse(url=f"/projects/{project_id}", status_code=303)


@app.post("/leads/{lead_id}/approve")
def approve_lead(lead_id: int, db: Session = Depends(get_db)):
    ok, message = approve_and_mark_sent(db, lead_id)
    if not ok:
        raise HTTPException(status_code=400, detail=message)
    return {"ok": ok, "message": message}


@app.post("/leads/{lead_id}/approve/form")
def approve_lead_form(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadCandidate).filter(LeadCandidate.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    ok, _ = approve_and_mark_sent(db, lead_id)
    return RedirectResponse(url=f"/projects/{lead.project_id}", status_code=303 if ok else 302)


@app.post("/leads/{lead_id}/reject")
def reject_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadCandidate).filter(LeadCandidate.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead.status = "rejected_manual"
    db.commit()
    return {"ok": True}


@app.post("/leads/{lead_id}/reject/form")
def reject_lead_form(lead_id: int, db: Session = Depends(get_db)):
    lead = db.query(LeadCandidate).filter(LeadCandidate.id == lead_id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")

    reject_lead(lead_id, db)
    return RedirectResponse(url=f"/projects/{lead.project_id}", status_code=303)


@app.post("/worker/tick")
def worker_tick(db: Session = Depends(get_db)):
    report = process_ready_queue(db=db, batch_size=settings.worker_batch_size)
    return {"ok": True, "report": report}
