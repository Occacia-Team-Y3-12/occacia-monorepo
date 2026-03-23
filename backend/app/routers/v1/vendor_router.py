"""
app/routers/v1/vendor_router.py

Vendor self-service endpoints (requires vendor JWT).
"""
from __future__ import annotations

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_admin, get_current_vendor
from app.models.admin import Admin
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.models.vendor import Vendor
from app.schemas.admin_schema import VendorAdminView
from app.schemas.event_planning_schema import TaskResponse
from app.schemas.package_schema import FulfillmentRequestResponse
from app.schemas.package_schema import PackageCreate, PackageUpdate, PackageResponse
from app.schemas.offering_schema import (
    OfferingCreate,
    OfferingListResponse,
    OfferingResponse,
    OfferingUpdate,
)
from app.schemas.inquiry_schema import (
    InquiryCreate,
    InquiryResponse,
    PaginatedInquiriesResponse,
)
from app.schemas.vendor_schema import (
    PaginatedFulfillmentRequestsResponse,
    PaginatedVendorTasksResponse,
    RespondFulfillmentRequestRequest,
    RespondFulfillmentRequestResponse,
    VendorResponse,
    VendorTaskUpdateRequest,
    VendorUpdate,
)
from app.services.vendor_service import AdminVendorService, vendor_service
from app.services.offering_service import offering_service
from app.services.inquiry_service import inquiry_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vendors", tags=["Vendors"])
admin_router = APIRouter(prefix="/admin", tags=["Admin"])

# --- Local Guardrail ---


