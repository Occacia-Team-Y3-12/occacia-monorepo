from __future__ import annotations

import asyncio
import concurrent.futures
import logging
import re
from dataclasses import dataclass
from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.utils import now_utc
from app.models.event_persona import EventPersona
from app.models.offering import Offering
from app.models.package_item import PackageItem
from app.models.persona import Persona
from app.models.recommendation_package import RecommendationPackage
from app.models.task import Task
from app.models.task_recommendation import TaskRecommendation
from app.models.vendor import Vendor
from app.schemas.recommendation_schema import (
    CreateCustomPackageRequest,
    RecommendationPackageItemResponse,
    RecommendationPackageDetailsResponse,
    RecommendationPackageListResponse,
    RecommendationPackageResponse,
    TaskRecommendationListResponse,
    TaskRecommendationResponse,
    UpdateCustomPackageRequest,
)
from app.services.groq_ai_service import groq_ai_service as ai_service
from app.services.event_planning_service import event_planning_service
from app.services.offering_service import offering_service

logger = logging.getLogger(__name__)

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_PACKAGE_TYPE_ORDER = {"BUDGET": 0, "RECOMMENDED": 1, "HIGH_QUALITY": 2}
_PACKAGE_TTL = timedelta(minutes=5)


@dataclass(slots=True)
class RankedOffering:
    offering: Offering
    score: float
    rank: int


def _run_async(coro):
    """
    Run an async coroutine from a sync context, safely handling the case
    where we may already be inside a running event loop (e.g. FastAPI threadpool).
    """
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're inside a running loop (FastAPI runs sync endpoints in a
            # threadpool that shares the loop). Spin up a fresh thread with
            # its own event loop to avoid blocking the main loop.
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No current event loop at all — just create one
        return asyncio.run(coro)


