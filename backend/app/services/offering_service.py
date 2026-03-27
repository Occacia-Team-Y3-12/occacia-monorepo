from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.event import Event
from app.models.offering import Offering
from app.models.task import Task
from app.models.task_offering import TaskOffering
from app.models.vendor import Vendor
from app.schemas.offering_schema import OFFERING_CATEGORIES

logger = logging.getLogger(__name__)

_CATEGORY_MAP = {
    "cakes & bakery": ["cake", "bakery", "baking", "dessert", "pastry", "cupcake"],
    "catering": ["catering", "food", "buffet", "meal", "lunch", "dinner", "breakfast", "snack"],
    "drinks & bar": ["drink", "bar", "beverage", "alcohol", "juice", "cocktail"],
    "food & beverage": ["feast", "cuisine", "menu"],
    "dj & music": ["dj", "music", "sound", "audio", "disc", "playlist"],
    "photography & videography": ["photo", "photograph", "video", "videograph", "camera", "film", "coverage"],
    "band & live music": ["band", "live music", "singer", "performer", "entertainment music"],
    "entertainment": ["entertainment", "magician", "clown", "performer", "show", "comedian"],
    "floral arrangements": ["flower", "floral", "bouquet", "arrangement", "petal"],
    "event decoration": ["decor", "decoration", "balloon", "setup", "theme", "backdrop", "table"],
    "decor & flowers": ["centerpiece", "garland"],
    "venue & spaces": ["venue", "hall", "space", "room", "location", "place", "ground"],
    "transport": ["transport", "car", "bus", "vehicle", "driver", "shuttle", "limo"],
}


