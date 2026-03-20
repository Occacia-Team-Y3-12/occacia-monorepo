from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException

from app.services.vendor_service import VendorService, normalize_tags
from app.core.database import SessionLocal


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
    # Impossible guest count but valid tags — fallback should still return results
    results = service.find_perfect_matches(db, {
        "venue_tags": ["romantic"],
        "guest_count": 9999,
        "budget_per_head": 0.01,
    })
    db.close()
    assert len(results) > 0


def test_find_perfect_matches_only_verified_vendors(vendor_with_packages):
    db = SessionLocal()
    service = VendorService()
    results = service.find_perfect_matches(db, {"venue_tags": ["romantic"]})
    db.close()
    assert all(p.vendor.is_verified for p in results)


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
