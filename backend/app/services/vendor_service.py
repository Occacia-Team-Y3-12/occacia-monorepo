from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.marketplace import Vendor, Package

class VendorService:
    def find_perfect_matches(self, db: Session, analysis: dict):
        """
        Takes the AI dictionary and queries the database.
        ✅ FIXED: Uses .get() to safely handle dictionaries (No more AttributeErrors)
        """
        
        print(f"🕵️ Vendor Service analyzing: {analysis}")

        # 1. SAFETY CHECK: Ensure analysis is a dictionary
        if not analysis or not isinstance(analysis, dict):
            print("⚠️ Analysis is empty or invalid. Returning empty list.")
            return []

        # 2. CHECK FOR FAILURE FLAGS
        # We use .get("key", default) to prevent crashes if the key is missing
        missing_info = analysis.get("missing_info", [])
        if "SERVICE_UNAVAILABLE" in missing_info:
            return []

        # 3. EXTRACT CRITERIA (Safely)
        # Handles both "location" (from AI) and "Any" (from fallback)
        loc = analysis.get("location")
        if loc == "Any": loc = None
        
        budget = analysis.get("budget")
        if budget == "Any": budget = None

        tags = analysis.get("tags", [])
        if isinstance(tags, str): tags = [tags] # Handle single string case

        # 4. BUILD QUERY
        query = db.query(Package).join(Vendor)

        # -- Filter by Location --
        if loc:
            query = query.filter(Vendor.location_base.ilike(f"%{loc}%"))

        # -- Filter by Budget --
        if budget == "Cheap":
            query = query.filter(Package.price < 3000)
        elif budget == "Moderate":
            query = query.filter(Package.price.between(3000, 10000))
        elif budget == "Luxury":
            query = query.filter(Package.price > 10000)

        # -- Filter by Vibe/Tags (Simple Keyword Search) --
        # If we have tags, try to find packages that match at least one
        if tags:
            # This creates a dynamic OR filter for tags
            tag_filters = [Package.tags.contains([t]) for t in tags]
            if tag_filters:
                query = query.filter(or_(*tag_filters))

        results = query.limit(5).all()
        print(f"✅ Found {len(results)} matches in DB.")
        return results

vendor_service = VendorService()