class RecommendationService:
    def generate_packages(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
    ) -> RecommendationPackageListResponse:
        event = event_planning_service.get_event_for_customer(
            db,
            customer_id=customer_id,
            event_id=event_id,
        )
        if event.status != "ACTIVE":
            raise HTTPException(status_code=409, detail="Event must be active before generating packages")

        tasks = self._get_confirmed_tasks(db, event_id=event_id)
        if not tasks:
            raise HTTPException(status_code=400, detail="No confirmed tasks available for recommendations")

        # Regenerate full shortlist (5) for all confirmed tasks (UC-16 source of truth).
        for task in tasks:
            try:
                shortlist = offering_service.find_offerings_for_task(db=db, task=task, limit=5)
                if shortlist:
                    offering_service.save_task_offering_shortlist(
                        db=db,
                        task_id=task.task_id,
                        offerings_with_rank=shortlist,
                    )
            except Exception as exc:
                logger.warning("Task offering shortlist generation failed for %s: %s", task.task_id, exc)

        personas = self._get_event_personas(db, event_id=event_id)
        ranked_by_task: dict[str, list[RankedOffering]] = {}
        for task in tasks:
            ranked = self._rank_offerings_for_task(
                db,
                task=task,
                event=event,
                personas=personas,
            )
            if not ranked:
                raise HTTPException(
                    status_code=400,
                    detail=f"No valid offerings available for task {task.task_id}",
                )
            ranked_by_task[task.task_id] = ranked

        self._delete_existing_generated_records(db, event_id=event_id)

        generated_at = now_utc()
        expires_at = generated_at + _PACKAGE_TTL

        for task in tasks:
            for ranked in ranked_by_task[task.task_id]:
                db.add(
                    TaskRecommendation(
                        event_id=event_id,
                        task_id=task.task_id,
                        offering_id=ranked.offering.offering_id,
                        score=ranked.score,
                        rank=ranked.rank,
                        generated_at=generated_at,
                    )
                )

        package_rows: list[RecommendationPackage] = []
        for package_type in ("BUDGET", "RECOMMENDED", "HIGH_QUALITY"):
            package_row = RecommendationPackage(
                event_id=event_id,
                package_type=package_type,
                package_total_price=0.0,
                currency=self._resolve_currency(tasks, ranked_by_task),
                is_customized=False,
                generated_at=generated_at,
                expires_at=expires_at,
            )
            db.add(package_row)
            db.flush()

            total_price = 0.0
            for task in tasks:
                ranked = self._select_ranked_offering(package_type, ranked_by_task[task.task_id])
                quantity = max(task.quantity, 1)
                line_total = ranked.offering.price * quantity
                total_price += line_total
                package_item = PackageItem(
                    package_id=package_row.package_id,
                    task_id=task.task_id,
                    offering_id=ranked.offering.offering_id,
                    quantity=quantity,
                    unit_price=ranked.offering.price,
                    line_total=line_total,
                )
                db.add(package_item)

            package_row.package_total_price = total_price
            db.add(package_row)
            package_rows.append(package_row)

        db.commit()
        for row in package_rows:
            db.refresh(row)

        return self._build_package_list_response(
            db,
            event_id=event_id,
            packages=package_rows,
        )

    def get_packages(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
    ) -> RecommendationPackageListResponse:
        event_planning_service.get_event_for_customer(
            db,
            customer_id=customer_id,
            event_id=event_id,
        )
        packages = (
            db.query(RecommendationPackage)
            .filter(
                RecommendationPackage.event_id == event_id,
                RecommendationPackage.is_customized.is_(False),
            )
            .all()
        )
        if not packages:
            raise HTTPException(status_code=404, detail="Recommendation packages not found")
        return self._build_package_list_response(db, event_id=event_id, packages=packages)

    def get_package_by_id(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        package_id: str,
    ) -> RecommendationPackageDetailsResponse:
        event_planning_service.get_event_for_customer(
            db,
            customer_id=customer_id,
            event_id=event_id,
        )
        package = self._get_package_or_404(db, event_id=event_id, package_id=package_id)
        return self._build_package_details_response(db, event_id=event_id, package=package)

    def get_task_recommendations(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        task_id: str,
    ) -> TaskRecommendationListResponse:
        event_planning_service.get_event_for_customer(
            db,
            customer_id=customer_id,
            event_id=event_id,
        )
        task = (
            db.query(Task)
            .filter(Task.event_id == event_id, Task.task_id == task_id)
            .first()
        )
        if not task:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

        recommendations = self._get_task_recommendations_for_tasks(
            db,
            event_id=event_id,
            task_ids=[task_id],
        )
        return TaskRecommendationListResponse(items=recommendations.get(task_id, []))

    def create_custom_package(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        request: CreateCustomPackageRequest,
    ) -> RecommendationPackageDetailsResponse:
        event_planning_service.get_event_for_customer(
            db,
            customer_id=customer_id,
            event_id=event_id,
        )
        base_package = self._get_package_or_404(db, event_id=event_id, package_id=request.base_package_id)
        if base_package.is_customized:
            raise HTTPException(status_code=400, detail="Base package must be system generated")

        custom_package = RecommendationPackage(
            event_id=event_id,
            package_type="CUSTOM",
            package_total_price=0.0,
            currency=base_package.currency,
            is_customized=True,
            base_package_id=base_package.package_id,
            created_by_customer_id=customer_id,
            generated_at=now_utc(),
            expires_at=base_package.expires_at,
        )
        db.add(custom_package)
        db.flush()

        try:
            self._replace_package_items(
                db,
                event_id=event_id,
                package=custom_package,
                base_package=base_package,
                requested_items=request.items,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(custom_package)
        return self._build_package_details_response(db, event_id=event_id, package=custom_package)

    def update_custom_package(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        package_id: str,
        request: UpdateCustomPackageRequest,
    ) -> RecommendationPackageDetailsResponse:
        event_planning_service.get_event_for_customer(
            db,
            customer_id=customer_id,
            event_id=event_id,
        )
        package = self._get_package_or_404(db, event_id=event_id, package_id=package_id)
        if not package.is_customized:
            raise HTTPException(status_code=400, detail="Only custom packages can be updated")
        if package.created_by_customer_id and package.created_by_customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Custom package does not belong to this customer")

        base_package = self._get_package_or_404(
            db,
            event_id=event_id,
            package_id=package.base_package_id or package.package_id,
        )

        try:
            self._replace_package_items(
                db,
                event_id=event_id,
                package=package,
                base_package=base_package,
                requested_items=request.items,
            )
            db.commit()
        except Exception:
            db.rollback()
            raise

        db.refresh(package)
        return self._build_package_details_response(db, event_id=event_id, package=package)

    def delete_custom_package(
        self,
        db: Session,
        *,
        customer_id: str,
        event_id: str,
        package_id: str,
    ) -> None:
        event_planning_service.get_event_for_customer(
            db,
            customer_id=customer_id,
            event_id=event_id,
        )
        package = self._get_package_or_404(db, event_id=event_id, package_id=package_id)
        if not package.is_customized:
            raise HTTPException(status_code=400, detail="Only custom packages can be deleted")
        if package.created_by_customer_id and package.created_by_customer_id != customer_id:
            raise HTTPException(status_code=403, detail="Custom package does not belong to this customer")

        (
            db.query(PackageItem)
            .filter(PackageItem.package_id == package.package_id)
            .delete(synchronize_session=False)
        )
        db.delete(package)
        db.commit()

    def _build_package_list_response(
        self,
        db: Session,
        *,
        event_id: str,
        packages: list[RecommendationPackage],
    ) -> RecommendationPackageListResponse:
        ordered_packages = sorted(packages, key=lambda pkg: _PACKAGE_TYPE_ORDER.get(pkg.package_type, 999))
        package_ids = [pkg.package_id for pkg in ordered_packages]
        package_items = (
            db.query(PackageItem)
            .filter(PackageItem.package_id.in_(package_ids))
            .all()
        )
        items_by_package: dict[str, list[PackageItem]] = {package_id: [] for package_id in package_ids}
        for item in package_items:
            items_by_package.setdefault(item.package_id, []).append(item)

        task_ids = list({item.task_id for item in package_items})
        offering_ids = list({item.offering_id for item in package_items})
        tasks = (
            db.query(Task)
            .filter(Task.task_id.in_(task_ids))
            .all()
            if task_ids
            else []
        )
        offerings = (
            db.query(Offering)
            .filter(Offering.offering_id.in_(offering_ids))
            .all()
            if offering_ids
            else []
        )
        recommendations = (
            db.query(TaskRecommendation)
            .filter(
                TaskRecommendation.event_id == event_id,
                TaskRecommendation.offering_id.in_(offering_ids),
            )
            .all()
            if offering_ids
            else []
        )

        tasks_by_id = {task.task_id: task for task in tasks}
        offerings_by_id = {offering.offering_id: offering for offering in offerings}
        vendors = (
            db.query(Vendor)
            .filter(Vendor.vendor_id.in_([offering.vendor_id for offering in offerings]))
            .all()
            if offerings
            else []
        )
        vendors_by_id = {vendor.vendor_id: vendor for vendor in vendors}
        rec_rank_by_key = {
            (rec.task_id, rec.offering_id): rec.rank
            for rec in recommendations
        }

        package_responses: list[RecommendationPackageResponse] = []
        now = now_utc()
        for package_row in ordered_packages:
            generated_at = self._ensure_aware_datetime(package_row.generated_at)
            expires_at = self._ensure_aware_datetime(package_row.expires_at)
            item_responses: list[RecommendationPackageItemResponse] = []
            sorted_items = sorted(
                items_by_package.get(package_row.package_id, []),
                key=lambda item: tasks_by_id.get(item.task_id).created_at if tasks_by_id.get(item.task_id) else now,
            )
            for item in sorted_items:
                task = tasks_by_id.get(item.task_id)
                offering = offerings_by_id.get(item.offering_id)
                vendor = vendors_by_id.get(offering.vendor_id) if offering else None
                item_responses.append(
                    RecommendationPackageItemResponse(
                        taskId=item.task_id,
                        taskName=task.name if task else item.task_id,
                        quantity=item.quantity,
                        offeringId=item.offering_id,
                        offeringName=offering.name if offering else item.offering_id,
                        offeringCategory=offering.category if offering else "Unknown",
                        vendorId=offering.vendor_id if offering else "",
                        vendorName=vendor.display_name or vendor.business_name if vendor else None,
                        unitPrice=item.unit_price,
                        taskPrice=item.line_total,
                        currency=offering.currency if offering else package_row.currency,
                        aiRank=rec_rank_by_key.get((item.task_id, item.offering_id)),
                    )
                )
            is_expired = bool(expires_at and expires_at <= now)
            package_responses.append(
                RecommendationPackageResponse(
                    packageId=package_row.package_id,
                    eventId=package_row.event_id,
                    packageType=package_row.package_type,
                    packageTotalPrice=package_row.package_total_price,
                    currency=package_row.currency,
                    isCustomized=package_row.is_customized,
                    basePackageId=package_row.base_package_id,
                    createdByCustomerId=package_row.created_by_customer_id,
                    generatedAt=generated_at,
                    expiresAt=expires_at,
                    isExpired=is_expired,
                    items=item_responses,
                )
            )

        generated_at = max(self._ensure_aware_datetime(pkg.generated_at) for pkg in ordered_packages)
        expires_at = min(
            (self._ensure_aware_datetime(pkg.expires_at) for pkg in ordered_packages if pkg.expires_at is not None),
            default=None,
        )
        is_expired = bool(expires_at and expires_at <= now)
        return RecommendationPackageListResponse(
            eventId=event_id,
            generatedAt=generated_at,
            expiresAt=expires_at,
            isExpired=is_expired,
            packages=package_responses,
        )

    def _build_package_details_response(
        self,
        db: Session,
        *,
        event_id: str,
        package: RecommendationPackage,
    ) -> RecommendationPackageDetailsResponse:
        package_response = self._build_package_list_response(db, event_id=event_id, packages=[package]).packages[0]
        task_ids = [item.task_id for item in self._get_package_items(db, package.package_id)]
        allowed_offerings = self._get_task_recommendations_for_tasks(db, event_id=event_id, task_ids=task_ids)
        return RecommendationPackageDetailsResponse(
            **package_response.model_dump(),
            allowedOfferingsByTask=allowed_offerings,
        )

    def _delete_existing_generated_records(self, db: Session, *, event_id: str) -> None:
        existing_package_ids = [
            package_id
            for (package_id,) in (
                db.query(RecommendationPackage.package_id)
                .filter(
                    RecommendationPackage.event_id == event_id,
                    RecommendationPackage.is_customized.is_(False),
                )
                .all()
            )
        ]
        if existing_package_ids:
            (
                db.query(PackageItem)
                .filter(PackageItem.package_id.in_(existing_package_ids))
                .delete(synchronize_session=False)
            )
            (
                db.query(RecommendationPackage)
                .filter(
                    RecommendationPackage.event_id == event_id,
                    RecommendationPackage.is_customized.is_(False),
                )
                .delete(synchronize_session=False)
            )
        (
            db.query(TaskRecommendation)
            .filter(TaskRecommendation.event_id == event_id)
            .delete(synchronize_session=False)
        )
        db.flush()

    def _get_confirmed_tasks(self, db: Session, *, event_id: str) -> list[Task]:
        return (
            db.query(Task)
            .filter(Task.event_id == event_id, Task.confirmed_at.is_not(None))
            .order_by(Task.created_at.asc(), Task.id.asc())
            .all()
        )

    def _get_package_or_404(self, db: Session, *, event_id: str, package_id: str) -> RecommendationPackage:
        package = (
            db.query(RecommendationPackage)
            .filter(
                RecommendationPackage.event_id == event_id,
                RecommendationPackage.package_id == package_id,
            )
            .first()
        )
        if not package:
            raise HTTPException(status_code=404, detail=f"Recommendation package {package_id} not found")
        return package

    def _get_package_items(self, db: Session, package_id: str) -> list[PackageItem]:
        return (
            db.query(PackageItem)
            .filter(PackageItem.package_id == package_id)
            .all()
        )

    def _get_task_recommendations_for_tasks(
        self,
        db: Session,
        *,
        event_id: str,
        task_ids: list[str],
    ) -> dict[str, list[TaskRecommendationResponse]]:
        if not task_ids:
            return {}

        recommendations = (
            db.query(TaskRecommendation)
            .filter(
                TaskRecommendation.event_id == event_id,
                TaskRecommendation.task_id.in_(task_ids),
            )
            .order_by(TaskRecommendation.task_id.asc(), TaskRecommendation.rank.asc(), TaskRecommendation.id.asc())
            .all()
        )
        response: dict[str, list[TaskRecommendationResponse]] = {task_id: [] for task_id in task_ids}
        for recommendation in recommendations:
            response.setdefault(recommendation.task_id, []).append(
                TaskRecommendationResponse(
                    recommendationId=recommendation.recommendation_id,
                    eventId=recommendation.event_id,
                    taskId=recommendation.task_id,
                    offeringId=recommendation.offering_id,
                    score=recommendation.score,
                    rank=recommendation.rank,
                    generatedAt=self._ensure_aware_datetime(recommendation.generated_at),
                )
            )
        return response

    def _replace_package_items(
        self,
        db: Session,
        *,
        event_id: str,
        package: RecommendationPackage,
        base_package: RecommendationPackage,
        requested_items,
    ) -> None:
        requested_by_task = {}
        for item in requested_items:
            if item.task_id in requested_by_task:
                raise HTTPException(status_code=400, detail=f"Duplicate task {item.task_id} in package update")
            requested_by_task[item.task_id] = item

        base_items = self._get_package_items(db, base_package.package_id)
        if not base_items:
            raise HTTPException(status_code=400, detail="Base package has no items")

        base_items_by_task = {item.task_id: item for item in base_items}
        invalid_task_ids = sorted(set(requested_by_task) - set(base_items_by_task))
        if invalid_task_ids:
            raise HTTPException(
                status_code=400,
                detail=f"Tasks not part of base package: {', '.join(invalid_task_ids)}",
            )

        recommendations_by_task = self._get_task_recommendations_for_tasks(
            db,
            event_id=event_id,
            task_ids=list(base_items_by_task),
        )
        offering_ids = [item.offering_id for item in requested_by_task.values()]
        offerings = (
            db.query(Offering)
            .filter(Offering.offering_id.in_(offering_ids))
            .all()
            if offering_ids
            else []
        )
        offerings_by_id = {offering.offering_id: offering for offering in offerings}

        new_rows: list[PackageItem] = []
        total_price = 0.0
        currency = None
        for task_id, requested_item in requested_by_task.items():
            allowed_offering_ids = {
                recommendation.offering_id
                for recommendation in recommendations_by_task.get(task_id, [])
            }
            if requested_item.offering_id not in allowed_offering_ids:
                raise HTTPException(
                    status_code=400,
                    detail=f"Offering {requested_item.offering_id} is not in the shortlist for task {task_id}",
                )

            offering = offerings_by_id.get(requested_item.offering_id)
            if offering is None:
                raise HTTPException(status_code=404, detail=f"Offering {requested_item.offering_id} not found")
            if not (offering.is_active and offering.is_available):
                raise HTTPException(
                    status_code=409,
                    detail=f"Offering {requested_item.offering_id} is no longer available",
                )

            base_item = base_items_by_task[task_id]
            quantity = requested_item.quantity or base_item.quantity
            if quantity < 1:
                raise HTTPException(status_code=400, detail=f"Quantity for task {task_id} must be at least 1")

            line_total = offering.price * quantity
            total_price += line_total
            currency = currency or offering.currency
            if offering.currency != currency:
                raise HTTPException(status_code=400, detail="Custom package requires a single currency")

            new_rows.append(
                PackageItem(
                    package_id=package.package_id,
                    task_id=task_id,
                    offering_id=offering.offering_id,
                    quantity=quantity,
                    unit_price=offering.price,
                    line_total=line_total,
                )
            )

        (
            db.query(PackageItem)
            .filter(PackageItem.package_id == package.package_id)
            .delete(synchronize_session=False)
        )
        for row in new_rows:
            db.add(row)

        package.package_total_price = total_price
        package.currency = currency or base_package.currency
        package.base_package_id = base_package.package_id
        package.is_customized = True
        db.add(package)
        db.flush()

    def _get_event_personas(self, db: Session, *, event_id: str) -> list[Persona]:
        return (
            db.query(Persona)
            .join(EventPersona, EventPersona.persona_id == Persona.persona_id)
            .filter(EventPersona.event_id == event_id)
            .all()
        )

    def _rank_offerings_for_task(self, db: Session, *, task: Task, event, personas: list[Persona]) -> list[RankedOffering]:
        query = db.query(Offering).filter(Offering.is_active.is_(True), Offering.is_available.is_(True))
        if task.needs_vendor:
            query = query.filter(Offering.category.ilike(task.needs_vendor))
        offerings = query.all()

        scored: list[tuple[Offering, float]] = []
        task_tokens = self._build_task_context_tokens(task=task, event=event, personas=personas)
        for offering in offerings:
            score = self._score_offering(offering=offering, task=task, task_tokens=task_tokens, event=event)
            scored.append((offering, score))

        scored.sort(
            key=lambda item: (
                -item[1],
                item[0].price,
                item[0].offering_id,
            )
        )

        seen_vendors: set[str] = set()
        unique_ranked: list[RankedOffering] = []
        for offering, score in scored:
            if offering.vendor_id in seen_vendors:
                continue
            seen_vendors.add(offering.vendor_id)
            unique_ranked.append(
                RankedOffering(
                    offering=offering,
                    score=round(score, 4),
                    rank=len(unique_ranked) + 1,
                )
            )
            if len(unique_ranked) == 12:
                break

        ai_ranked = self._apply_ai_shortlist(
            ranked_offerings=unique_ranked,
            task=task,
            event=event,
            personas=personas,
        )
        return ai_ranked[:5]

    def _score_offering(self, *, offering: Offering, task: Task, task_tokens: set[str], event) -> float:
        offering_tokens = self._tokenize(
            " ".join(
                value
                for value in (
                    offering.name,
                    offering.description,
                    offering.category,
                )
                if value
            )
        )
        overlap_score = float(len(task_tokens & offering_tokens))
        score = overlap_score

        if task.needs_vendor and offering.category.lower() == task.needs_vendor.lower():
            score += 6.0

        if task.budget_min is not None or task.budget_max is not None:
            if task.budget_min is not None and task.budget_max is not None and task.budget_min <= offering.price <= task.budget_max:
                score += 3.0
            elif task.budget_max is not None and offering.price <= task.budget_max:
                score += 2.0
            elif task.budget_min is not None and offering.price >= task.budget_min:
                score += 1.0
            else:
                distance = 0.0
                if task.budget_max is not None and offering.price > task.budget_max:
                    distance = offering.price - task.budget_max
                elif task.budget_min is not None and offering.price < task.budget_min:
                    distance = task.budget_min - offering.price
                score -= min(distance / 100.0, 5.0)
        else:
            score += 1.0

        if event.location_text and event.location_text.lower() in offering_tokens:
            score += 0.5

        return score

    def _build_task_context_tokens(self, *, task: Task, event, personas: list[Persona]) -> set[str]:
        parts = [
            event.title,
            event.description,
            event.event_type,
            event.location_text,
            task.name,
            task.description,
            task.needs_vendor,
        ]
        for persona in personas:
            parts.extend(
                [
                    persona.name,
                    persona.relationship,
                    persona.personality,
                    " ".join(persona.food_preferences or []),
                    " ".join(persona.color_preferences or []),
                    " ".join(persona.music_preferences or []),
                    " ".join(persona.personality_tags or []),
                ]
            )
        return self._tokenize(" ".join(part for part in parts if part))

    def _tokenize(self, raw: str) -> set[str]:
        return {token for token in _TOKEN_RE.findall((raw or "").lower()) if len(token) > 1}

    def _ensure_aware_datetime(self, value):
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=now_utc().tzinfo)
        return value

    def _apply_ai_shortlist(
        self,
        *,
        ranked_offerings: list[RankedOffering],
        task: Task,
        event,
        personas: list[Persona],
    ) -> list[RankedOffering]:
        # FIX: recommend_offerings_for_task is async but this method is sync.
        # Use _run_async() to safely bridge the sync/async boundary regardless
        # of whether we're inside a running event loop or not.
        try:
            ai_shortlist = _run_async(
                ai_service.recommend_offerings_for_task(
                    event_context={
                        "event_id": event.event_id,
                        "title": event.title,
                        "description": event.description,
                        "event_type": event.event_type,
                        "location_text": event.location_text,
                        "status": event.status,
                    },
                    personas=[
                        {
                            "persona_id": persona.persona_id,
                            "name": persona.name,
                            "relationship": persona.relationship,
                            "personality": persona.personality,
                            "food_preferences": persona.food_preferences or [],
                            "color_preferences": persona.color_preferences or [],
                            "music_preferences": persona.music_preferences or [],
                            "personality_tags": persona.personality_tags or [],
                        }
                        for persona in personas
                    ],
                    task={
                        "task_id": task.task_id,
                        "name": task.name,
                        "description": task.description,
                        "quantity": task.quantity,
                        "vendor_category": task.needs_vendor,
                        "budget_min": task.budget_min,
                        "budget_max": task.budget_max,
                        "currency": task.currency,
                    },
                    offerings=[
                        {
                            "offering_id": ranked.offering.offering_id,
                            "vendor_id": ranked.offering.vendor_id,
                            "name": ranked.offering.name,
                            "category": ranked.offering.category,
                            "description": ranked.offering.description,
                            "price": ranked.offering.price,
                            "currency": ranked.offering.currency,
                            "fallback_score": ranked.score,
                            "fallback_rank": ranked.rank,
                        }
                        for ranked in ranked_offerings
                    ],
                    limit=5,
                )
            )
        except Exception as exc:
            logger.warning("AI shortlist failed, falling back to score order: %s", exc)
            ai_shortlist = None

        if not ai_shortlist:
            return ranked_offerings

        ranked_by_id = {ranked.offering.offering_id: ranked for ranked in ranked_offerings}
        ordered: list[RankedOffering] = []
        for offering_id in ai_shortlist:
            ranked = ranked_by_id.get(offering_id)
            if ranked is not None:
                ordered.append(ranked)
        for ranked in ranked_offerings:
            if ranked.offering.offering_id not in {item.offering.offering_id for item in ordered}:
                ordered.append(ranked)

        return [
            RankedOffering(
                offering=ranked.offering,
                score=ranked.score,
                rank=index + 1,
            )
            for index, ranked in enumerate(ordered)
        ]

    def _select_ranked_offering(self, package_type: str, ranked_offerings: list[RankedOffering]) -> RankedOffering:
        if package_type == "BUDGET":
            return min(ranked_offerings, key=lambda item: (item.offering.price, item.rank, item.offering.offering_id))
        if package_type == "HIGH_QUALITY":
            return max(ranked_offerings, key=lambda item: (item.offering.price, -item.rank, item.offering.offering_id))
        return min(ranked_offerings, key=lambda item: (item.rank, -item.score, item.offering.offering_id))

    def _resolve_currency(self, tasks: list[Task], ranked_by_task: dict[str, list[RankedOffering]]) -> str:
        offering_currencies = {
            ranked_list[0].offering.currency
            for ranked_list in ranked_by_task.values()
            if ranked_list
        }
        if len(offering_currencies) != 1:
            raise HTTPException(status_code=400, detail="Recommendations require a single currency")
        offering_currency = next(iter(offering_currencies))

        task_currencies = {task.currency for task in tasks if task.currency}
        if task_currencies and (len(task_currencies) != 1 or offering_currency not in task_currencies):
            raise HTTPException(status_code=400, detail="Task and offering currencies must match")
        return offering_currency


recommendation_service = RecommendationService()
