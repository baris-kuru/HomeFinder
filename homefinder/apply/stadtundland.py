"""STADT UND LAND: inline contact form on the listing detail page. No captcha."""
from __future__ import annotations

from ..browser import dismiss_consent
from .base import Adapter, try_check, try_click, try_fill


class StadtUndLandAdapter(Adapter):
    company = "stadtundland"

    def fill(self, page, listing, applicant) -> None:
        page.goto(listing.deeplink, wait_until="domcontentloaded", timeout=60000)
        dismiss_consent(page)
        # Reveal / scroll to the contact form.
        try_click(page, "a:has-text('Kontakt aufnehmen'), button:has-text('Kontakt aufnehmen')")
        page.wait_for_timeout(500)

        try_fill(page, "#name", applicant["first_name"])
        try_fill(page, "#surname", applicant["last_name"])
        try_fill(page, "#street", applicant["street"])
        try_fill(page, "#houseNo", applicant["house_number"])
        try_fill(page, "#postalCode", applicant["zip"])
        try_fill(page, "#city", applicant["city"])
        try_fill(page, "#phone", applicant["phone"])
        try_fill(page, "#email", applicant["email"])

        # Required consent checkboxes (privacy + provision notice).
        try_check(page, "#privacy")
        try_check(page, "#provision")
