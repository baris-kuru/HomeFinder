"""Decide whether a listing matches the user's search criteria."""
from __future__ import annotations

from .models import Listing


def matches(listing: Listing, f: dict) -> tuple[bool, str]:
    """Return (passes, reason). `f` is the [filters] config section."""
    if f.get("require_no_wbs", True) and listing.wbs_required:
        return False, "requires WBS"

    if f.get("exclude_senior", True) and listing.senior:
        return False, "senior / age-restricted housing"

    if listing.rooms is not None:
        if listing.rooms < f.get("min_rooms", 0):
            return False, f"rooms {listing.rooms:g} < {f['min_rooms']}"
        if "max_rooms" in f and listing.rooms > f["max_rooms"]:
            return False, f"rooms {listing.rooms:g} > {f['max_rooms']}"

    if listing.area is not None:
        if listing.area < f.get("min_area", 0):
            return False, f"area {listing.area:g} < {f['min_area']}"
        if "max_area" in f and listing.area > f["max_area"]:
            return False, f"area {listing.area:g} > {f['max_area']}"

    basis = f.get("rent_basis", "gross")
    rent = listing.rent_for(basis)
    if rent is not None and "max_rent" in f and rent > f["max_rent"]:
        return False, f"rent {rent:.0f} > {f['max_rent']} ({basis})"

    districts = [d.strip().lower() for d in f.get("districts", []) if d.strip()]
    if districts and listing.district.lower() not in districts:
        return False, f"district {listing.district!r} not in list"

    return True, "match"


def is_applyable(listing: Listing, f: dict, adapter_companies: set[str]) -> bool:
    """True if we have an auto-fill adapter AND the user enabled this company."""
    enabled = {c.strip().lower() for c in f.get("apply_companies", [])}
    return listing.company in adapter_companies and listing.company in enabled
