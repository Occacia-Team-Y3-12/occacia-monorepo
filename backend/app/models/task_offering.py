from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.common.utils import now_utc
from app.core.database import Base


class TaskOffering(Base):
    __tablename__ = "task_offerings"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("tasks.task_id"), nullable=False, index=True)
    offering_id = Column(String, ForeignKey("offerings.offering_id"), nullable=False, index=True)
    rank = Column(Integer, nullable=False)
    score = Column(Float, nullable=True)
    is_selected = Column(Boolean, nullable=False, default=False)
    selected_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)

    task = relationship("Task", back_populates="task_offerings")
    offering = relationship("Offering", back_populates="task_offerings")
