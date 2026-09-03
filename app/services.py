from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Member, Participation
from app.schemas import FederatedMember, FederatedOverview, ProgramMetric


def federated_member(
    member_id: UUID, private_db: Session, cloud_db: Session
) -> FederatedMember | None:
    member = private_db.get(Member, member_id)
    if member is None:
        return None
    activities = list(
        cloud_db.scalars(
            select(Participation)
            .where(Participation.member_ref == member_id)
            .order_by(Participation.recorded_at)
        )
    )
    return FederatedMember(
        member=member,
        participations=activities,
        total_hours=sum(activity.hours for activity in activities),
    )


def federated_overview(private_db: Session, cloud_db: Session) -> FederatedOverview:
    member_count = private_db.scalar(select(func.count()).select_from(Member)) or 0
    rows = cloud_db.execute(
        select(Participation.program, func.sum(Participation.hours))
        .group_by(Participation.program)
        .order_by(Participation.program)
    ).all()
    participant_count = cloud_db.scalar(
        select(func.count(func.distinct(Participation.member_ref)))
    ) or 0
    programs = [ProgramMetric(program=name, total_hours=float(hours)) for name, hours in rows]
    return FederatedOverview(
        member_count=member_count,
        participant_count=participant_count,
        total_hours=sum(item.total_hours for item in programs),
        programs=programs,
    )
