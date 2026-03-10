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
