# backend/app/models/task_models.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Text, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.core.database import Base

class TaskStatus(str, enum.Enum):
    PENDING_RESPONSE = "pending_response"      # Needs accept/reject
    ASSIGNED = "assigned"                      # In Progress
    COMPLETED = "completed"
    REJECTED = "rejected"
    EXPIRED = "expired"

class TaskPriority(str, enum.Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class VendorTask(Base):
    __tablename__ = "vendor_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    offering_id = Column(Integer, ForeignKey("offerings.id"), nullable=True)
    
    # Task details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.PENDING_RESPONSE, index=True)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    
    # Financial
    budget_min = Column(Numeric(10, 2), nullable=True)
    budget_max = Column(Numeric(10, 2), nullable=True)
    agreed_price = Column(Numeric(10, 2), nullable=True)
    
    # Timing
    due_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True)  # When vendor must respond by
    completed_at = Column(DateTime, nullable=True)
    
    # Metadata
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    responded_at = Column(DateTime, nullable=True)  # When vendor accepted/rejected
    
    # Relationships
    vendor = relationship("Vendor", back_populates="vendor_tasks")
    customer = relationship("Customer", back_populates="vendor_tasks")
    event = relationship("Event", back_populates="tasks")
    offering = relationship("Offering", back_populates="tasks")
    messages = relationship("VendorTaskMessage", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<VendorTask(id={self.id}, title={self.title}, status={self.status})>"

# Backward compatibility alias
Task = VendorTask

class VendorTaskMessage(Base):
    __tablename__ = "vendor_task_messages"
    
    id = Column(Integer, primary_key=True)
    task_id = Column(Integer, ForeignKey("vendor_tasks.id"), nullable=False)
    sender_type = Column(String(20), nullable=False)  # 'vendor', 'customer', 'system'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    task = relationship("VendorTask", back_populates="messages")

# Backward compatibility alias
TaskMessage = VendorTaskMessage