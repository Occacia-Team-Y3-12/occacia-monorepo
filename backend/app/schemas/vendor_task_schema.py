from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

class TaskStatusEnum(str, Enum):
    PENDING_RESPONSE = "pending_response"
    ASSIGNED = "assigned"
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TaskPriorityEnum(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class CustomerBrief(BaseModel):
    id: int
    name: str
    email: str
    
    class Config:
        from_attributes = True

class EventBrief(BaseModel):
    id: int
    title: str
    occasion_type: str
    event_date: Optional[datetime]
    
    class Config:
        from_attributes = True

class OfferingBrief(BaseModel):
    id: int
    name: str
    category: str
    
    class Config:
        from_attributes = True

class TaskListItem(BaseModel):
    """Schema for list view - lightweight"""
    id: int
    title: str
    status: TaskStatusEnum
    priority: TaskPriorityEnum
    due_date: Optional[datetime]
    expiry_date: Optional[datetime]
    budget_range: Optional[str] = Field(None, description="Formatted budget range")
    customer: CustomerBrief
    event: Optional[EventBrief]
    created_at: datetime
    is_urgent: bool = Field(False, description="True if due within 24h or high priority")
    
    class Config:
        from_attributes = True

class TaskDetail(BaseModel):
    """Schema for detailed view"""
    id: int
    title: str
    description: Optional[str]
    status: TaskStatusEnum
    priority: TaskPriorityEnum
    budget_min: Optional[Decimal]
    budget_max: Optional[Decimal]
    agreed_price: Optional[Decimal]
    due_date: Optional[datetime]
    expiry_date: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    responded_at: Optional[datetime]
    
    customer: CustomerBrief
    event: Optional[EventBrief]
    offering: Optional[OfferingBrief]
    
    # Computed fields
    time_remaining: Optional[str] = Field(None, description="Human readable time to due date")
    can_respond: bool = Field(True, description="Whether vendor can still accept/reject")
    
    class Config:
        from_attributes = True

class TaskListResponse(BaseModel):
    """Grouped response by status"""
    pending_response: List[TaskListItem]
    assigned: List[TaskListItem]
    completed: List[TaskListItem]
    rejected_expired: List[TaskListItem]
    total_count: int
    
    class Config:
        from_attributes = True

class TaskFilterParams(BaseModel):
    status: Optional[TaskStatusEnum] = None
    priority: Optional[TaskPriorityEnum] = None
    search: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None