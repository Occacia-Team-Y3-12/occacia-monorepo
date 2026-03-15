from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.services.recommendation_service import RankedOffering, RecommendationService


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
