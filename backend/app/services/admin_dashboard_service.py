from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from app.common.utils import now_utc
from app.models.admin import Admin
from app.models.customer import Customer
from app.models.event import Event
from app.models.package_execution_request import PackageExecutionRequest
from app.models.user import User
from app.models.vendor import Vendor


@dataclass
class MetricCounts:
    total: int
    active: int
    pending: int


class AdminDashboardAggregator:
    def get_dashboard_metrics(self, db: Session) -> dict:
        users_table = self._aggregate_counts(
            db,
            model=User,
            status_column=User.status,
            active_values=("ACTIVE",),
            pending_values=("PENDING",),
        )
        vendors = self._aggregate_counts(
            db,
            model=Vendor,
            status_column=Vendor.approval_status,
            active_values=("APPROVED",),
            pending_values=("PENDING",),
        )
        customers = self._aggregate_counts(
            db,
            model=Customer,
            status_column=Customer.status,
            active_values=("ACTIVE",),
            pending_values=("PENDING",),
        )
        admins = self._aggregate_admin_counts(db)
        users = MetricCounts(
            total=users_table.total + customers.total + vendors.total + admins.total,
            active=users_table.active + customers.active + vendors.active + admins.active,
            pending=users_table.pending + customers.pending + vendors.pending + admins.pending,
        )
        events = self._aggregate_counts(
            db,
            model=Event,
            status_column=Event.status,
            active_values=("ACTIVE",),
            pending_values=("PENDING",),
        )
        package_orders = self._aggregate_counts(
            db,
            model=PackageExecutionRequest,
            status_column=PackageExecutionRequest.status,
            active_values=("COMPLETED",),
            pending_values=("CREATED",),
        )

        return {
            "users": users,
            "usersTable": users_table,
            "vendors": vendors,
            "events": events,
            "packageOrders": package_orders,
            "generatedAt": now_utc(),
        }

    @staticmethod
    def _aggregate_counts(
        db: Session,
        *,
        model,
        status_column,
        active_values: tuple[str, ...],
        pending_values: tuple[str, ...],
    ) -> MetricCounts:
        total, active, pending = (
            db.query(
                func.count(model.id),
                func.sum(case((status_column.in_(active_values), 1), else_=0)),
                func.sum(case((status_column.in_(pending_values), 1), else_=0)),
            )
            .one()
        )
        return MetricCounts(
            total=int(total or 0),
            active=int(active or 0),
            pending=int(pending or 0),
        )

    @staticmethod
    def _aggregate_admin_counts(db: Session) -> MetricCounts:
        total = int(db.query(func.count(Admin.id)).scalar() or 0)
        return MetricCounts(total=total, active=total, pending=0)


admin_dashboard_aggregator = AdminDashboardAggregator()
