from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.common.enums import UserRole, UserStatus
from app.models.base.updatable import UpdatableEntity


def now_utc() -> datetime:
    return datetime.now(timezone.utc)

@dataclass
class User(UpdatableEntity, ABC):
    user_id: str
    email: str
    password_hash: str
    role: UserRole
    status: UserStatus
    last_login_at: Optional[datetime] = None

    def mark_login_time(self) -> None:
        self.last_login_at = now_utc()
        self.mark_modified_time()