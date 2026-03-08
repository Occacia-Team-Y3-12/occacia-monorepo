from __future__ import annotations

from sqlalchemy import Column, DateTime, Float, Integer, String

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class TaskRecommendation(Base):
    __tablename__ = "task_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    recommendation_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("REC"))

    event_id = Column(String, index=True, nullable=False)
    task_id = Column(String, index=True, nullable=False)
    offering_id = Column(String, index=True, nullable=False)
    score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    generated_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