class OfferingService:
    def create_offering(self, db: Session, vendor_id: str, data: dict) -> Offering:
        offering = Offering(vendor_id=vendor_id, **data)
        db.add(offering)
        db.commit()
        db.refresh(offering)
        return offering

    def get_offering_by_id(self, db: Session, offering_id: str) -> Offering:
        offering = db.query(Offering).filter(Offering.offering_id == offering_id).first()
        if not offering:
            raise HTTPException(status_code=404, detail="Offering not found")
        return offering

    def list_vendor_offerings(self, db: Session, vendor_id: str, include_inactive: bool = False) -> list[Offering]:
        query = db.query(Offering).filter(Offering.vendor_id == vendor_id)
        if not include_inactive:
            query = query.filter(Offering.is_active.is_(True))
        return query.order_by(Offering.updated_at.desc(), Offering.id.desc()).all()

    def list_all_offerings(
        self,
        db: Session,
        category: Optional[str] = None,
        vendor_id: Optional[str] = None,
    ) -> list[Offering]:
        query = db.query(Offering).filter(
            Offering.is_active.is_(True),
            Offering.is_available.is_(True),
        )
        if category:
            query = query.filter(Offering.category == category)
        if vendor_id:
            query = query.filter(Offering.vendor_id == vendor_id)
        return query.order_by(Offering.price.asc(), Offering.id.asc()).all()

    def update_offering(self, db: Session, offering_id: str, vendor_id: str, data: dict) -> Offering:
        offering = (
            db.query(Offering)
            .filter(Offering.offering_id == offering_id, Offering.vendor_id == vendor_id)
            .first()
        )
        if not offering:
            raise HTTPException(status_code=404, detail="Offering not found")
        for key, value in data.items():
            if value is not None:
                setattr(offering, key, value)
        db.commit()
        db.refresh(offering)
        return offering

    def delete_offering(self, db: Session, offering_id: str, vendor_id: str) -> None:
        offering = (
            db.query(Offering)
            .filter(Offering.offering_id == offering_id, Offering.vendor_id == vendor_id)
            .first()
        )
        if not offering:
            raise HTTPException(status_code=404, detail="Offering not found")
        offering.is_active = False
        db.commit()

    def infer_category(self, task_name: str, vendor_category: str | None = None) -> str:
        """
        Infer the offering category for a task.
        If vendor_category is explicitly provided (set by AI), use it directly.
        Otherwise fall back to keyword matching on the task name.
        """
        # Prefer AI-provided vendor_category
        if vendor_category:
            for canonical in OFFERING_CATEGORIES:
                if canonical.lower() == vendor_category.lower():
                    return canonical

        # Keyword fallback
        lowered = (task_name or "").lower()
        for category, keywords in _CATEGORY_MAP.items():
            if any(keyword in lowered for keyword in keywords):
                for canonical in OFFERING_CATEGORIES:
                    if canonical.lower() == category:
                        return canonical
        return "Other"

    def find_offerings_for_task(
        self,
        db: Session,
        task: Task,
        limit: int = 1,  # Default to 1 — one offering per task
    ) -> list[dict]:
        vendor_category = getattr(task, "vendor_category", None)
        inferred_category = self.infer_category(task.name, vendor_category)

        query = (
            db.query(Offering)
            .join(Vendor, Vendor.vendor_id == Offering.vendor_id)
            .filter(
                Offering.is_active.is_(True),
                Offering.is_available.is_(True),
                Vendor.approval_status == "APPROVED",
            )
        )
        if task.budget_max:
            query = query.filter(Offering.price <= float(task.budget_max) * 1.2)

        offerings = query.all()
        if not offerings:
            offerings = (
                db.query(Offering)
                .join(Vendor, Vendor.vendor_id == Offering.vendor_id)
                .filter(
                    Offering.is_active.is_(True),
                    Offering.is_available.is_(True),
                    Offering.category == inferred_category,
                    Vendor.approval_status == "APPROVED",
                )
                .all()
            )

        scored: list[dict] = []
        for offering in offerings:
            score = 10.0
            if offering.category == inferred_category:
                score += 5

            if task.budget_max is not None:
                budget_max = float(task.budget_max)
                if offering.price <= budget_max:
                    score += 5
                elif offering.price <= budget_max * 1.1:
                    score += 2
                elif offering.price <= budget_max * 1.2:
                    score -= 2

            if offering.is_available:
                score += 3

            score += {"HIGH": 4, "MEDIUM": 2, "LOW": 0}.get((offering.quality_tier or "").upper(), 0)
            scored.append({"offering": offering, "score": score})

        scored.sort(key=lambda item: (-item["score"], item["offering"].price, item["offering"].offering_id))
        top = scored[:limit]
        return [
            {"offering": row["offering"], "rank": index + 1, "score": row["score"]}
            for index, row in enumerate(top)
        ]

    def save_task_offering_shortlist(
        self,
        db: Session,
        task_id: str,
        offerings_with_rank: list[dict],
    ) -> list[TaskOffering]:
        (
            db.query(TaskOffering)
            .filter(TaskOffering.task_id == task_id)
            .delete(synchronize_session=False)
        )
        db.flush()

        rows: list[TaskOffering] = []
        for item in offerings_with_rank:
            row = TaskOffering(
                task_id=task_id,
                offering_id=item["offering"].offering_id,
                rank=item["rank"],
                score=item.get("score"),
                is_selected=False,
            )
            db.add(row)
            rows.append(row)
        db.commit()
        for row in rows:
            db.refresh(row)
        return rows

    def get_task_offerings(self, db: Session, task_id: str) -> list[TaskOffering]:
        return (
            db.query(TaskOffering)
            .filter(TaskOffering.task_id == task_id)
            .order_by(TaskOffering.rank.asc(), TaskOffering.id.asc())
            .all()
        )

    def select_offering(self, db: Session, task_id: str, offering_id: str, customer_id: str) -> TaskOffering:
        task = db.query(Task).filter(Task.task_id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        event = db.query(Event).filter(Event.event_id == task.event_id, Event.customer_id == customer_id).first()
        if not event:
            raise HTTPException(status_code=403, detail="Not your event")

        task_offering = (
            db.query(TaskOffering)
            .filter(TaskOffering.task_id == task_id, TaskOffering.offering_id == offering_id)
            .first()
        )
        if not task_offering:
            raise HTTPException(status_code=404, detail="Offering not in shortlist for this task")

        (
            db.query(TaskOffering)
            .filter(TaskOffering.task_id == task_id, TaskOffering.offering_id != offering_id)
            .update({"is_selected": False, "selected_at": None}, synchronize_session=False)
        )

        task_offering.is_selected = True
        task_offering.selected_at = datetime.now(timezone.utc)

        offering = self.get_offering_by_id(db, offering_id)
        task.selected_offering_id = offering_id
        task.assigned_vendor_id = offering.vendor_id
        db.add(task)
        db.commit()
        db.refresh(task_offering)
        return task_offering


offering_service = OfferingService()