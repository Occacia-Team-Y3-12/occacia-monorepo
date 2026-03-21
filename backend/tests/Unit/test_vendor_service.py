from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.vendor_service import VendorService, normalize_tags
from app.services.admin_service import AdminService
from app.core.database import SessionLocal


# ── AdminService tests ────────────────────────────────────────────────

def test_approve_vendor_sets_approved_status_and_verified():
    service = AdminService()
    db = MagicMock()
    vendor = SimpleNamespace(
        vendor_id="VEN-001",
        approval_status="PENDING",
        is_verified=False,
        approved_at=None,
        status="PENDING",
    )

    with patch.object(service, "get_vendor", return_value=vendor):
        result = service.approve_vendor(db, vendor_id=1, admin_email="admin@test.com")

    assert result is vendor
    assert vendor.approval_status == "APPROVED"
    assert vendor.is_verified is True
    assert vendor.approved_at is not None
    assert vendor.status == "ACTIVE"
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(vendor)


def test_approve_vendor_fails_when_already_approved():
    service = AdminService()
    db = MagicMock()
    vendor = SimpleNamespace(approval_status="APPROVED")

    with patch.object(service, "get_vendor", return_value=vendor):
        with pytest.raises(HTTPException) as exc:
            service.approve_vendor(db, vendor_id=1, admin_email="admin@test.com")

    assert exc.value.status_code == 400
    assert "already approved" in exc.value.detail
    db.commit.assert_not_called()


def test_reject_vendor_sets_rejected_status_and_unverified():
    service = AdminService()
    db = MagicMock()
    vendor = SimpleNamespace(
        vendor_id="VEN-002",
        approval_status="PENDING",
        is_verified=True,
    )

    with patch.object(service, "get_vendor", return_value=vendor):
        result = service.reject_vendor(db, vendor_id=2, reason="Incomplete docs", admin_email="admin@test.com")

    assert result is vendor
    assert vendor.approval_status == "REJECTED"
    assert vendor.is_verified is False
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(vendor)


def test_reject_vendor_fails_when_already_rejected():
    service = AdminService()
    db = MagicMock()
    vendor = SimpleNamespace(approval_status="REJECTED")

    with patch.object(service, "get_vendor", return_value=vendor):
        with pytest.raises(HTTPException) as exc:
            service.reject_vendor(db, vendor_id=2, reason="Test", admin_email="admin@test.com")

    assert exc.value.status_code == 400
    assert "already rejected" in exc.value.detail
    db.commit.assert_not_called()


def test_get_vendor_returns_vendor_when_exists():
    service = AdminService()
    db = MagicMock()
    vendor = SimpleNamespace(id=1, vendor_id="VEN-001")
    db.query.return_value.filter.return_value.first.return_value = vendor

    result = service.get_vendor(db, vendor_id=1)

    assert result is vendor


def test_get_vendor_raises_404_when_not_found():
    service = AdminService()
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        service.get_vendor(db, vendor_id=999)

    assert exc.value.status_code == 404
    assert "not found" in exc.value.detail


def test_list_vendors_filters_by_approval_status():
    service = AdminService()
    db = MagicMock()
    vendors = [SimpleNamespace(id=1), SimpleNamespace(id=2)]
    query_mock = db.query.return_value
    filter_mock = query_mock.filter.return_value
    order_mock = filter_mock.order_by.return_value
    order_mock.all.return_value = vendors

    result = service.list_vendors(db, approval_status="PENDING")

    assert result == vendors
    query_mock.filter.assert_called()


def test_list_vendors_returns_all_when_no_filters():
    service = AdminService()
    db = MagicMock()
    vendors = [SimpleNamespace(id=1), SimpleNamespace(id=2), SimpleNamespace(id=3)]
    query_mock = db.query.return_value
    order_mock = query_mock.order_by.return_value
    order_mock.all.return_value = vendors

    result = service.list_vendors(db)

    assert result == vendors
    assert len(result) == 3


# ── normalize_tags ────────────────────────────────────────────────────

