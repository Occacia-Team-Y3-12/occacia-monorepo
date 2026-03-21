# ruff: noqa: S101

from types import SimpleNamespace
from unittest.mock import MagicMock

from app.services.customer_service import CustomerService


def test_update_customer_profile_updates_fields_and_persists():
    service = CustomerService()
    db = MagicMock()
    customer = SimpleNamespace(
        full_name="Initial Name",
        phone="+94000000000",
        locale="en",
    )

    updated_customer = service.update_customer_profile(
        db,
        customer,
        full_name="Updated Name",
        phone="+94112223344",
        locale="en-LK",
    )

    assert updated_customer is customer
    assert customer.full_name == "Updated Name"
    assert customer.phone == "+94112223344"
    assert customer.locale == "en-LK"
    db.add.assert_called_once_with(customer)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(customer)


def test_get_event_persona_ids_returns_empty_mapping_when_no_event_ids():
    service = CustomerService()
    db = MagicMock()

    persona_ids_by_event = service.get_event_persona_ids(db, event_ids=[])

    assert persona_ids_by_event == {}
    db.query.assert_not_called()


def test_get_event_persona_ids_groups_links_by_event_id():
    service = CustomerService()
    db = MagicMock()
    query = db.query.return_value
    filtered_query = query.filter.return_value
    filtered_query.all.return_value = [
        SimpleNamespace(event_id="EVT-001", persona_id="PER-001"),
        SimpleNamespace(event_id="EVT-001", persona_id="PER-002"),
        SimpleNamespace(event_id="EVT-002", persona_id="PER-003"),
    ]

    persona_ids_by_event = service.get_event_persona_ids(
        db,
        event_ids=["EVT-001", "EVT-002"],
    )

    assert persona_ids_by_event == {
        "EVT-001": ["PER-001", "PER-002"],
        "EVT-002": ["PER-003"],
    }


def test_list_event_templates_returns_uc09_quick_start_templates():
    service = CustomerService()

    templates = service.list_event_templates()

    assert templates == ["Birthday", "Family Gathering", "Shopping"]


# UC-29: Manage Customers - Admin Service Unit Tests

def test_admin_list_customers_no_filter():
    from app.services.admin_service import AdminService
    service = AdminService()
    db = MagicMock()
    query = db.query.return_value
    query.order_by.return_value.limit.return_value.all.return_value = [
        SimpleNamespace(id=1, customer_id="CUS-001", email="c1@test.com", full_name="C1", status="ACTIVE"),
        SimpleNamespace(id=2, customer_id="CUS-002", email="c2@test.com", full_name="C2", status="PENDING"),
    ]
    
    customers, next_cursor = service.list_customers(db, status=None, limit=20, cursor=None)
    
    assert len(customers) == 2
    assert next_cursor is None
    db.query.assert_called_once()


def test_admin_list_customers_with_status_filter():
    from app.services.admin_service import AdminService
    service = AdminService()
    db = MagicMock()
    query = db.query.return_value
    filtered_query = query.filter.return_value
    filtered_query.order_by.return_value.limit.return_value.all.return_value = [
        SimpleNamespace(id=1, customer_id="CUS-001", email="c1@test.com", full_name="C1", status="ACTIVE"),
    ]
    
    customers, next_cursor = service.list_customers(db, status="ACTIVE", limit=20, cursor=None)
    
    assert len(customers) == 1
    query.filter.assert_called_once()


def test_admin_get_customer_success():
    from app.services.admin_service import AdminService
    service = AdminService()
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = SimpleNamespace(
        customer_id="CUS-001", email="c@test.com", full_name="Customer", status="ACTIVE"
    )
    
    customer = service.get_customer(db, "CUS-001")
    
    assert customer.customer_id == "CUS-001"
    assert customer.email == "c@test.com"


def test_admin_get_customer_not_found():
    from app.services.admin_service import AdminService
    from fastapi import HTTPException
    import pytest
    
    service = AdminService()
    db = MagicMock()
    query = db.query.return_value
    query.filter.return_value.first.return_value = None
    
    with pytest.raises(HTTPException) as exc_info:
        service.get_customer(db, "CUS-NOTFOUND")
    
    assert exc_info.value.status_code == 404
    assert "not found" in exc_info.value.detail.lower()


def test_admin_update_customer_status_to_active():
    from app.services.admin_service import AdminService
    service = AdminService()
    db = MagicMock()
    customer = SimpleNamespace(customer_id="CUS-001", status="PENDING")
    query = db.query.return_value
    query.filter.return_value.first.return_value = customer
    
    updated = service.update_customer_status(db, "CUS-001", "ACTIVE", "admin@test.com")
    
    assert updated.status == "ACTIVE"
    db.commit.assert_called_once()
    db.refresh.assert_called_once()


def test_admin_update_customer_status_invalid_status():
    from app.services.admin_service import AdminService
    from fastapi import HTTPException
    import pytest
    
    service = AdminService()
    db = MagicMock()
    
    with pytest.raises(HTTPException) as exc_info:
        service.update_customer_status(db, "CUS-001", "INVALID", "admin@test.com")
    
    assert exc_info.value.status_code == 400
    assert "status must be" in exc_info.value.detail
