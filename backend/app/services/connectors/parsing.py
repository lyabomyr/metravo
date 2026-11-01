"""Text → number helpers shared by HTML connectors."""

from __future__ import annotations

import re

_PRICE = re.compile(r"([\d\s]+)\s*zł", re.IGNORECASE)
_AREA = re.compile(r"(\d+[.,]?\d*)\s*m", re.IGNORECASE)
_ROOMS = re.compile(r"(\d+)\s*pok", re.IGNORECASE)


def parse_price(text: str | None) -> int | None:
    """'598 955 zł' → 598955."""
    match = _PRICE.search((text or "").replace("\xa0", " "))
    digits = re.sub(r"\D", "", match.group(1)) if match else ""
    return int(digits) if digits else None


def parse_area(text: str | None) -> float | None:
    """'40,60 m²' → 40.6."""
    match = _AREA.search(text or "")
    return float(match.group(1).replace(",", ".")) if match else None


def parse_rooms(text: str | None) -> int | None:
    """'2 pokoje' → 2."""
    match = _ROOMS.search(text or "")
    return int(match.group(1)) if match else None


def as_int(value) -> int | None:
    return int(value) if isinstance(value, (int, float)) else None


def as_float(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) else None
