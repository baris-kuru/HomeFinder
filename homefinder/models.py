"""Listing model + parsing from inberlinwohnen's wire:snapshot JSON."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Age-restricted / senior housing signals (matched against the title).
# Catches: Seniorenwohnung, "ab 60 Jahren", "60+", "Wohnen ab 65", betreutes Wohnen.
_SENIOR_RE = re.compile(
    r"senioren?|betreutes?\s+wohnen|pflegewohn"
    r"|ab\s*(?:5[5-9]|[67]\d)\s*jahr"
    r"|\b(?:5[5-9]|[67]\d)\s*\+"
    r"|wohnen\s*ab\s*(?:5[5-9]|[67]\d)",
    re.IGNORECASE,
)


def _de_num(value) -> float | None:
    """Parse a German-formatted number: '1.060,25' -> 1060.25, '59,06' -> 59.06."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _unwrap(value):
    """The site nests payloads as [actual, {"s": "arr"}]; return the actual part."""
    if (
        isinstance(value, list)
        and len(value) == 2
        and isinstance(value[1], dict)
        and value[1].get("s") == "arr"
    ):
        return value[0]
    return value


def _detail_pairs(node, out: dict) -> None:
    """Walk the nested `details` tree collecting {label: value} pairs."""
    if isinstance(node, dict):
        if "label" in node and "value" in node and node["label"] not in out:
            out[node["label"]] = node["value"]
        for v in node.values():
            _detail_pairs(v, out)
    elif isinstance(node, list):
        for v in node:
            _detail_pairs(v, out)


@dataclass
class Listing:
    id: int
    title: str
    object_id: str
    deeplink: str
    company: str            # internal slug, e.g. "gewobag"
    company_name: str
    rooms: float | None
    area: float | None      # m²
    rent_net: float | None  # Kaltmiete
    rent_gross: float | None  # Gesamtmiete / Warmmiete
    address: str
    district: str
    occupation_date: str
    wbs_required: bool = False
    senior: bool = False
    details: dict = field(default_factory=dict)
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_snapshot(cls, item: dict) -> "Listing":
        company = _unwrap(item.get("company"))
        if isinstance(company, list):
            company = company[0] if company else {}
        comp0 = company if isinstance(company, dict) else {}

        addr = _unwrap(item.get("address")) or {}
        if isinstance(addr, list):
            addr = addr[0] if addr else {}
        street = (addr.get("street") or "").strip()
        number = (addr.get("number") or "").strip()
        zip_code = (addr.get("zipCode") or "").strip()
        district = (addr.get("district") or "").strip()
        address = ", ".join(
            p for p in [f"{street} {number}".strip(), f"{zip_code} {district}".strip()] if p
        )

        details: dict = {}
        _detail_pairs(item.get("details"), details)

        wbs_val = str(details.get("WBS", "")).lower()
        wbs_required = "erforderlich" in wbs_val and "nicht" not in wbs_val

        title = item.get("title", "") or ""
        senior = bool(_SENIOR_RE.search(title))

        return cls(
            id=int(item["id"]),
            title=title,
            object_id=item.get("objectId", ""),
            deeplink=item.get("deeplink", ""),
            company=(comp0.get("intern") or "").strip().lower(),
            company_name=(comp0.get("name") or "").strip(),
            rooms=_de_num(item.get("rooms")),
            area=_de_num(item.get("area")),
            rent_net=_de_num(item.get("rentNet")),
            rent_gross=_de_num(item.get("rentGross")),
            address=address or title,
            district=district,
            occupation_date=item.get("occupationDate", "") or "",
            wbs_required=wbs_required,
            senior=senior,
            details=details,
            raw=item,
        )

    def rent_for(self, basis: str) -> float | None:
        return self.rent_net if basis == "net" else self.rent_gross

    def summary(self) -> str:
        parts = []
        if self.rooms is not None:
            parts.append(f"{self.rooms:g} Zi")
        if self.area is not None:
            parts.append(f"{self.area:g} m²")
        if self.rent_gross is not None:
            parts.append(f"{self.rent_gross:.0f} € warm")
        elif self.rent_net is not None:
            parts.append(f"{self.rent_net:.0f} € kalt")
        head = ", ".join(parts)
        tags = ""
        if self.wbs_required:
            tags += " · WBS"
        if self.senior:
            tags += " · Senior"
        return f"{head} | {self.address} ({self.company_name}){tags}"
