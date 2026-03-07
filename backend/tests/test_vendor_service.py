# import pytest
# from app.services.vendor_service import VendorService, normalize_tags
# from app.core.database import SessionLocal


# # ── normalize_tags ────────────────────────────────────────────────────

# def test_normalize_tags_exact_match():
#     result = normalize_tags(["romantic", "luxury"])
#     assert "romantic" in result
#     assert "luxury" in result


# def test_normalize_tags_partial_match():
#     result = normalize_tags(["romantic-dinner"])
#     assert "romantic" in result


# def test_normalize_tags_unknown_tag_excluded():
#     result = normalize_tags(["completelymadeuptag12345"])
#     assert result == []


# def test_normalize_tags_deduplicates():
#     result = normalize_tags(["romantic", "romantic", "luxury"])
#     assert result.count("romantic") == 1


# def test_normalize_tags_empty():
#     assert normalize_tags([]) == []


# def test_normalize_tags_case_insensitive():
#     result = normalize_tags(["ROMANTIC", "Luxury"])
#     assert "romantic" in result
#     assert "luxury" in result


# # ── find_perfect_matches ──────────────────────────────────────────────

# def test_find_perfect_matches_returns_results(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     results = service.find_perfect_matches(db, {
#         "venue_tags": ["romantic"],
#         "guest_count": 2,
#         "budget_per_head": 200.0,
#         "location": "Colombo",
#     })
#     db.close()
#     assert len(results) > 0
#     assert any("romantic" in p.tags for p in results)


# def test_find_perfect_matches_empty_tags_returns_nothing(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     results = service.find_perfect_matches(db, {
#         "venue_tags": [],
#         "guest_count": 2,
#     })
#     db.close()
#     assert results == []


# def test_find_perfect_matches_guest_count_filter(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     # Birthday package min is 10, so 2 guests should exclude it
#     results = service.find_perfect_matches(db, {
#         "venue_tags": ["party"],
#         "guest_count": 2,
#     })
#     db.close()
#     # Should find nothing because min_guests=10 for party package
#     assert all(p.min_guests <= 2 for p in results)


# def test_find_perfect_matches_budget_filter(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     results = service.find_perfect_matches(db, {
#         "venue_tags": ["romantic"],
#         "budget_per_head": 10.0,  # Too low for romantic dinner (150/head)
#     })
#     db.close()
#     assert all(
#         p.price_per_head is None or p.price_per_head <= 10.0
#         for p in results
#     )


# def test_find_perfect_matches_fallback_relaxes_filters(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     # Impossible guest count but valid tags — fallback should still return results
#     results = service.find_perfect_matches(db, {
#         "venue_tags": ["romantic"],
#         "guest_count": 9999,
#         "budget_per_head": 0.01,
#     })
#     db.close()
#     assert len(results) > 0


# def test_find_perfect_matches_only_verified_vendors(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     results = service.find_perfect_matches(db, {"venue_tags": ["romantic"]})
#     db.close()
#     assert all(p.vendor.is_verified for p in results)


# # ── find_gift_matches ─────────────────────────────────────────────────

# def test_find_gift_matches_returns_results(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     results = service.find_gift_matches(db, ["adventure", "nature"])
#     db.close()
#     assert len(results) > 0


# def test_find_gift_matches_empty_tags(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     results = service.find_gift_matches(db, [])
#     db.close()
#     assert results == []


# def test_find_gift_matches_budget_filter(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     results = service.find_gift_matches(db, ["adventure"], budget=10.0)
#     db.close()
#     assert all(
#         p.price_per_head is None or p.price_per_head <= 10.0
#         for p in results
#     )


# # ── get_all_tags ──────────────────────────────────────────────────────

# def test_get_all_tags_returns_list(vendor_with_packages):
#     db = SessionLocal()
#     service = VendorService()
#     tags = service.get_all_tags(db)
#     db.close()
#     assert isinstance(tags, list)
#     assert len(tags) > 0
#     assert "romantic" in tags