def require_approved_vendor(vendor: Vendor = Depends(get_current_vendor)) -> Vendor:
    """Blocks any action if vendor is not approved by admin."""
    if vendor.approval_status != "APPROVED":
        status_msg = {
            "PENDING": "Your account is pending admin approval. You will be notified by email once approved.",
            "REJECTED": "Your vendor application was not approved. Please contact support.",
        }.get(vendor.approval_status, "Your account is not active.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=status_msg)
    return vendor


def get_vendor_service(db: Session = Depends(get_db)):
    return AdminVendorService(db)


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


@admin_router.get(
    "/vendors",
    response_model=list[VendorAdminView],
    operation_id="admin_list_vendors_vendor_router",
)
async def list_vendors(
    approval_status: str | None = Query(default=None),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    vendor_service: AdminVendorService = Depends(get_vendor_service)
):
    """List all vendors."""
    return vendor_service.list_vendors(
        approval_status=approval_status,
        status=status,
    )


@admin_router.get("/vendors/{vendor_id}", response_model=VendorAdminView)
async def get_vendor(
    vendor_id: int,
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    vendor_service: AdminVendorService = Depends(get_vendor_service)
):
    """Get vendor detail."""
    return vendor_service.get_vendor(vendor_id=vendor_id)


@admin_router.put("/vendors/{vendor_id}/status", response_model=VendorAdminView)
async def update_vendor_status(
    vendor_id: int,
    body: dict,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    vendor_service: AdminVendorService = Depends(get_vendor_service)
):
    """Update vendor account status."""
    status_val = body.get("status") or ""
    return vendor_service.update_vendor_status(
        vendor_id=vendor_id,
        new_status=status_val,
        admin_email=current_admin.email,
    )


@admin_router.get("/vendors/stats/pending")
async def get_vendor_pending_stats(
    db: Session = Depends(get_db),
    _: Admin = Depends(get_current_admin),
    vendor_service: AdminVendorService = Depends(get_vendor_service)
):
    """
    Get counts of pending vendors and organizations.
    """
    return vendor_service.get_pending_counts()


# --- Profile Routes ---

@router.get("/me", response_model=VendorResponse)
def get_vendor_me(
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """
    Get current vendor's profile and performance metrics.
    """
    if not current_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    task_summary = vendor_service.get_vendor_task_summary(
        db, vendor_id=current_vendor.id)

    vendor_data = current_vendor.__dict__
    vendor_data['task_summary'] = task_summary

    return VendorResponse.model_validate(vendor_data)


@router.put("/me", response_model=VendorResponse)
def update_vendor_me(
    vendor_data: VendorUpdate,
    current_vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """
    Update current vendor's profile.
    """
    if not current_vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")

    updated_vendor = vendor_service.update_vendor(
        db, vendor_id=current_vendor.id, vendor_data=vendor_data
    )
    return updated_vendor


@router.get("/fulfillment-requests", response_model=PaginatedFulfillmentRequestsResponse)
def list_fulfillment_requests(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    items, next_cursor = vendor_service.list_fulfillment_requests(
        db,
        vendor_id=vendor.vendor_id,
        status_filter=status,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedFulfillmentRequestsResponse(
        items=[_fulfillment_request_response(item) for item in items],
        nextCursor=next_cursor,
    )


@router.get("/fulfillment-requests/{fulfillment_request_id}", response_model=FulfillmentRequestResponse)
def get_fulfillment_request_detail(
    fulfillment_request_id: str,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    request = vendor_service.get_fulfillment_request_detail(
        db,
        vendor_id=vendor.vendor_id,
        fulfillment_request_id=fulfillment_request_id,
    )
    return _fulfillment_request_response(request)


@router.post(
    "/fulfillment-requests/{fulfillment_request_id}/response",
    response_model=RespondFulfillmentRequestResponse,
)
def respond_to_fulfillment_request(
    fulfillment_request_id: str,
    body: RespondFulfillmentRequestRequest,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    request, task = vendor_service.respond_to_fulfillment_request(
        db,
        vendor_id=vendor.vendor_id,
        fulfillment_request_id=fulfillment_request_id,
        decision=body.decision,
        response_note=body.response_note,
    )
    return RespondFulfillmentRequestResponse(
        fulfillmentRequest=_fulfillment_request_response(request),
        task=_task_response(task),
    )


@router.get(
    "/tasks",
    response_model=PaginatedVendorTasksResponse,
    operation_id="vendors_list_tasks_v1_vendor_router",
)
def list_vendor_tasks(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    items, next_cursor = vendor_service.list_vendor_tasks(
        db,
        vendor_id=vendor.vendor_id,
        status_filter=status,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedVendorTasksResponse(
        items=[_task_response(item) for item in items],
        nextCursor=next_cursor,
    )


@router.get("/tasks/{task_id}", response_model=TaskResponse)
def get_vendor_task(
    task_id: str,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    task = vendor_service.get_vendor_task(
        db,
        vendor_id=vendor.vendor_id,
        task_id=task_id,
    )
    return _task_response(task)


@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_vendor_task(
    task_id: str,
    body: VendorTaskUpdateRequest,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    task = vendor_service.update_vendor_task_status(
        db,
        vendor_id=vendor.vendor_id,
        task_id=task_id,
        next_status=body.status,
    )
    return _task_response(task)


# --- Packages Routes ---

@router.get("/me/packages", response_model=List[PackageResponse])
def list_my_packages(
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    """Any logged-in vendor can view their own packages."""
    return vendor_service.get_packages_by_vendor(db, vendor.id)


@router.post("/me/packages", response_model=PackageResponse, status_code=status.HTTP_201_CREATED)
def create_package(
    payload: PackageCreate,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    """Only APPROVED vendors can create packages."""
    # Service expects the Pydantic object based on original code, so we pass 'payload'
    return vendor_service.create_package(db, vendor.id, payload)


@router.put("/me/packages/{package_id}", response_model=PackageResponse)
def update_package(
    package_id: int,
    payload: PackageUpdate,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    """Only APPROVED vendors can update their own packages."""
    # SECURE: vendor.id is now strictly enforced in the service layer
    pkg = vendor_service.update_package(db, package_id, payload, vendor.id)
    if not pkg:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Package not found or unauthorized.")
    return pkg


@router.delete("/me/packages/{package_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_package(
    package_id: int,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    """Only APPROVED vendors can delete their own packages."""
    # SECURE: vendor.id is now strictly enforced in the service layer
    success = vendor_service.delete_package(db, package_id, vendor.id)
    if not success:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Package not found or unauthorized.")
    return None


@router.get("/offerings", response_model=OfferingListResponse, response_model_by_alias=True)
def list_my_offerings(
    include_inactive: bool = Query(default=False, alias="includeInactive"),
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    items = offering_service.list_vendor_offerings(
        db,
        vendor_id=vendor.vendor_id,
        include_inactive=include_inactive,
    )
    return OfferingListResponse(items=[OfferingResponse.model_validate(item) for item in items])


@router.post("/offerings", response_model=OfferingResponse, response_model_by_alias=True, status_code=201)
def create_offering(
    payload: OfferingCreate,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    offering = offering_service.create_offering(
        db,
        vendor_id=vendor.vendor_id,
        data=payload.model_dump(exclude_none=False),
    )
    return OfferingResponse.model_validate(offering)


@router.get("/offerings/{offering_id}", response_model=OfferingResponse, response_model_by_alias=True)
def get_offering(
    offering_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    offering = offering_service.get_offering_by_id(db, offering_id)
    if offering.vendor_id != vendor.vendor_id:
        raise HTTPException(status_code=403, detail="Not your offering")
    return OfferingResponse.model_validate(offering)


@router.put("/offerings/{offering_id}", response_model=OfferingResponse, response_model_by_alias=True)
def update_offering(
    offering_id: str,
    payload: OfferingUpdate,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    offering = offering_service.update_offering(
        db,
        offering_id=offering_id,
        vendor_id=vendor.vendor_id,
        data=payload.model_dump(exclude_unset=True),
    )
    return OfferingResponse.model_validate(offering)


@router.delete("/offerings/{offering_id}", status_code=204)
def delete_offering(
    offering_id: str,
    vendor: Vendor = Depends(require_approved_vendor),
    db: Session = Depends(get_db),
):
    offering_service.delete_offering(db, offering_id=offering_id, vendor_id=vendor.vendor_id)
    return Response(status_code=204)


# --- Inquiries ---

@router.get(
    "/inquiries",
    response_model=PaginatedInquiriesResponse,
    response_model_by_alias=True,
)
def list_vendor_inquiries(
    status: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = Query(default=None),
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    items, next_cursor = inquiry_service.list_user_inquiries(
        db,
        user_id=str(vendor.vendor_id),
        status=status,
        limit=limit,
        cursor=cursor,
    )
    return PaginatedInquiriesResponse(
        items=[InquiryResponse.model_validate(item) for item in items],
        nextCursor=next_cursor,
    )


@router.post(
    "/inquiries",
    response_model=InquiryResponse,
    response_model_by_alias=True,
    status_code=status.HTTP_201_CREATED,
)
def create_vendor_inquiry(
    payload: InquiryCreate,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    inquiry = inquiry_service.create_inquiry(
        db,
        user_id=str(vendor.vendor_id),
        role="VENDOR",
        subject=payload.subject,
        message=payload.message,
    )
    return InquiryResponse.model_validate(inquiry)


@router.get(
    "/inquiries/{inquiry_id}",
    response_model=InquiryResponse,
    response_model_by_alias=True,
)
def get_vendor_inquiry(
    inquiry_id: str,
    vendor: Vendor = Depends(get_current_vendor),
    db: Session = Depends(get_db),
):
    inquiry = inquiry_service.get_user_inquiry(
        db,
        inquiry_id=inquiry_id,
        user_id=str(vendor.vendor_id),
    )
    return InquiryResponse.model_validate(inquiry)
