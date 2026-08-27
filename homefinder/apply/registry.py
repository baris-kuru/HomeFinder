"""Map company slug -> adapter instance."""
from __future__ import annotations

from .degewo import DegewoAdapter
from .gewobag import WohnungsheldenAdapter
from .howoge import HowogeAdapter
from .stadtundland import StadtUndLandAdapter

ADAPTERS = {
    "gewobag": WohnungsheldenAdapter(),
    "degewo": DegewoAdapter(),
    "howoge": HowogeAdapter(),
    "stadtundland": StadtUndLandAdapter(),
}

SUPPORTED = set(ADAPTERS)


def get(company: str):
    return ADAPTERS.get(company)
