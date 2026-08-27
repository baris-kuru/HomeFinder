"""HomeFinder main loop.

Every `interval_seconds`:
  1. scrape the newest listings from inberlinwohnen
  2. skip ones already seen
  3. for new listings that match the filters:
       - if an auto-fill adapter is enabled: open + pre-fill the form (left open,
         NOT submitted) in the visible browser
       - email the user so they can review and click submit
  4. record everything so nothing is processed twice
"""
from __future__ import annotations

import argparse
import time
import traceback

from playwright.sync_api import sync_playwright

from . import db, notify, scraper
from .apply import registry
from .apply.session import Applier
from .config import load
from .filters import is_applyable, matches


def run_once(cfg, conn, browser, applier, first_run: bool) -> None:
    fcfg = cfg["filters"]
    applicant = cfg["applicant"]
    max_pages = 30 if first_run else 2

    listings = scraper.scrape(browser, max_pages=max_pages)
    print(f"[{time.strftime('%H:%M:%S')}] scraped {len(listings)} listings", flush=True)

    new_matches = 0
    for listing in listings:
        if db.is_seen(conn, listing.id):
            continue
        ok, reason = matches(listing, fcfg)
        if not ok:
            db.mark_seen(conn, listing.id)
            continue

        new_matches += 1
        prefilled = False
        if applier and is_applyable(listing, fcfg, registry.SUPPORTED):
            prefilled = applier.prepare(listing, applicant)
        status = "prefilled" if prefilled else "notify_only"

        subject, body = notify.match_email(listing, prefilled)
        try:
            notify.send_email(cfg["email"], subject, body)
        except Exception as e:
            print(f"  ! email failed for #{listing.id}: {e}", flush=True)

        db.record_application(conn, listing.id, listing.company, status, listing.address)
        db.mark_seen(conn, listing.id)
        print(f"  + MATCH #{listing.id} {listing.summary()} [{status}]", flush=True)

    if new_matches == 0:
        print("  no new matches", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="HomeFinder — Berlin apartment auto-applier")
    ap.add_argument("--once", action="store_true", help="run a single cycle and exit")
    ap.add_argument("--no-apply", action="store_true",
                    help="scrape + email only; never open the apply browser")
    ap.add_argument("--seed", action="store_true",
                    help="mark all current listings as seen WITHOUT applying (baseline)")
    args = ap.parse_args()

    cfg = load()
    conn = db.connect()
    interval = int(cfg["poll"].get("interval_seconds", 300))
    headless_scrape = bool(cfg["poll"].get("headless_scrape", True))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless_scrape)

        if args.seed:
            listings = scraper.scrape(browser, max_pages=30)
            for l in listings:
                db.mark_seen(conn, l.id)
            print(f"Seeded {len(listings)} listings as seen. Future runs act only on new ones.")
            browser.close()
            return

        applier = None if args.no_apply else Applier(p)
        first_run = db.count_seen(conn) == 0
        try:
            while True:
                try:
                    run_once(cfg, conn, browser, applier, first_run)
                except Exception:
                    print("cycle error:\n" + traceback.format_exc(), flush=True)
                first_run = False
                if args.once:
                    break
                time.sleep(interval)
        finally:
            if applier:
                # Keep the window alive so the user can finish any open forms.
                print("Loop stopped. Close the browser window when you're done with open forms.",
                      flush=True)
            browser.close()


if __name__ == "__main__":
    main()
