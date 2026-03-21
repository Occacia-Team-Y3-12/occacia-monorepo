from __future__ import annotations

from sqlalchemy import Column, DateTime, Integer, String

from app.common.utils import generate_prefixed_id, now_utc
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("USR"))

    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), default=now_utc, nullable=False)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), default=now_utc, onupdate=now_utc, nullable=False)

