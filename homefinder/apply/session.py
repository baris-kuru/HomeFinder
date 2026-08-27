"""Applier: a long-lived, visible browser that pre-fills forms and leaves the
tab open so the user can review and click submit."""
from __future__ import annotations

from pathlib import Path

from ..browser import USER_AGENT
from ..models import Listing
from . import registry

ROOT = Path(__file__).resolve().parent.parent.parent
PROFILE_DIR = ROOT / "browser_profile"


class Applier:
    def __init__(self, playwright):
        # A persistent profile keeps cookies/consent between runs and gives the
        # reCAPTCHA-v3 score a stable, real-looking browser to work with.
        self.context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(PROFILE_DIR),
            headless=False,
            user_agent=USER_AGENT,
            locale="de-DE",
            accept_downloads=False,
            args=["--start-maximized"],
        )

    def prepare(self, listing: Listing, applicant: dict) -> bool:
        """Open a tab, pre-fill the form, and leave it open. Returns True on success."""
        adapter = registry.get(listing.company)
        if adapter is None:
            return False
        page = self.context.new_page()
        try:
            adapter.fill(page, listing, applicant)
            return True
        except Exception as e:
            print(f"  ! fill failed for #{listing.id} ({listing.company}): {e}")
            return False  # leave the tab open regardless so the user can finish manually

    def close(self) -> None:
        try:
            self.context.close()
        except Exception:
            pass
