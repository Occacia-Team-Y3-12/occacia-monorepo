from __future__ import annotations

from collections.abc import Iterable

from fastapi import HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.common.utils import now_utc
from app.models.event import Event
from app.models.offering import Offering
from app.models.package_execution_request import PackageExecutionRequest
from app.models.package_item import PackageItem
from app.models.recommendation_package import RecommendationPackage
from app.models.task import Task
from app.models.task_request import TaskRequest
from app.services.event_planning_service import event_planning_service


class PackageOrderService:
    def confirm_package_order(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        package_id: str,
        idempotency_key: str,
    ) -> tuple[PackageExecutionRequest, list[Task], list[TaskRequest]]:
        event = event_planning_service.get_event_for_customer(
            db,
            customer_id=customer_id,
            event_id=event_id,
        )
        if event.status != "ACTIVE":
            raise HTTPException(status_code=409, detail="Event must be active before confirming a package")

        existing_order = self._get_order_by_event_and_package(
            db,
            event_id=event_id,
            package_id=package_id,
        )
        if existing_order:
            return self._load_order_bundle(db, existing_order)

        idempotency_order = self._get_order_by_idempotency_key(db, idempotency_key=idempotency_key)
        if idempotency_order:
            if idempotency_order.event_id == event_id and idempotency_order.package_id == package_id:
                return self._load_order_bundle(db, idempotency_order)
            raise HTTPException(status_code=409, detail="Idempotency key is already used for a different package order")

        package = self._get_package_or_404(db, event_id=event_id, package_id=package_id)
        package_items, tasks_by_id, offerings_by_id = self._validate_package_for_confirmation(
            db,
            event=event,
            package=package,
        )

        confirmed_at = now_utc()
        order = PackageExecutionRequest(
            event_id=event_id,
            package_id=package.package_id,
            idempotency_key=idempotency_key,
            currency=package.currency,
            package_total_price=package.package_total_price,
            status="CREATED",
            status_updated_at=confirmed_at,
        )

        try:
            db.add(order)
            db.flush()

            for package_item in package_items:
                task = tasks_by_id[package_item.task_id]
                offering = offerings_by_id[package_item.offering_id]
                task.selected_offering_id = package_item.offering_id
                task.assigned_vendor_id = offering.vendor_id
                task.status = "PENDING"
                task.locked_at = confirmed_at
                task.status_updated_at = confirmed_at
                db.add(task)
                db.add(
                    TaskRequest(
                        package_order_id=order.execution_request_id,
                        task_id=task.task_id,
                        vendor_id=offering.vendor_id,
                        offering_id=offering.offering_id,
                        status="SENT",
                        requested_at=confirmed_at,
                        attempt_no=1,
                    )
                )

            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(order)
        return self._load_order_bundle(db, order)

    def list_customer_package_orders(
        self,
        db: Session,
        *,
        customer_id: str,
        limit: int,
        cursor: str | None,
    ) -> tuple[list[PackageExecutionRequest], str | None]:
        query = (
            db.query(PackageExecutionRequest)
            .join(Event, Event.event_id == PackageExecutionRequest.event_id)
            .filter(Event.customer_id == customer_id)
        )

        if cursor:
            cursor_order = (
                db.query(PackageExecutionRequest)
                .join(Event, Event.event_id == PackageExecutionRequest.event_id)
                .filter(
                    Event.customer_id == customer_id,
                    PackageExecutionRequest.execution_request_id == cursor,
                )
                .first()
            )
            if cursor_order:
                query = query.filter(
                    or_(
                        PackageExecutionRequest.created_at < cursor_order.created_at,
                        and_(
                            PackageExecutionRequest.created_at == cursor_order.created_at,
                            PackageExecutionRequest.id > cursor_order.id,
                        ),
                    )
                )

        items = (
            query.order_by(PackageExecutionRequest.created_at.desc(), PackageExecutionRequest.id.asc())
            .limit(limit + 1)
            .all()
        )
        next_cursor = None
        if len(items) > limit:
            next_cursor = items[limit].execution_request_id
            items = items[:limit]
        return items, next_cursor

    def get_customer_package_order_detail(
        self,
        db: Session,
        *,
        customer_id: str,
        package_order_id: str,
    ) -> tuple[PackageExecutionRequest, list[Task]]:
        order = self._get_customer_order_or_404(
            db,
            customer_id=customer_id,
            package_order_id=package_order_id,
        )
        task_ids = self._get_order_task_ids(db, package_order_id=order.execution_request_id)
        tasks = self._get_tasks_by_ids(db, task_ids=task_ids)
        return order, tasks

    def get_order_fulfillment_requests(
        self,
        db: Session,
        *,
        package_order_id: str,
    ) -> list[TaskRequest]:
        return (
            db.query(TaskRequest)
            .filter(TaskRequest.package_order_id == package_order_id)
            .order_by(TaskRequest.requested_at.asc(), TaskRequest.id.asc())
            .all()
        )

    def _load_order_bundle(
        self,
        db: Session,
        order: PackageExecutionRequest,
    ) -> tuple[PackageExecutionRequest, list[Task], list[TaskRequest]]:
        fulfillment_requests = self.get_order_fulfillment_requests(
            db,
            package_order_id=order.execution_request_id,
        )
        task_ids = [request.task_id for request in fulfillment_requests]
        tasks = self._get_tasks_by_ids(db, task_ids=task_ids)
        return order, tasks, fulfillment_requests

    def _validate_package_for_confirmation(
        self,
        db: Session,
        *,
        event: Event,
        package: RecommendationPackage,
    ) -> tuple[list[PackageItem], dict[str, Task], dict[str, Offering]]:
        package_items = (
            db.query(PackageItem)
            .filter(PackageItem.package_id == package.package_id)
            .order_by(PackageItem.id.asc())
            .all()
        )
        if not package_items:
            raise HTTPException(status_code=400, detail="Package has no items to confirm")

        task_ids = list(dict.fromkeys(item.task_id for item in package_items))
        offering_ids = list(dict.fromkeys(item.offering_id for item in package_items))

        tasks = (
            db.query(Task)
            .filter(Task.event_id == event.event_id, Task.task_id.in_(task_ids))
            .all()
        )
        if len(tasks) != len(task_ids):
            raise HTTPException(status_code=400, detail="Package references tasks that are no longer available")

        offerings = db.query(Offering).filter(Offering.offering_id.in_(offering_ids)).all()
        if len(offerings) != len(offering_ids):
            raise HTTPException(status_code=400, detail="Package contains offerings that are no longer available")

        tasks_by_id = {task.task_id: task for task in tasks}
        offerings_by_id = {offering.offering_id: offering for offering in offerings}

        for task in tasks:
            if task.confirmed_at is None:
                raise HTTPException(status_code=409, detail="Package tasks must be confirmed before confirmation")

        for offering in offerings:
            if not offering.is_active or not offering.is_available:
                raise HTTPException(status_code=400, detail=f"Offering {offering.offering_id} is no longer available")
            if offering.currency != package.currency:
                raise HTTPException(status_code=400, detail="Package contains offerings with mismatched currency")

        return package_items, tasks_by_id, offerings_by_id

    def _get_customer_order_or_404(
        self,
        db: Session,
        *,
        customer_id: str,
        package_order_id: str,
    ) -> PackageExecutionRequest:
        order = (
            db.query(PackageExecutionRequest)
            .join(Event, Event.event_id == PackageExecutionRequest.event_id)
            .filter(
                Event.customer_id == customer_id,
                PackageExecutionRequest.execution_request_id == package_order_id,
            )
            .first()
        )
        if not order:
            raise HTTPException(status_code=404, detail="Package order not found")
        return order

    def _get_order_by_event_and_package(
        self,
        db: Session,
        *,
        event_id: str,
        package_id: str,
    ) -> PackageExecutionRequest | None:
        return (
            db.query(PackageExecutionRequest)
            .filter(
                PackageExecutionRequest.event_id == event_id,
                PackageExecutionRequest.package_id == package_id,
            )
            .first()
        )

    def _get_order_by_idempotency_key(
        self,
        db: Session,
        *,
        idempotency_key: str,
    ) -> PackageExecutionRequest | None:
        return (
            db.query(PackageExecutionRequest)
            .filter(PackageExecutionRequest.idempotency_key == idempotency_key)
            .first()
        )

    def _get_package_or_404(
        self,
        db: Session,
        *,
        event_id: str,
        package_id: str,
    ) -> RecommendationPackage:
        package = (
            db.query(RecommendationPackage)
            .filter(
                RecommendationPackage.event_id == event_id,
                RecommendationPackage.package_id == package_id,
            )
            .first()
        )
        if not package:
            raise HTTPException(status_code=404, detail="Package not found")
        return package

    def _get_order_task_ids(
        self,
        db: Session,
        *,
        package_order_id: str,
    ) -> list[str]:
        task_ids = (
            db.query(TaskRequest.task_id)
            .filter(TaskRequest.package_order_id == package_order_id)
            .order_by(TaskRequest.requested_at.asc(), TaskRequest.id.asc())
            .all()
        )
        return list(dict.fromkeys(task_id for (task_id,) in task_ids))

    def _get_tasks_by_ids(
        self,
        db: Session,
        *,
        task_ids: Iterable[str],
    ) -> list[Task]:
        normalized_task_ids = list(dict.fromkeys(task_ids))
        if not normalized_task_ids:
            return []

        tasks = db.query(Task).filter(Task.task_id.in_(normalized_task_ids)).all()
        tasks_by_id = {task.task_id: task for task in tasks}
        return [tasks_by_id[task_id] for task_id in normalized_task_ids if task_id in tasks_by_id]


package_order_service = PackageOrderService()
