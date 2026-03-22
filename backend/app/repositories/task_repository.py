# backend/app/repositories/task_repository.py

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, asc
from sqlalchemy.orm import selectinload
from typing import List, Optional
from datetime import datetime, timedelta
from app.models.task_models import Task, TaskStatus
from app.schemas.vendor_task_schema import TaskFilterParams

class TaskRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_vendor_tasks(
        self, 
        vendor_id: int, 
        filters: Optional[TaskFilterParams] = None
    ) -> List[Task]:
        """Retrieve all tasks for a vendor with optional filtering"""
        query = select(Task).where(Task.vendor_id == vendor_id)
        
        # Eager load relationships
        query = query.options(
            selectinload(Task.customer),
            selectinload(Task.event),
            selectinload(Task.offering)
        )
        
        if filters:
            if filters.status:
                query = query.where(Task.status == filters.status)
            if filters.priority:
                query = query.where(Task.priority == filters.priority)
            if filters.search:
                search_filter = or_(
                    Task.title.ilike(f"%{filters.search}%"),
                    Task.description.ilike(f"%{filters.search}%")
                )
                query = query.where(search_filter)
            if filters.date_from:
                query = query.where(Task.due_date >= filters.date_from)
            if filters.date_to:
                query = query.where(Task.due_date <= filters.date_to)
        
        # Order by urgency: expiry_date first, then priority, then created
        query = query.order_by(
            asc(Task.expiry_date).nullslast(),
            desc(Task.priority),
            desc(Task.created_at)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_task_by_id(self, task_id: int, vendor_id: int) -> Optional[Task]:
        """Get specific task ensuring it belongs to the vendor"""
        query = select(Task).where(
            and_(Task.id == task_id, Task.vendor_id == vendor_id)
        ).options(
            selectinload(Task.customer),
            selectinload(Task.event),
            selectinload(Task.offering),
            selectinload(Task.messages)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def count_tasks_by_status(self, vendor_id: int) -> dict:
        """Get counts for dashboard badges"""
        from sqlalchemy import func
        
        query = select(
            Task.status,
            func.count(Task.id).label("count")
        ).where(
            Task.vendor_id == vendor_id
        ).group_by(Task.status)
        
        result = await self.db.execute(query)
        counts = {status: 0 for status in TaskStatus}
        for row in result.all():
            counts[row.status] = row.count
        return counts
    
    async def get_urgent_tasks(self, vendor_id: int, hours: int = 24) -> List[Task]:
        """Get tasks due within specified hours or expired"""
        cutoff = datetime.utcnow() + timedelta(hours=hours)
        
        query = select(Task).where(
            and_(
                Task.vendor_id == vendor_id,
                Task.status.in_([TaskStatus.PENDING_RESPONSE, TaskStatus.ASSIGNED]),
                or_(
                    Task.due_date <= cutoff,
                    Task.expiry_date <= datetime.utcnow()
                )
            )
        ).options(
            selectinload(Task.customer),
            selectinload(Task.event)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()