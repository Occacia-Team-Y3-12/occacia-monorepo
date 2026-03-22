# ruff: noqa: S101

from unittest.mock import MagicMock

from app.services.admin_dashboard_service import AdminDashboardAggregator


def test_get_dashboard_metrics_maps_totals_and_status_counts():
    db = MagicMock()
    users_query = MagicMock()
    users_query.one.return_value = (10, 7, 2)
    vendors_query = MagicMock()
    vendors_query.one.return_value = (8, 5, 2)
    customers_query = MagicMock()
    customers_query.one.return_value = (4, 3, 1)
    admins_query = MagicMock()
    admins_query.scalar.return_value = 2
    events_query = MagicMock()
    events_query.one.return_value = (6, 4, 1)
    package_orders_query = MagicMock()
    package_orders_query.one.return_value = (12, 3, 5)

    db.query.side_effect = [
        users_query,
        vendors_query,
        customers_query,
        admins_query,
        events_query,
        package_orders_query,
    ]

    service = AdminDashboardAggregator()
    payload = service.get_dashboard_metrics(db)

    assert payload["users"].total == 24
    assert payload["users"].active == 17
    assert payload["users"].pending == 5
    assert payload["usersTable"].total == 10
    assert payload["usersTable"].active == 7
    assert payload["usersTable"].pending == 2

    assert payload["vendors"].total == 8
    assert payload["vendors"].active == 5
    assert payload["vendors"].pending == 2

    assert payload["events"].total == 6
    assert payload["events"].active == 4
    assert payload["events"].pending == 1

    assert payload["packageOrders"].total == 12
    assert payload["packageOrders"].active == 3
    assert payload["packageOrders"].pending == 5
    assert payload["generatedAt"] is not None
