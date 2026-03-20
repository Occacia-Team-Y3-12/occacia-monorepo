from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.schemas.recommendation_schema import TaskRecommendationResponse
from app.services.recommendation_service import RankedOffering, RecommendationService, event_planning_service


def _ranked(offering_id: str, *, price: float, rank: int, score: float = 0.0, currency: str = "LKR"):
    return RankedOffering(
        offering=SimpleNamespace(
            offering_id=offering_id,
            price=price,
            currency=currency,
        ),
        score=score,
        rank=rank,
    )


def test_select_ranked_offering_budget_uses_lowest_price():
    service = RecommendationService()
    ranked = [
        _ranked("OFF-3", price=300.0, rank=3),
        _ranked("OFF-1", price=100.0, rank=1),
        _ranked("OFF-2", price=200.0, rank=2),
    ]

    selected = service._select_ranked_offering("BUDGET", ranked)

    assert selected.offering.offering_id == "OFF-1"


def test_select_ranked_offering_recommended_uses_top_ai_rank():
    service = RecommendationService()
    ranked = [
        _ranked("OFF-2", price=150.0, rank=2, score=8.0),
        _ranked("OFF-1", price=250.0, rank=1, score=5.0),
        _ranked("OFF-3", price=120.0, rank=3, score=9.0),
    ]

    selected = service._select_ranked_offering("RECOMMENDED", ranked)

    assert selected.offering.offering_id == "OFF-1"


def test_select_ranked_offering_high_quality_uses_highest_price():
    service = RecommendationService()
    ranked = [
        _ranked("OFF-1", price=100.0, rank=1),
        _ranked("OFF-3", price=500.0, rank=3),
        _ranked("OFF-2", price=250.0, rank=2),
    ]

    selected = service._select_ranked_offering("HIGH_QUALITY", ranked)

    assert selected.offering.offering_id == "OFF-3"


def test_resolve_currency_accepts_matching_task_and_offering_currency():
    service = RecommendationService()
    tasks = [SimpleNamespace(currency="LKR"), SimpleNamespace(currency="LKR")]
    ranked_by_task = {
        "TSK-1": [_ranked("OFF-1", price=100.0, rank=1, currency="LKR")],
        "TSK-2": [_ranked("OFF-2", price=150.0, rank=1, currency="LKR")],
    }

    currency = service._resolve_currency(tasks, ranked_by_task)

    assert currency == "LKR"


def test_resolve_currency_rejects_mismatched_currency():
    service = RecommendationService()
    tasks = [SimpleNamespace(currency="USD")]
    ranked_by_task = {
        "TSK-1": [_ranked("OFF-1", price=100.0, rank=1, currency="LKR")],
    }

    with pytest.raises(HTTPException) as exc:
        service._resolve_currency(tasks, ranked_by_task)

    assert exc.value.status_code == 400
    assert exc.value.detail == "Task and offering currencies must match"


def test_ensure_aware_datetime_adds_utc_when_naive():
    service = RecommendationService()
    naive = datetime(2026, 8, 1, 18, 0, 0)

    aware = service._ensure_aware_datetime(naive)

    assert aware.tzinfo == timezone.utc


def test_ensure_aware_datetime_preserves_existing_timezone():
    service = RecommendationService()
    aware = datetime.now(timezone.utc) + timedelta(minutes=5)

    normalized = service._ensure_aware_datetime(aware)

    assert normalized == aware


def test_get_task_recommendations_returns_shortlist_items_for_task():
    service = RecommendationService()
    db = MagicMock()
    query = db.query.return_value
    filtered_query = query.filter.return_value
    filtered_query.first.return_value = SimpleNamespace(task_id="TSK-001", event_id="EVT-001")
    event_planning_service.get_event_for_customer = MagicMock()
    service._get_task_recommendations_for_tasks = MagicMock(
        return_value={
            "TSK-001": [
                TaskRecommendationResponse(
                    recommendationId="REC-001",
                    eventId="EVT-001",
                    taskId="TSK-001",
                    offeringId="OFF-001",
                    score=9.0,
                    rank=1,
                    generatedAt=datetime.now(timezone.utc),
                ),
                TaskRecommendationResponse(
                    recommendationId="REC-002",
                    eventId="EVT-001",
                    taskId="TSK-001",
                    offeringId="OFF-002",
                    score=8.0,
                    rank=2,
                    generatedAt=datetime.now(timezone.utc),
                ),
            ]
        }
    )

    response = service.get_task_recommendations(
        db,
        customer_id="CUS-001",
        event_id="EVT-001",
        task_id="TSK-001",
    )

    assert len(response.items) == 2
    assert response.items[0].offering_id == "OFF-001"
    assert response.items[1].rank == 2


