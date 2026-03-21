"""
Convenience import module.

Importing this module registers all ORM models on `Base.metadata`.
"""

from app.models.admin import Admin
from app.models.customer import Customer
from app.models.event import Event
from app.models.event_chat_message import EventChatMessage
from app.models.event_persona import EventPersona
from app.models.notification import Notification
from app.models.offering import Offering
from app.models.organization import Organization
from app.models.package import Package
from app.models.package_execution_request import PackageExecutionRequest
from app.models.package_item import PackageItem
from app.models.persona import Persona
from app.models.recommendation_package import RecommendationPackage
from app.models.support_note import SupportNote
from app.models.task import Task
from app.models.task_models import VendorTask, VendorTaskMessage
from app.models.task_recommendation import TaskRecommendation
from app.models.task_request import TaskRequest
from app.models.user import User
from app.models.vendor import Vendor
from app.models.chat_session import ChatSession 

__all__ = [
    "Admin",
    "Customer",
    "Event",
    "EventChatMessage",
    "EventPersona",
    "Notification",
    "Offering",
    "Organization",
    "Package",
    "PackageExecutionRequest",
    "PackageItem",
    "Persona",
    "RecommendationPackage",
    "SupportNote",
    "Task",
    "VendorTask",
    "VendorTaskMessage",
    "TaskRecommendation",
    "TaskRequest",
    "User",
    "Vendor",
    "VendorTask",
    "VendorTaskMessage",
]
