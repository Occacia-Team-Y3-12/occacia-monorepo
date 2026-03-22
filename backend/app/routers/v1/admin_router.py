"""
app/routers/v1/admin_router.py
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.admin import Admin
from app.models.package_execution_request import PackageExecutionRequest
from app.models.support_note import SupportNote
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor
from app.schemas.admin_schema import (
    AdminRegister, AdminResponse, NotificationResponse, PaginatedNotificationsResponse,
    VendorAdminView, VendorRejectRequest, CustomerAdminView, PaginatedCustomers,
    CustomerStatusUpdateRequest, AdminTaskSupportActionRequest, InternalNoteCreateRequest,
    InternalNoteResponse, PaginatedFulfillmentRequestsResponse, PaginatedInternalNotesResponse,
    PaginatedPackageOrdersResponse, PaginatedTasksResponse, AdminDashboardResponse,
)
from app.schemas.event_planning_schema import TaskResponse
from app.schemas.package_schema import (
    FulfillmentRequestResponse,
    PackageOrderDetailsResponse,
    PackageOrderResponse,
)
from app.services.admin_service import admin_service
from app.services.admin_dashboard_service import admin_dashboard_aggregator
from app.services.notification_service import notification_service
from app.services.auth_service import _send_email

logger = logging.getLogger(__name__)

router            = APIRouter(prefix="/admin",      tags=["Admin"])
auth_admin_router = APIRouter(prefix="/auth/admin", tags=["Authentication"])


# ── Email helpers (vendor approval / rejection) ───────────────────────────────

def _send_approval_email(vendor: Vendor):
    subject = "Your Occacia vendor account has been approved!"
    body = (
        f"Congratulations, {vendor.display_name or vendor.business_name}!\n\n"
        f"Your vendor application for {vendor.business_name} has been approved.\n\n"
        f"You can now log in and start adding your packages.\n\n"
        f"Vendor ID: {vendor.vendor_id}\n"
    )
    _send_email(vendor.email, subject, body)


def _send_rejection_email(vendor: Vendor, reason: str):
    subject = "Update on your Occacia vendor application"
    body = (
        f"Hi {vendor.display_name or vendor.business_name},\n\n"
        f"Unfortunately, your vendor application was not approved at this time.\n\n"
        f"Reason: {reason}\n\n"
        f"If you have questions, please contact our support team."
    )
    _send_email(vendor.email, subject, body)


# ── Response builders ─────────────────────────────────────────────────────────

def _task_response(task: Task) -> TaskResponse:
    return TaskResponse(
        taskId=task.task_id,
        eventId=task.event_id,
        name=task.name,
        description=task.description,
        quantity=task.quantity,
        needsVendor=bool(task.needs_vendor),
        vendorCategory=task.needs_vendor,
        budgetMin=task.budget_min,
        budgetMax=task.budget_max,
        currency=task.currency,
        status=task.status,
        selectedOfferingId=task.selected_offering_id,
        assignedVendorId=task.assigned_vendor_id,
        confirmedAt=task.confirmed_at,
        lockedAt=task.locked_at,
        dueAt=task.due_at,
        expiresAt=task.expires_at,
        rejectedAt=task.rejected_at,
        rejectionReason=task.rejection_reason,
        statusUpdatedAt=task.status_updated_at,
        createdAt=task.created_at,
        updatedAt=task.updated_at,
    )


def _package_order_response(order: PackageExecutionRequest) -> PackageOrderResponse:
    return PackageOrderResponse(
        packageOrderId=order.execution_request_id,
        eventId=order.event_id,
        packageId=order.package_id,
        packageOrderTotalPrice=order.package_total_price,
        currency=order.currency,
        status=order.status,
        createdAt=order.created_at,
        statusUpdatedAt=order.status_updated_at,
        notes=order.notes,
        idempotencyKey=order.idempotency_key,
    )


def _fulfillment_request_response(request: TaskRequest) -> FulfillmentRequestResponse:
    return FulfillmentRequestResponse(
        fulfillmentRequestId=request.request_id,
        packageOrderId=request.package_order_id,
        taskId=request.task_id,
        vendorId=request.vendor_id,
        offeringId=request.offering_id,
        status=request.status,
        requestedAt=request.requested_at,
        respondBy=request.respond_by,
        respondedAt=request.responded_at,
        responseNote=request.response_note,
        attemptNo=request.attempt_no,
    )


def _internal_note_response(note: SupportNote) -> InternalNoteResponse:
    return InternalNoteResponse(
        noteId=note.note_id,
        adminId=note.admin_id,
        packageOrderId=note.package_order_id,
        eventId=note.event_id,
        taskId=note.task_id,
        vendorId=note.vendor_id,
        actionType=note.action_type,
        note=note.note,
        createdAt=note.created_at,
    )


# ── Auth routes — registration only (login moved to auth_router.py) ───────────

@auth_admin_router.post("/register", response_model=AdminResponse, status_code=201)
def register_admin(payload: AdminRegister, db: Session = Depends(get_db)):
    """
    Provision a new admin account (internal use only).
    Disabled in production via DISABLE_ADMIN_REGISTER env var.
    """
    if getattr(settings, "DISABLE_ADMIN_REGISTER", "false").lower() == "true":
        raise HTTPException(status_code=403, detail="Admin registration is disabled.")
    return admin_service.register_admin(
        db,
        email=payload.email,
        password=payload.password,
        staff_role=payload.staff_role,
    )


# ── Vendor management ─────────────────────────────────────────────────────────

@router.get("/vendors", response_model=list[VendorAdminView])
def list_vendors(
    approval_status: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    return admin_service.list_vendors(db, approval_status=approval_status, status=status)


@router.get("/vendors/{vendor_id}", response_model=VendorAdminView)
def get_vendor_detail(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    return admin_service.get_vendor(db, vendor_id=vendor_id)


@router.post("/vendors/{vendor_id}/approve", response_model=VendorAdminView)
def approve_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    vendor = admin_service.approve_vendor(db, vendor_id=vendor_id, admin_email=current_admin.email)
    _send_approval_email(vendor)
    return vendor


@router.post("/vendors/{vendor_id}/reject", response_model=VendorAdminView)
def reject_vendor(
    vendor_id: int,
    body: VendorRejectRequest = VendorRejectRequest(),
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    vendor = admin_service.reject_vendor(
        db, vendor_id=vendor_id, reason=body.reason, admin_email=current_admin.email,
    )
    _send_rejection_email(vendor, body.reason)
    return vendor


# ── Notifications ─────────────────────────────────────────────────────────────

@router.get("/notifications", response_model=PaginatedNotificationsResponse)
def list_notifications(
    limit: int = 50,
    cursor: str | None = None,
    user_id: str | None = None,
    event_id: str | None = None,
    task_id: str | None = None,
    status: str | None = None,
    type: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    items, next_cursor = notification_service.list_notifications(
        db,
        limit=limit,
        cursor=cursor,
        user_id=user_id,
        event_id=event_id,
        task_id=task_id,
        status=status,
        type=type,
    )
    return PaginatedNotificationsResponse(
        items=[NotificationResponse.model_validate(item) for item in items],
        next_cursor=next_cursor,
    )


# ── Customer management ───────────────────────────────────────────────────────

@router.get("/customers", response_model=PaginatedCustomers)
def list_customers(
    status: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    customers, next_cursor = admin_service.list_customers(
        db, status=status, limit=limit, cursor=cursor,
    )
    return PaginatedCustomers(
        items=[CustomerAdminView.model_validate(c) for c in customers],
        nextCursor=next_cursor,
    )


@router.get("/customers/{customer_id}", response_model=CustomerAdminView)
def get_customer_detail(
    customer_id: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    return admin_service.get_customer(db, customer_id=customer_id)


@router.put("/customers/{customer_id}/status", response_model=CustomerAdminView)
def update_customer_status(
    customer_id: str,
    body: CustomerStatusUpdateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    return admin_service.update_customer_status(
        db,
        customer_id=customer_id,
        new_status=body.status,
        admin_email=current_admin.email,
    )


# ── Internal notes ────────────────────────────────────────────────────────────

@router.get("/internal-notes", response_model=PaginatedInternalNotesResponse)
def list_internal_notes(
    eventId: str | None = None,
    taskId: str | None = None,
    vendorId: str | None = None,
    packageOrderId: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    items, next_cursor = admin_service.list_internal_notes(
        db,
        event_id=eventId,
        task_id=taskId,
        vendor_id=vendorId,
        package_order_id=packageOrderId,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedInternalNotesResponse(
        items=[_internal_note_response(item) for item in items],
        nextCursor=next_cursor,
    )


@router.post("/internal-notes", response_model=InternalNoteResponse, status_code=201)
def create_internal_note(
    body: InternalNoteCreateRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    note = admin_service.create_internal_note(
        db,
        admin_id=current_admin.admin_id,
        package_order_id=body.package_order_id,
        event_id=body.event_id,
        task_id=body.task_id,
        vendor_id=body.vendor_id,
        action_type=body.action_type,
        note=body.note,
    )
    return _internal_note_response(note)


# ── Package orders ────────────────────────────────────────────────────────────

@router.get("/package-orders", response_model=PaginatedPackageOrdersResponse)
def list_package_orders(
    status: str | None = None,
    eventId: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    items, next_cursor = admin_service.list_package_orders(
        db, status_filter=status, event_id=eventId, limit=limit, cursor=cursor,
    )
    return PaginatedPackageOrdersResponse(
        items=[_package_order_response(item) for item in items],
        nextCursor=next_cursor,
    )


@router.get("/package-orders/{packageOrderId}", response_model=PackageOrderDetailsResponse)
def get_package_order_detail(
    packageOrderId: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    order, tasks = admin_service.get_package_order_detail(db, package_order_id=packageOrderId)
    return PackageOrderDetailsResponse(
        packageOrder=_package_order_response(order),
        tasks=[_task_response(task) for task in tasks],
    )


# ── Tasks ─────────────────────────────────────────────────────────────────────

@router.get("/tasks", response_model=PaginatedTasksResponse)
def list_tasks(
    status: str | None = None,
    eventId: str | None = None,
    vendorId: str | None = None,
    limit: int = 20,
    cursor: str | None = None,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    items, next_cursor = admin_service.list_tasks(
        db,
        status_filter=status,
        event_id=eventId,
        vendor_id=vendorId,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedTasksResponse(
        items=[_task_response(item) for item in items],
        nextCursor=next_cursor,
    )


@router.get("/tasks/{taskId}", response_model=TaskResponse)
def get_task_detail(
    taskId: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    return _task_response(admin_service.get_task(db, task_id=taskId))


@router.patch("/tasks/{taskId}", response_model=TaskResponse)
def apply_task_support_action(
    taskId: str,
    body: AdminTaskSupportActionRequest,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    task = admin_service.apply_task_support_action(
        db,
        admin_id=current_admin.admin_id,
        task_id=taskId,
        action=body.action,
        assigned_vendor_id=body.assigned_vendor_id,
        expires_at=body.expires_at,
        status_value=body.status,
        note=body.note,
    )
    return _task_response(task)


@router.get("/tasks/{taskId}/fulfillment-requests", response_model=PaginatedFulfillmentRequestsResponse)
def get_task_fulfillment_requests(
    taskId: str,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    items = admin_service.get_task_fulfillment_requests(db, task_id=taskId)
    return PaginatedFulfillmentRequestsResponse(
        items=[_fulfillment_request_response(item) for item in items],
        nextCursor=None,
    )


# ── Dashboard ─────────────────────────────────────────────────────────────────

@router.get("/dashboard", response_model=AdminDashboardResponse)
def get_admin_dashboard(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
):
    _ = current_admin
    return admin_dashboard_aggregator.get_dashboard_metrics(db)