def test_create_custom_package_rejects_customized_base_package():
    service = RecommendationService()
    db = MagicMock()
    event_planning_service.get_event_for_customer = MagicMock()
    service._get_package_or_404 = MagicMock(
        return_value=SimpleNamespace(
            package_id="PKG-BASE",
            event_id="EVT-001",
            is_customized=True,
            currency="LKR",
            expires_at=None,
        )
    )

    with pytest.raises(HTTPException) as exc:
        service.create_custom_package(
            db,
            customer_id="CUS-001",
            event_id="EVT-001",
            request=SimpleNamespace(base_package_id="PKG-BASE", items=[SimpleNamespace()]),
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Base package must be system generated"


def test_replace_package_items_rejects_offering_outside_shortlist():
    service = RecommendationService()
    db = MagicMock()
    service._get_package_items = MagicMock(
        return_value=[
            SimpleNamespace(task_id="TSK-001", quantity=1),
        ]
    )
    service._get_task_recommendations_for_tasks = MagicMock(
        return_value={
            "TSK-001": [
                SimpleNamespace(offering_id="OFF-001"),
                SimpleNamespace(offering_id="OFF-002"),
            ]
        }
    )

    with pytest.raises(HTTPException) as exc:
        service._replace_package_items(
            db,
            event_id="EVT-001",
            package=SimpleNamespace(package_id="PKG-CUSTOM"),
            base_package=SimpleNamespace(package_id="PKG-BASE", currency="LKR"),
            requested_items=[SimpleNamespace(task_id="TSK-001", offering_id="OFF-999", quantity=1)],
        )

    assert exc.value.status_code == 400
    assert exc.value.detail == "Offering OFF-999 is not in the shortlist for task TSK-001"


def test_replace_package_items_recalculates_total_and_persists_rows():
    service = RecommendationService()
    db = MagicMock()
    package = SimpleNamespace(
        package_id="PKG-CUSTOM",
        package_total_price=0.0,
        currency="LKR",
        base_package_id=None,
        is_customized=False,
    )
    base_package = SimpleNamespace(package_id="PKG-BASE", currency="LKR")
    service._get_package_items = MagicMock(
        return_value=[
            SimpleNamespace(task_id="TSK-001", quantity=1),
            SimpleNamespace(task_id="TSK-002", quantity=2),
        ]
    )
    service._get_task_recommendations_for_tasks = MagicMock(
        return_value={
            "TSK-001": [SimpleNamespace(offering_id="OFF-001")],
            "TSK-002": [SimpleNamespace(offering_id="OFF-002")],
        }
    )

    offering_one = SimpleNamespace(
        offering_id="OFF-001",
        price=1200.0,
        currency="LKR",
        is_active=True,
        is_available=True,
    )
    offering_two = SimpleNamespace(
        offering_id="OFF-002",
        price=900.0,
        currency="LKR",
        is_active=True,
        is_available=True,
    )
    db.query.return_value.filter.return_value.all.return_value = [offering_one, offering_two]

    service._replace_package_items(
        db,
        event_id="EVT-001",
        package=package,
        base_package=base_package,
        requested_items=[
            SimpleNamespace(task_id="TSK-001", offering_id="OFF-001", quantity=1),
            SimpleNamespace(task_id="TSK-002", offering_id="OFF-002", quantity=None),
        ],
    )

    assert package.package_total_price == 3000.0
    assert package.currency == "LKR"
    assert package.base_package_id == "PKG-BASE"
    assert package.is_customized is True
    assert db.add.call_count >= 3
    db.flush.assert_called_once()
