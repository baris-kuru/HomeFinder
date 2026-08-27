"""Shared Playwright helpers: realistic context + cookie-consent dismissal."""
from __future__ import annotations

# A realistic UA is required for inberlinwohnen: the default headless UA makes the
# server return a download response instead of the page.
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def new_context(browser):
    return browser.new_context(
        user_agent=USER_AGENT,
        locale="de-DE",
        accept_downloads=False,
        extra_http_headers={"Accept-Language": "de-DE,de;q=0.9"},
    )


# Consent buttons across the sites we touch. Privacy-preserving choices first
# (decline / essential-only), then plain "accept" fallbacks so the overlay never
# blocks interaction. Buttons may be <button>, <a>, or <input>.
_CONSENT_TEXTS = [
    "Ablehnen",              # Cookiebot: decline all
    "Nur notwendige",
    "Nur essenzielle",
    "Auswahl erlauben",     # Cookiebot: allow current (necessary-only) selection
    "Auswahl speichern",
    "Speichern",            # inberlinwohnen: save (essential only)
    "Alle zulassen",        # fallbacks (accept)
    "Alle akzeptieren",
    "Akzeptieren",
    "Zustimmen",
    "Einverstanden",
]


def dismiss_consent(page, timeout_ms: int = 4000) -> bool:
    """Click a cookie/consent button if one is blocking the page. Best-effort."""
    page.wait_for_timeout(1000)  # let the banner mount
    for text in _CONSENT_TEXTS:
        for role in ("button", "link"):
            try:
                el = page.get_by_role(role, name=text, exact=False)
                if el.count() and el.first.is_visible():
                    el.first.click(timeout=timeout_ms)
                    page.wait_for_timeout(600)
                    return True
            except Exception:
                continue
        # Some banners use plain clickable text/inputs without an ARIA role.
        try:
            el = page.locator(
                f"button:has-text('{text}'), a:has-text('{text}'), input[value='{text}']"
            ).first
            if el.is_visible():
                el.click(timeout=timeout_ms)
                page.wait_for_timeout(600)
                return True
        except Exception:
            continue
    return False
