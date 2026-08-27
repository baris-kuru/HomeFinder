"""Base class + shared helpers for company application adapters.

An adapter navigates to a listing's application form and fills it with the
applicant's details, then STOPS before submitting. The human reviews the open
browser tab and clicks the final submit button themselves.
"""
from __future__ import annotations

from ..models import Listing


class Adapter:
    company: str = ""

    def fill(self, page, listing: Listing, applicant: dict) -> None:
        """Navigate to the form and fill it. Must NOT submit."""
        raise NotImplementedError


# ---- small, forgiving helpers (never raise; return whether they did something) ----

def try_fill(scope, selector: str, value, timeout: int = 8000) -> bool:
    """Fill an input. Falls back to force-fill, then to a JS value-set with events,
    so forms that render oddly in one mode still get populated."""
    if value is None or value == "":
        return False
    loc = scope.locator(selector).first
    try:
        loc.wait_for(state="visible", timeout=timeout)
        loc.fill(str(value), timeout=timeout)
        return True
    except Exception:
        pass
    try:
        loc.fill(str(value), timeout=3000, force=True)
        return True
    except Exception:
        pass
    # Last resort: set the value directly and fire input/change so frameworks notice.
    try:
        loc.evaluate(
            "(el, v) => { el.value = v;"
            " el.dispatchEvent(new Event('input', {bubbles:true}));"
            " el.dispatchEvent(new Event('change', {bubbles:true})); }",
            str(value),
        )
        return True
    except Exception:
        return False


def try_check(scope, selector: str, timeout: int = 5000) -> bool:
    """Tick a checkbox. Handles Material-style checkboxes whose real <input> is
    visually hidden by force-checking, then falling back to a JS check + event."""
    loc = scope.locator(selector).first
    try:
        if loc.is_checked():
            return True
    except Exception:
        pass
    try:
        loc.check(timeout=timeout, force=True)
        return True
    except Exception:
        pass
    try:
        loc.evaluate(
            "el => { if (!el.checked) { el.checked = true;"
            " el.dispatchEvent(new Event('change', {bubbles:true})); } }"
        )
        return True
    except Exception:
        return False


def try_click(scope, selector: str, timeout: int = 5000) -> bool:
    try:
        loc = scope.locator(selector).first
        loc.wait_for(state="visible", timeout=timeout)
        loc.click(timeout=timeout)
        return True
    except Exception:
        return False


def try_select(scope, selector: str, label: str, timeout: int = 5000) -> bool:
    """Select an <option> by visible label (native <select>)."""
    if not label:
        return False
    try:
        loc = scope.locator(selector).first
        loc.wait_for(state="attached", timeout=timeout)
        loc.select_option(label=label, timeout=timeout)
        return True
    except Exception:
        return False


def try_dropdown(scope, trigger_selector: str, option_text: str, timeout: int = 5000) -> bool:
    """Open a custom (Angular Material / formly) dropdown and pick an option by text."""
    if not option_text:
        return False
    try:
        scope.locator(trigger_selector).first.click(timeout=timeout)
        opt = scope.get_by_role("option", name=option_text, exact=False).first
        opt.click(timeout=timeout)
        return True
    except Exception:
        return False
