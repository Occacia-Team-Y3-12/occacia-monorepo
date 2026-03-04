from __future__ import annotations

from sqlalchemy import Column, Integer, String

from app.common.utils import generate_prefixed_id
from app.core.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(String, unique=True, index=True, default=lambda: generate_prefixed_id("ADM"))
    staff_role = Column(String, nullable=True)

