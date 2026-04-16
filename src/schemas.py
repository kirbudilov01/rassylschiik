from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    offer_text: str = Field(min_length=10)
    destination_link: str = Field(min_length=5)
    min_score: float = Field(default=0.65, ge=0.0, le=1.0)


class AccountCreate(BaseModel):
    alias: str = Field(min_length=2, max_length=80)
    phone_masked: str = Field(default="hidden", max_length=40)
    max_per_hour: int = Field(default=3, ge=1, le=50)
    max_per_day: int = Field(default=5, ge=1, le=200)


class LeadIngest(BaseModel):
    source_chat: str
    source_user: str
    source_message: str
