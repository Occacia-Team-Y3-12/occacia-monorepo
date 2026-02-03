from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from app.common.enums import UserRole, UserStatus

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

@dataclass
class User(ABC):
    user_id: str
    email: str
    password_hash: str
    role: UserRole
    status: UserStatus
    last_login_at: Optional[datetime] = None

    # Use default_factory to create a new default value at runtime
    created_at: datetime = field(default_factory=now_utc)
    updated_at: datetime = field(default_factory=now_utc)

    def mark_modified_time(self) -> None:
        self.updated_at = now_utc()

    def mark_login_time(self) -> None:
        self.last_login_at = now_utc()
        self.mark_modified_time()