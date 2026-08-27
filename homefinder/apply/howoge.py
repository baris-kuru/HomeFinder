"""HOWOGE: a multi-step TYPO3 application wizard ("Besichtigung anfragen").

The exposé links to a Bewerbungsprozess form (with a per-listing cHash). It has
up to 4 steps; we fill the fields we recognise on each step and advance with
"Weiter", stopping before the final submit so the user reviews and sends.
No captcha.
"""
from __future__ import annotations

from ..browser import dismiss_consent
from .base import Adapter

# name-fragment -> applicant key. Matched case-insensitively against input names.
_FIELD_MAP = [
    ("firstName", "first_name"),
    ("lastName", "last_name"),
    ("email", "email"),
    ("phone", "phone"),
    ("telephone", "phone"),
    ("mobile", "phone"),
    ("street", "street"),
    ("houseNumber", "house_number"),
    ("zip", "zip"),
    ("postal", "zip"),
    ("city", "city"),
    ("person", "num_occupants"),
]


def _quick_fill(page, selector: str, value) -> None:
    """Fill only if the field is present and visible; short timeout, no retries."""
    if value in (None, ""):
        return
    try:
        loc = page.locator(selector).first
        if loc.count() and loc.is_visible():
            loc.fill(str(value), timeout=1500)
    except Exception:
        pass


class HowogeAdapter(Adapter):
    company = "howoge"

    def fill(self, page, listing, applicant) -> None:
        page.goto(listing.deeplink, wait_until="domcontentloaded", timeout=60000)
        dismiss_consent(page)

        # Enter the wizard via the "Besichtigung anfragen" href (carries the cHash).
        href = page.evaluate(
            "() => { const a = [...document.querySelectorAll('a')]"
            ".find(a => /besichtigung anfragen|wohnung anfragen/i.test(a.textContent)"
            " && /bewerbungsprozess|visitform/i.test(a.href)); return a ? a.href : null; }"
        )
        if not href:
            return
        page.goto(href, wait_until="domcontentloaded", timeout=60000)
        dismiss_consent(page)
        page.wait_for_timeout(600)

        # Steps 1-3 are acknowledgements (WBS / income / credit "zur Kenntnis
        # genommen"); step 4 is the actual contact form. Advance until the name
        # field appears, filling it there. Stop before the final submit.
        for _ in range(6):
            name_field = page.locator("input[name*='firstName' i]").first
            if name_field.count() and name_field.is_visible():
                for frag, key in _FIELD_MAP:
                    _quick_fill(page, f"input[name*='{frag}' i]", applicant.get(key))
                break
            self._check_ack(page)
            if not self._go_next(page):
                break
            page.wait_for_timeout(900)

    def _check_ack(self, page) -> None:
        # Tick the current step's acknowledgement with a REAL click so the
        # framework enables "Weiter" (force-setting the value does not).
        try:
            boxes = page.locator("input[type=checkbox]")
            for i in range(min(boxes.count(), 8)):
                b = boxes.nth(i)
                try:
                    if not b.is_visible() or b.is_checked():
                        continue
                    b.click(timeout=1500)          # real click on the input
                except Exception:
                    try:                            # fall back to clicking its label
                        cid = b.get_attribute("id")
                        if cid:
                            page.locator(f"label[for='{cid}']").first.click(timeout=1500)
                    except Exception:
                        continue
        except Exception:
            pass

    def _go_next(self, page) -> bool:
        # Click "Weiter" to advance. If only the final submit remains, stop.
        btn = page.locator(
            "button:has-text('Weiter'), a:has-text('Weiter'), input[value*='Weiter' i]"
        ).first
        try:
            if btn.count() and btn.is_visible():
                btn.click(timeout=2500)
                page.wait_for_timeout(400)
                return True
        except Exception:
            pass
        return False
