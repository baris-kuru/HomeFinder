"""degewo: inline TYPO3 inquiry form on the listing detail page.

The page renders the inquiry form more than once (responsive duplicates) and uses
content-visibility, which makes normal Playwright visibility checks unreliable.
So we set the values directly via JS on every matching field, firing input/change
so the framework registers them. Uses Friendly Captcha, which solves itself — the
user only clicks the final submit.
"""
from __future__ import annotations

from ..browser import dismiss_consent
from .base import Adapter, try_click

# id-suffix -> applicant key
_FIELDS = {
    "-firstname": "first_name",
    "-lastname": "last_name",
    "-email": "email",
    "-telephone": "phone",
    "-notes": "message",
}

_JS = """
(data) => {
  let n = 0;
  document.querySelectorAll("form[id^='form_apartment_inquiry']").forEach(form => {
    for (const [suffix, value] of Object.entries(data)) {
      if (value === "" || value == null) continue;
      const el = form.querySelector(`[id$='${suffix}']`);
      if (el) {
        el.value = value;
        el.dispatchEvent(new Event('input', {bubbles: true}));
        el.dispatchEvent(new Event('change', {bubbles: true}));
        n++;
      }
    }
  });
  return n;
}
"""


class DegewoAdapter(Adapter):
    company = "degewo"

    def fill(self, page, listing, applicant) -> None:
        page.goto(listing.deeplink, wait_until="domcontentloaded", timeout=60000)
        dismiss_consent(page)

        data = {suffix: applicant.get(key, "") for suffix, key in _FIELDS.items()}
        page.evaluate(_JS, data)

        # Reveal the inquiry section so the user immediately sees the filled form.
        try_click(page, "a:has-text('Anfrage senden'), button:has-text('Anfrage senden')")
