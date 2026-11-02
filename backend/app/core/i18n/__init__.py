"""Translations for text the backend shows to people: API errors and Telegram messages.

The catalogs are static data, so one shared ``translator`` is enough.
"""

from .catalogs import CATALOGS
from .translator import DEFAULT_LOCALE, Translator

translator = Translator(CATALOGS)

__all__ = ["DEFAULT_LOCALE", "Translator", "translator"]
