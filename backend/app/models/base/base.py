from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

# Use this base entity for every other entity
@dataclass
class BaseEntity:
    # DB-generated primary key (AUTO INCREMENT)
    id: Optional[int] = field(default=None, init=False)

    created_at: datetime = field(default_factory=now_utc, init=False)

