"""Base class for every service."""

from __future__ import annotations

import logging
from typing import TypeVar

from .errors import AppError

T = TypeVar("T")


class BaseService:
    """Business logic. Knows nothing about HTTP or SQL."""

    def __init__(self) -> None:
        self.log = logging.getLogger(type(self).__module__)

    @staticmethod
    def require(value: T | None, error: AppError) -> T:
        """Return ``value`` or raise ``error`` — the one-line guard clause."""
        if value is None or value is False:
            raise error
        return value
