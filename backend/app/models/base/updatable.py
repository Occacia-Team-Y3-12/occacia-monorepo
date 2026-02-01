from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.common.utils.time_utils import now_utc
from app.models.base.base import BaseEntity

# Use this class if you need updated_at along with the base entity
@dataclass
class UpdatableEntity(BaseEntity):
    updated_at: datetime = field(default_factory=now_utc, init=False)

    def mark_modified_time(self) -> None:
        self.updated_at = now_utc()