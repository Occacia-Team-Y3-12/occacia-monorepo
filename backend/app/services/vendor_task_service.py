from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.repositories.task_repository import TaskRepository
from app.models.task_models import Task, TaskStatus
from app.schemas.vendor_task_schema import (
    TaskListResponse, 
    TaskListItem, 
    TaskDetail,
    TaskFilterParams
)

class VendorTaskService:
    def __init__(self, task_repository: TaskRepository):
        self.repo = task_repository
    
    def _format_budget_range(self, task: Task) -> Optional[str]:
        """Format budget for display"""
        if task.budget_min and task.budget_max:
            return f"${task.budget_min:,.0f} - ${task.budget_max:,.0f}"
        elif task.budget_min:
            return f"From ${task.budget_min:,.0f}"
        elif task.budget_max:
            return f"Up to ${task.budget_max:,.0f}"
        return None
    
    def _is_urgent(self, task: Task) -> bool:
        """Determine if task needs urgent attention"""
        if task.priority == TaskStatus.PENDING_RESPONSE:
            return True
        if task.due_date and (task.due_date - datetime.utcnow()).days <= 1:
            return True
        if task.expiry_date and task.expiry_date <= datetime.utcnow():
            return True
        return False
    
    def _format_time_remaining(self, task: Task) -> Optional[str]:
        """Human readable time remaining"""
        if not task.due_date:
            return None
        
        delta = task.due_date - datetime.utcnow()
        if delta.days < 0:
            return "Overdue"
        elif delta.days == 0:
            hours = delta.seconds // 3600
            return f"{hours} hours left"
        elif delta.days == 1:
            return "1 day left"
        else:
            return f"{delta.days} days left"
    
    def _to_list_item(self, task: Task) -> TaskListItem:
        """Convert Task model to list view schema"""
        return TaskListItem(
            id=task.id,
            title=task.title,
            status=task.status.value,
            priority=task.priority.value,
            due_date=task.due_date,
            expiry_date=task.expiry_date,
            budget_range=self._format_budget_range(task),
            customer={
                "id": task.customer.id,
                "name": task.customer.name,
                "email": task.customer.email
            },
            event={
                "id": task.event.id,
                "title": task.event.title,
                "occasion_type": task.event.occasion_type,
                "event_date": task.event.event_date
            } if task.event else None,
            created_at=task.created_at,
            is_urgent=self._is_urgent(task)
        )
    
    def _to_detail(self, task: Task) -> TaskDetail:
        """Convert Task model to detail view schema"""
        can_respond = (
            task.status == TaskStatus.PENDING_RESPONSE and 
            (not task.expiry_date or task.expiry_date > datetime.utcnow())
        )
        
        return TaskDetail(
            id=task.id,
            title=task.title,
            description=task.description,
            status=task.status.value,
            priority=task.priority.value,
            budget_min=task.budget_min,
            budget_max=task.budget_max,
            agreed_price=task.agreed_price,
            due_date=task.due_date,
            expiry_date=task.expiry_date,
            completed_at=task.completed_at,
            created_at=task.created_at,
            responded_at=task.responded_at,
            customer={
                "id": task.customer.id,
                "name": task.customer.name,
                "email": task.customer.email
            },
            event={
                "id": task.event.id,
                "title": task.event.title,
                "occasion_type": task.event.occasion_type,
                "event_date": task.event.event_date
            } if task.event else None,
            offering={
                "id": task.offering.id,
                "name": task.offering.name,
                "category": task.offering.category
            } if task.offering else None,
            time_remaining=self._format_time_remaining(task),
            can_respond=can_respond
        )
    
    async def get_grouped_tasks(
        self, 
        vendor_id: int, 
        filters: Optional[TaskFilterParams] = None
    ) -> TaskListResponse:
        """Get tasks grouped by status for vendor dashboard"""
        tasks = await self.repo.get_vendor_tasks(vendor_id, filters)
        
        # Group by status
        pending = []
        assigned = []
        completed = []
        rejected_expired = []
        
        for task in tasks:
            item = self._to_list_item(task)
            if task.status == TaskStatus.PENDING_RESPONSE:
                pending.append(item)
            elif task.status == TaskStatus.ASSIGNED:
                assigned.append(item)
            elif task.status == TaskStatus.COMPLETED:
                completed.append(item)
            else:
                rejected_expired.append(item)
        
        return TaskListResponse(
            pending_response=pending,
            assigned=assigned,
            completed=completed,
            rejected_expired=rejected_expired,
            total_count=len(tasks)
        )
    
    async def get_task_detail(self, task_id: int, vendor_id: int) -> TaskDetail:
        """Get detailed view of specific task"""
        task = await self.repo.get_task_by_id(task_id, vendor_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found or access denied"
            )
        return self._to_detail(task)
    
    async def get_dashboard_stats(self, vendor_id: int) -> dict:
        """Get quick stats for vendor dashboard"""
        counts = await self.repo.count_tasks_by_status(vendor_id)
        urgent = await self.repo.get_urgent_tasks(vendor_id)
        
        return {
            "counts": counts,
            "urgent_count": len(urgent),
            "requires_action": counts.get(TaskStatus.PENDING_RESPONSE, 0),
            "in_progress": counts.get(TaskStatus.ASSIGNED, 0)
        }