from dataclasses import dataclass

from app.common.enums import UserRole
from app.models.user import User

@dataclass
class Customer(User):
    user_id: str
    email: str
    role: UserRole