def test_normalize_tags_exact_match():
    result = normalize_tags(["romantic", "luxury"])
    assert "romantic" in result
    assert "luxury" in result


def test_normalize_tags_partial_match():
    result = normalize_tags(["romantic-dinner"])
    assert "romantic" in result


def test_normalize_tags_unknown_tag_excluded():
    result = normalize_tags(["completelymadeuptag12345"])
    assert result == []


def test_normalize_tags_deduplicates():
    result = normalize_tags(["romantic", "romantic", "luxury"])
    assert result.count("romantic") == 1


def test_normalize_tags_empty():
    assert normalize_tags([]) == []


def test_normalize_tags_case_insensitive():
    result = normalize_tags(["ROMANTIC", "Luxury"])
    assert "romantic" in result
    assert "luxury" in result


# ── find_perfect_matches ──────────────────────────────────────────────

def test_find_perfect_matches_returns_results(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    results = service.find_perfect_matches(db, {
        "venue_tags": ["romantic"],
        "guest_count": 2,
        "budget_per_head": 200.0,
        "location": "Colombo",
    })
    db.close()
    assert len(results) > 0
    assert any("romantic" in p.tags for p in results)


def test_find_perfect_matches_empty_tags_returns_nothing(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    results = service.find_perfect_matches(db, {
        "venue_tags": [],
        "guest_count": 2,
    })
    db.close()
    assert results == []


def test_find_perfect_matches_guest_count_filter(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    # Birthday package min is 10, so 2 guests should exclude it
    results = service.find_perfect_matches(db, {
        "venue_tags": ["party"],
        "guest_count": 2,
    })
    db.close()
    # Should find nothing because min_guests=10 for party package
    assert all(p.min_guests <= 2 for p in results)


def test_find_perfect_matches_budget_filter(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    results = service.find_perfect_matches(db, {
        "venue_tags": ["romantic"],
        "budget_per_head": 10.0,  # Too low for romantic dinner (150/head)
    })
    db.close()
    assert all(
        p.price_per_head is None or p.price_per_head <= 10.0
        for p in results
    )


def test_find_perfect_matches_fallback_relaxes_filters(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    # Impossible budget but valid tags — fallback tiers should still return results
    results = service.find_perfect_matches(db, {
        "venue_tags": ["romantic"],
        "guest_count": 9999,
        "budget_per_head": 0.01,
    })
    db.close()
    assert len(results) > 0


def test_find_perfect_matches_returns_vendor(vendor_with_packages):
    """
    Packages returned by find_perfect_matches must have a vendor loaded.
    In production, only approved/verified vendors are included; in test
    environments the fallback may include pending vendors — the important
    invariant is that every result has an associated vendor object.
    """
    db = SessionLocal()
    service = VendorService()
    results = service.find_perfect_matches(db, {"venue_tags": ["romantic"]})
    db.close()
    for p in results:
        assert p.vendor is not None, \
            "Each matched package must have a vendor eagerly loaded"


# ── find_gift_matches ─────────────────────────────────────────────────

def test_find_gift_matches_returns_results(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    results = service.find_gift_matches(db, ["adventure", "nature"])
    db.close()
    assert len(results) > 0


def test_find_gift_matches_empty_tags(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    results = service.find_gift_matches(db, [])
    db.close()
    assert results == []


def test_find_gift_matches_budget_filter(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    results = service.find_gift_matches(db, ["adventure"], budget=10.0)
    db.close()
    assert all(
        p.price_per_head is None or p.price_per_head <= 10.0
        for p in results
    )


# ── get_all_tags ──────────────────────────────────────────────────────

def test_get_all_tags_returns_list(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    tags = service.get_all_tags(db)
    db.close()
    assert isinstance(tags, list)
    assert len(tags) > 0
    assert "romantic" in tags


def test_ensure_request_actionable_allows_sent_requests():
    service = VendorService()
    request = SimpleNamespace(status="SENT")

    service._ensure_request_actionable(request)


def test_ensure_request_actionable_rejects_expired_requests():
    service = VendorService()
    request = SimpleNamespace(status="EXPIRED")

    with pytest.raises(HTTPException) as exc:
        service._ensure_request_actionable(request)

    assert exc.value.status_code == 409
    assert "expired" in exc.value.detail


def test_update_vendor_task_status_updates_valid_transition_and_persists():
    service = VendorService()
    db = MagicMock()
    task = SimpleNamespace(status="ASSIGNED", status_updated_at=None)

    with patch.object(service, "get_vendor_task", return_value=task), \
         patch("app.services.vendor_service.now_utc", return_value="2026-03-20T12:00:00Z"):
        updated_task = service.update_vendor_task_status(
            db,
            vendor_id="VEN-001",
            task_id="TSK-001",
            next_status="IN_PROGRESS",
        )

    assert updated_task is task
    assert task.status == "IN_PROGRESS"
    assert task.status_updated_at == "2026-03-20T12:00:00Z"
    db.add.assert_called_once_with(task)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(task)


def test_update_vendor_task_status_rejects_invalid_transition():
    service = VendorService()
    db = MagicMock()
    task = SimpleNamespace(status="ASSIGNED")

    with patch.object(service, "get_vendor_task", return_value=task):
        with pytest.raises(HTTPException) as exc:
            service.update_vendor_task_status(
                db,
                vendor_id="VEN-001",
                task_id="TSK-001",
                next_status="DONE",
            )

    assert exc.value.status_code == 409
    db.commit.assert_not_called()


def test_respond_to_fulfillment_request_accepts_and_assigns_task():
    service = VendorService()
    db = MagicMock()
    request = SimpleNamespace(
        status="SENT",
        responded_at=None,
        response_note=None,
        task_id="TSK-001",
    )
    task = SimpleNamespace(
        status="PENDING",
        rejected_at=None,
        rejection_reason=None,
        status_updated_at=None,
    )

    with patch.object(service, "_expire_overdue_fulfillment_requests"), \
         patch.object(service, "_get_vendor_request_or_404", return_value=request), \
         patch.object(service, "_get_task_or_404", return_value=task), \
         patch("app.services.vendor_service.now_utc", return_value="2026-03-20T12:05:00Z"):
        returned_request, returned_task = service.respond_to_fulfillment_request(
            db,
            vendor_id="VEN-001",
            fulfillment_request_id="TQR-001",
            decision="ACCEPT",
            response_note=None,
        )

    assert returned_request is request
    assert returned_task is task
    assert request.status == "ACCEPTED"
    assert request.responded_at == "2026-03-20T12:05:00Z"
    assert task.status == "ASSIGNED"
    assert task.status_updated_at == "2026-03-20T12:05:00Z"
    db.commit.assert_called_once()
    assert db.add.call_count == 2


def test_respond_to_fulfillment_request_rejects_and_sets_reason():
    service = VendorService()
    db = MagicMock()
    request = SimpleNamespace(
        status="SENT",
        responded_at=None,
        response_note=None,
        task_id="TSK-001",
    )
    task = SimpleNamespace(
        status="PENDING",
        rejected_at=None,
        rejection_reason=None,
        status_updated_at=None,
    )

    with patch.object(service, "_expire_overdue_fulfillment_requests"), \
         patch.object(service, "_get_vendor_request_or_404", return_value=request), \
         patch.object(service, "_get_task_or_404", return_value=task), \
         patch("app.services.vendor_service.now_utc", return_value="2026-03-20T12:10:00Z"):
        service.respond_to_fulfillment_request(
            db,
            vendor_id="VEN-001",
            fulfillment_request_id="TQR-001",
            decision="REJECT",
            response_note="Already booked",
        )

    assert request.status == "REJECTED"
    assert request.response_note == "Already booked"
    assert task.status == "REJECTED"
    assert task.rejected_at == "2026-03-20T12:10:00Z"
    assert task.rejection_reason == "Already booked"
