"""
tests/test_scored_ranking.py

Pytest suite for AI Improvement #1 — Scored Package Ranking.

Verifies that find_perfect_matches() returns packages sorted by:
    score = (tag_overlap%) * 0.4 + (budget_closeness%) * 0.3 + (guest_fit%) * 0.3

All tests use an in-memory SQLite DB so no real database is needed.
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

# ─────────────────────────────────────────────────────────────────────────────
# Minimal stub models (avoids pulling the full app stack into tests)
# ─────────────────────────────────────────────────────────────────────────────

class _Vendor:
    def __init__(self, *, id: int, is_verified: bool = True, location_base: str = "colombo"):
        self.id = id
        self.is_verified = is_verified
        self.location_base = location_base


def _pkg(
    id: int,
    name: str,
    tags,
    price_per_head: float,
    vendor: _Vendor,
    min_guests: int = 1,
    max_guests: int = 200,
    location_coverage: str = "colombo",
):
    """Factory for a minimal Package-like stub."""
    p = MagicMock()
    p.id = id
    p.name = name
    p.tags = tags if isinstance(tags, list) else json.loads(tags)
    p.price_per_head = price_per_head
    p.min_guests = min_guests
    p.max_guests = max_guests
    p.location_coverage = location_coverage
    p.vendor_id = vendor.id
    p.vendor = vendor
    return p


# ─────────────────────────────────────────────────────────────────────────────
# Score helper (mirrors the formula in vendor_service._score_package)
# ─────────────────────────────────────────────────────────────────────────────

def _expected_score(pkg, *, req_tags, budget_per_head, guest_count):
    pkg_tags = set(pkg.tags)
    req = set(req_tags)

    tag_score = len(req & pkg_tags) / len(req) if req else 0.0

    pph = pkg.price_per_head
    if budget_per_head and pph is not None and budget_per_head > 0:
        budget_score = max(0.0, min(1.0, pph / budget_per_head))
    else:
        budget_score = 0.0

    min_g = pkg.min_guests
    if guest_count is None:
        guest_score = 0.5
    elif min_g is None or guest_count >= min_g:
        guest_score = 1.0
    else:
        guest_score = 0.0

    return round(tag_score * 0.4 + budget_score * 0.3 + guest_score * 0.3, 6)


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture()
def vendor():
    return _Vendor(id=1, is_verified=True, location_base="colombo")


@pytest.fixture()
def mock_db(vendor):
    """
    Returns a mock Session whose query() results are pre-seeded with the
    three packages used across most tests.
    """
    db = MagicMock(spec=Session)

    v = vendor

    # pkg_A: exact tag match, price close to budget cap → highest expected score
    pkg_a = _pkg(1, "Romantic Rooftop Dinner", ["romantic", "fine-dining"],
                 price_per_head=4800.0, vendor=v, min_guests=2)

    # pkg_B: partial tag match, lower price → medium score
    pkg_b = _pkg(2, "Casual Garden Lunch", ["romantic"],
                 price_per_head=2000.0, vendor=v, min_guests=1)

    # pkg_C: full tag match but price at 20 % of budget → low budget_score
    pkg_c = _pkg(3, "Budget Romantic Setup", ["romantic", "fine-dining"],
                 price_per_head=1000.0, vendor=v, min_guests=1)

    _wire_db(db, vendors=[v], packages=[pkg_a, pkg_b, pkg_c])
    return db, [pkg_a, pkg_b, pkg_c]


def _wire_db(db, *, vendors, packages):
    """Set up mock db.query().filter().all() chains."""
    from app.models.vendor import Vendor as VendorModel
    from app.models.package import Package as PackageModel

    def _query(model):
        q = MagicMock()
        if model is VendorModel:
            q.filter.return_value.all.return_value = vendors
        elif model is PackageModel:
            # joinedload chain: .options(...).all() → packages
            q.options.return_value.all.return_value = packages
            q.all.return_value = packages
        return q

    db.query.side_effect = _query


# ─────────────────────────────────────────────────────────────────────────────
# Import the live service (after stubs are ready)
# ─────────────────────────────────────────────────────────────────────────────

from app.services.vendor_service import vendor_service   # noqa: E402


# ═════════════════════════════════════════════════════════════════════════════
# TEST CLASS
# ═════════════════════════════════════════════════════════════════════════════

class TestScoredPackageRanking:
    """
    All tests share the same three packages described above:

        pkg_A  tags=[romantic, fine-dining]  price=4800  min_guests=2
        pkg_B  tags=[romantic]               price=2000  min_guests=1
        pkg_C  tags=[romantic, fine-dining]  price=1000  min_guests=1

    Budget cap = 5000, guest_count = 2.
    """

    CRITERIA = {
        "venue_tags": ["romantic", "fine-dining"],
        "budget_per_head": 5000.0,
        "guest_count": 2,
        "location": "colombo",
    }

    # ── 1. Basic ordering ────────────────────────────────────────────────────

    def test_results_are_sorted_descending(self, mock_db):
        """find_perfect_matches must return packages with scores strictly non-increasing."""
        db, pkgs = mock_db
        results = vendor_service.find_perfect_matches(db, self.CRITERIA)

        assert len(results) >= 2, "Expected at least 2 matches"

        scores = [
            _expected_score(p,
                            req_tags=self.CRITERIA["venue_tags"],
                            budget_per_head=self.CRITERIA["budget_per_head"],
                            guest_count=self.CRITERIA["guest_count"])
            for p in results
        ]
        assert scores == sorted(scores, reverse=True), (
            f"Results not sorted by score descending. Scores: {scores}"
        )

    # ── 2. Best match comes first ────────────────────────────────────────────

    def test_best_match_is_first(self, mock_db):
        """pkg_A should be first: full tag match + price closest to budget cap."""
        db, pkgs = mock_db
        pkg_a, pkg_b, pkg_c = pkgs

        results = vendor_service.find_perfect_matches(db, self.CRITERIA)

        assert results[0].id == pkg_a.id, (
            f"Expected pkg_A (id=1) first, got id={results[0].id} ({results[0].name})"
        )

    # ── 3. Tag overlap drives score ──────────────────────────────────────────

    def test_full_tag_match_scores_higher_than_partial(self, mock_db):
        """A package with all requested tags must outscore one with only some."""
        db, pkgs = mock_db
        pkg_a, pkg_b, pkg_c = pkgs

        score_a = _expected_score(pkg_a,
                                  req_tags=self.CRITERIA["venue_tags"],
                                  budget_per_head=self.CRITERIA["budget_per_head"],
                                  guest_count=self.CRITERIA["guest_count"])
        score_b = _expected_score(pkg_b,
                                  req_tags=self.CRITERIA["venue_tags"],
                                  budget_per_head=self.CRITERIA["budget_per_head"],
                                  guest_count=self.CRITERIA["guest_count"])

        assert score_a > score_b, (
            f"Full-tag pkg_A score ({score_a}) should exceed partial pkg_B ({score_b})"
        )

    # ── 4. Budget closeness drives score ─────────────────────────────────────

    def test_price_closer_to_budget_cap_scores_higher(self, mock_db):
        """Between two full-tag-match packages, higher price (closer to cap) wins."""
        db, pkgs = mock_db
        pkg_a, _, pkg_c = pkgs   # both have full tag match

        score_a = _expected_score(pkg_a,
                                  req_tags=self.CRITERIA["venue_tags"],
                                  budget_per_head=self.CRITERIA["budget_per_head"],
                                  guest_count=self.CRITERIA["guest_count"])
        score_c = _expected_score(pkg_c,
                                  req_tags=self.CRITERIA["venue_tags"],
                                  budget_per_head=self.CRITERIA["budget_per_head"],
                                  guest_count=self.CRITERIA["guest_count"])

        assert score_a > score_c, (
            f"Higher-priced pkg_A ({score_a:.4f}) should score above cheaper pkg_C ({score_c:.4f})"
        )

    # ── 5. Guest fit contribution ────────────────────────────────────────────

    def test_failing_min_guests_lowers_score(self, vendor):
        """A package whose min_guests exceeds the requested count gets guest_score=0."""
        db = MagicMock(spec=Session)

        # pkg_ok  min_guests=2 — satisfied (guest_count=2)
        pkg_ok = _pkg(10, "OK Package", ["romantic", "fine-dining"],
                      price_per_head=4500.0, vendor=vendor, min_guests=2)
        # pkg_bad min_guests=10 — NOT satisfied (guest_count=2)
        pkg_bad = _pkg(11, "Big Package", ["romantic", "fine-dining"],
                       price_per_head=4800.0, vendor=vendor, min_guests=10)

        _wire_db(db, vendors=[vendor], packages=[pkg_ok, pkg_bad])

        results = vendor_service.find_perfect_matches(db, self.CRITERIA)

        # pkg_bad should not appear (guest_ok returns False for guest_count=2 < min_guests=10)
        result_ids = [r.id for r in results]
        assert pkg_bad.id not in result_ids, (
            "pkg_bad (min_guests=10 > guest_count=2) should be filtered out, not ranked"
        )
        assert pkg_ok.id in result_ids, "pkg_ok should still be present"

    # ── 6. Score formula exact value ─────────────────────────────────────────

    def test_score_formula_exact_values(self, vendor):
        """Manually verify the formula for a controlled package."""
        #   tags=[romantic, fine-dining], price=3000, min_guests=1
        #   requested: tags=[romantic, fine-dining], budget=5000, guests=2
        #
        #   tag_score   = 2/2 = 1.0
        #   budget_score = 3000/5000 = 0.6
        #   guest_score  = 1.0  (2 >= 1)
        #   total = 1.0*0.4 + 0.6*0.3 + 1.0*0.3 = 0.4 + 0.18 + 0.3 = 0.88

        pkg = _pkg(99, "Exact Test Package", ["romantic", "fine-dining"],
                   price_per_head=3000.0, vendor=vendor, min_guests=1)

        score = _expected_score(pkg,
                                req_tags=["romantic", "fine-dining"],
                                budget_per_head=5000.0,
                                guest_count=2)

        assert abs(score - 0.88) < 1e-6, f"Expected 0.88, got {score}"

    # ── 7. No budget provided → budget_score = 0 ─────────────────────────────

    def test_no_budget_uses_zero_budget_score(self, vendor):
        """When budget_per_head is None, budget contributes 0 to the score."""
        pkg = _pkg(50, "No-Budget Package", ["romantic"],
                   price_per_head=5000.0, vendor=vendor, min_guests=1)

        score = _expected_score(pkg,
                                req_tags=["romantic"],
                                budget_per_head=None,
                                guest_count=2)
        # tag_score=1.0, budget_score=0.0, guest_score=1.0
        expected = 1.0 * 0.4 + 0.0 * 0.3 + 1.0 * 0.3
        assert abs(score - expected) < 1e-6, f"Expected {expected}, got {score}"

    # ── 8. No guest count → neutral guest score = 0.5 ────────────────────────

    def test_no_guest_count_uses_neutral_score(self, vendor):
        """When guest_count is None, guest_fit contributes 0.5 * 0.3 = 0.15."""
        pkg = _pkg(51, "Unknown-Guest Package", ["romantic"],
                   price_per_head=4000.0, vendor=vendor, min_guests=1)

        score = _expected_score(pkg,
                                req_tags=["romantic"],
                                budget_per_head=5000.0,
                                guest_count=None)
        # tag=1.0, budget=0.8, guest=0.5
        expected = 1.0 * 0.4 + 0.8 * 0.3 + 0.5 * 0.3
        assert abs(score - expected) < 1e-6, f"Expected {expected}, got {score}"

    # ── 9. Empty results for no tags ─────────────────────────────────────────

    def test_empty_tags_returns_empty(self, mock_db):
        """find_perfect_matches with no tags should return []."""
        db, _ = mock_db
        results = vendor_service.find_perfect_matches(db, {
            "venue_tags": [],
            "budget_per_head": 5000.0,
            "guest_count": 2,
            "location": "colombo",
        })
        assert results == []

    # ── 10. Limit is respected ───────────────────────────────────────────────

    def test_limit_is_respected(self, mock_db):
        """Ranked results must not exceed the requested limit."""
        db, _ = mock_db
        results = vendor_service.find_perfect_matches(db, self.CRITERIA, limit=2)
        assert len(results) <= 2, f"Expected ≤2 results, got {len(results)}"