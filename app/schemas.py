from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MemberCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    postal_code: str = Field(min_length=2, max_length=20)
    consent: bool


class MemberRead(MemberCreate):
    id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ParticipationCreate(BaseModel):
    member_ref: UUID
    program: str = Field(min_length=2, max_length=120)
    hours: float = Field(gt=0, le=24)


class ParticipationRead(ParticipationCreate):
    id: UUID
    recorded_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProgramMetric(BaseModel):
    program: str
    total_hours: float


class FederatedMember(BaseModel):
    member: MemberRead
    participations: list[ParticipationRead]
    total_hours: float


class FederatedOverview(BaseModel):
    member_count: int
    participant_count: int
    total_hours: float
    programs: list[ProgramMetric]


class DeploymentInfo(BaseModel):
    mode: Literal["local", "hybrid"]
    private_database: Literal["local"]
    cloud_database: Literal["local", "remote"]
    cloud_tls: bool
