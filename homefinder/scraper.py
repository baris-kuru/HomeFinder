"""Scrape inberlinwohnen.de/wohnungsfinder via Playwright.

Listings are rendered by Laravel Livewire; each row embeds a `wire:snapshot`
attribute containing the full listing JSON. We read those directly rather than
scraping visible text.
"""
from __future__ import annotations

import json

from playwright.sync_api import sync_playwright

from .browser import USER_AGENT, dismiss_consent, new_context
from .models import Listing

URL = "https://www.inberlinwohnen.de/wohnungsfinder/"

# JS that pulls every wire:snapshot on the page and returns the listing item dicts.
_EXTRACT_JS = """
() => {
  const out = [];
  document.querySelectorAll('[wire\\\\:snapshot]').forEach(el => {
    try {
      const snap = JSON.parse(el.getAttribute('wire:snapshot'));
      const item = snap && snap.data && snap.data.item;
      // item is nested as [ {...fields...}, {"s":"arr"} ]
      const obj = Array.isArray(item) ? item[0] : item;
      if (obj && obj.id && obj.deeplink) out.push(obj);
    } catch (e) {}
  });
  return out;
}
"""


# Returns the id of the first *listing* (skipping non-listing wire components).
_FIRST_LISTING_ID_JS = """
() => {
  for (const el of document.querySelectorAll('[wire\\\\:snapshot]')) {
    try {
      const it = JSON.parse(el.getAttribute('wire:snapshot')).data.item;
      const o = Array.isArray(it) ? it[0] : it;
      if (o && o.id && o.deeplink) return o.id;
    } catch (e) {}
  }
  return null;
}
"""


def _page_items(page) -> list[dict]:
    return page.evaluate(_EXTRACT_JS)


def scrape(browser, max_pages: int = 1) -> list[Listing]:
    """Scrape listings using an already-launched Playwright browser.

    max_pages=1 reads only the newest page (enough for frequent polling);
    pass a larger number (e.g. 30) on the first run to backfill everything.
    """
    items_by_id: dict[int, dict] = {}
    context = new_context(browser)
    try:
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        # Wait for the Livewire table to render at least one listing.
        page.wait_for_function("document.querySelectorAll('[wire\\\\:snapshot]').length > 0",
                               timeout=30000)
        dismiss_consent(page)  # otherwise the consent modal intercepts pagination clicks
        # Saving consent briefly re-renders the table; wait for listings to return.
        page.wait_for_function("(" + _FIRST_LISTING_ID_JS + ")() !== null", timeout=30000)

        for _ in range(max_pages):
            for obj in _page_items(page):
                items_by_id[int(obj["id"])] = obj
            if not _goto_next_page(page):
                break
    finally:
        context.close()

    return [Listing.from_snapshot(o) for o in items_by_id.values()]


def fetch(max_pages: int = 1, headless: bool = True) -> list[Listing]:
    """Standalone scrape that manages its own browser (for CLI / testing)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            return scrape(browser, max_pages=max_pages)
        finally:
            browser.close()


def _goto_next_page(page) -> bool:
    """Click the 'Vor' (next) pagination button. Returns False if there's no next page.

    Pagination is driven by Livewire ($dispatch('nextPage')); we click the button
    and wait for the first listing id to change.
    """
    before = page.evaluate(_FIRST_LISTING_ID_JS)
    btn = page.query_selector("button:has-text('Vor')")
    if not btn or before is None:
        return False
    try:
        btn.scroll_into_view_if_needed(timeout=3000)
        btn.click(timeout=5000)
        page.wait_for_function(
            "(prev) => (" + _FIRST_LISTING_ID_JS + ")() !== null && ("
            + _FIRST_LISTING_ID_JS + ")() !== prev",
            arg=before,
            timeout=10000,
        )
    except Exception:
        return False
    return True


if __name__ == "__main__":
    import sys

    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    listings = fetch(max_pages=pages, headless=True)
    print(f"Fetched {len(listings)} listings\n")
    for l in listings[:15]:
        print(f"  #{l.id} {l.summary()}")
        print(f"       {l.company} -> {l.deeplink}")
