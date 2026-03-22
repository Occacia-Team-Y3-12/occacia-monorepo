# backend/app/routers/vendor_tasks.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List
from datetime import datetime

from app.core.dependencies import get_current_vendor, get_db
from app.core.security import require_vendor_approved
from app.services.vendor_task_service import VendorTaskService
from app.repositories.task_repository import TaskRepository
from app.schemas.vendor_task_schema import (
    TaskListResponse, 
    TaskDetail, 
    TaskFilterParams,
    TaskStatusEnum,
    TaskPriorityEnum
)
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(
    prefix="/vendors",
    tags=["Vendor Tasks"],
    dependencies=[Depends(get_current_vendor), Depends(require_vendor_approved)]
)

# Dependency injection for service
async def get_task_service(db: AsyncSession = Depends(get_db)) -> VendorTaskService:
    repo = TaskRepository(db)
    return VendorTaskService(repo)

@router.get(
    "/tasks",
    response_model=TaskListResponse,
    operation_id="vendors_list_tasks_async_router",
    summary="Get vendor's assigned activities",
    description="Retrieve all tasks assigned to the vendor, grouped by status"
)
async def list_vendor_tasks(
    status: Optional[TaskStatusEnum] = Query(None, description="Filter by status"),
    priority: Optional[TaskPriorityEnum] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    date_from: Optional[datetime] = Query(None, description="Filter by due date from"),
    date_to: Optional[datetime] = Query(None, description="Filter by due date to"),
    current_vendor = Depends(get_current_vendor),
    service: VendorTaskService = Depends(get_task_service)
):
    """
    Get all assigned activities for the authenticated vendor.
    
    Returns tasks grouped by:
    - pending_response: Needs accept/reject decision
    - assigned: Currently in progress
    - completed: Finished tasks
    - rejected_expired: Rejected or expired requests
    """
    filters = TaskFilterParams(
        status=status,
        priority=priority,
        search=search,
        date_from=date_from,
        date_to=date_to
    )
    
    return await service.get_grouped_tasks(current_vendor.id, filters)

@router.get(
    "/tasks/{task_id}",
    response_model=TaskDetail,
    summary="Get task details",
    description="Get detailed information about a specific task"
)
async def get_task_detail(
    task_id: int,
    current_vendor = Depends(get_current_vendor),
    service: VendorTaskService = Depends(get_task_service)
):
    """
    Retrieve detailed information about a specific assigned activity.
    Includes customer details, event context, and timing information.
    """
    return await service.get_task_detail(task_id, current_vendor.id)

@router.get(
    "/tasks/stats/dashboard",
    summary="Get dashboard statistics",
    description="Quick stats for vendor dashboard badges"
)
async def get_dashboard_stats(
    current_vendor = Depends(get_current_vendor),
    service: VendorTaskService = Depends(get_task_service)
):
    """Get counts and urgent items for dashboard overview"""
    return await service.get_dashboard_stats(current_vendor.id)
