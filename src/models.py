from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    offer_text: Mapped[str] = mapped_column(Text, nullable=False)
    destination_link: Mapped[str] = mapped_column(String(255), nullable=False)
    min_score: Mapped[float] = mapped_column(Float, default=0.65)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    accounts: Mapped[list["Account"]] = relationship("Account", back_populates="project")
    leads: Mapped[list["LeadCandidate"]] = relationship("LeadCandidate", back_populates="project")


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(80), nullable=False)
    phone_masked: Mapped[str] = mapped_column(String(40), default="hidden")
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    max_per_hour: Mapped[int] = mapped_column(Integer, default=3)
    max_per_day: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project] = relationship("Project", back_populates="accounts")


class LeadCandidate(Base):
    __tablename__ = "lead_candidates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    source_chat: Mapped[str] = mapped_column(String(120), nullable=False)
    source_user: Mapped[str] = mapped_column(String(120), nullable=False)
    source_message: Mapped[str] = mapped_column(Text, nullable=False)
    lead_score: Mapped[float] = mapped_column(Float, default=0.0)
    lead_reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(40), default="new")
    drafted_message: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped[Project] = relationship("Project", back_populates="leads")
