"""Gewobag: the inquiry form is an embedded Wohnungshelden iframe.

Flow: open the exposé -> click "Anfrage senden" (reveals the iframe) -> fill the
fields inside the iframe. reCAPTCHA v3 is invisible; the user just clicks
"Anfrage versenden" at the end.

This adapter also covers any other company that embeds a Wohnungshelden form.
"""
from __future__ import annotations

from ..browser import dismiss_consent
from .base import Adapter, try_check, try_click, try_dropdown, try_fill, try_select

FRAME = "iframe[src*='wohnungshelden']"


class WohnungsheldenAdapter(Adapter):
    company = "gewobag"

    def fill(self, page, listing, applicant) -> None:
        page.goto(listing.deeplink, wait_until="domcontentloaded", timeout=60000)
        dismiss_consent(page)
        # Switch to the inquiry tab, which mounts the Wohnungshelden iframe.
        try_click(page, "button.rental-contact, button:has-text('Anfrage senden')")

        frame = page.frame_locator(FRAME)
        # Wait for the form inside the iframe.
        try:
            frame.locator("#firstName").wait_for(state="visible", timeout=20000)
        except Exception:
            return  # iframe never appeared; leave the page open for manual handling

        # Salutation ("Anrede") is an Angular Material dropdown, not a native select.
        sal = applicant.get("salutation", "")
        if not try_select(frame, "#salutation", sal):
            try_dropdown(frame, "#salutation", sal)

        try_fill(frame, "#firstName", applicant["first_name"])
        try_fill(frame, "#lastName", applicant["last_name"])
        try_fill(frame, "#email", applicant["email"])
        try_fill(frame, "#phone-number", applicant["phone"])
        # A separate required "Mobilfunknummer" formly field.
        try_fill(frame, "[id*='telephone_number']", applicant["phone"])
        try_fill(frame, "#street", applicant["street"])
        try_fill(frame, "#house-number", applicant["house_number"])
        try_fill(frame, "#zip-code", applicant["zip"])
        try_fill(frame, "#city", applicant["city"])
        if applicant.get("message"):
            try_fill(frame, "#applicant-message", applicant["message"])

        # Company-specific formly fields (ids carry stable German fragments).
        try_fill(frame, "[id*='gesamtzahl_der_einziehenden_personen']",
                 applicant.get("num_occupants", 1))
        if not try_select(frame, "[id*='fuer_wen_wird_die_wohnungsanfrage_gestellt']", "mich selbst"):
            try_dropdown(frame, "[id*='fuer_wen_wird_die_wohnungsanfrage_gestellt']", "mich selbst")

        # Confirm the data-protection / truthfulness checkbox (target the real <input>,
        # not the custom wrapper element that shares the id fragment).
        try_check(frame, "input[id*='datenschutzhinweis_bestaetigt']")
