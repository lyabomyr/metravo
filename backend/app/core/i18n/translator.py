"""Turns a message key into text in the user's language."""

from __future__ import annotations

from collections.abc import Mapping

DEFAULT_LOCALE = "en"


class Translator:
    """Message catalogs per locale, with English as the fallback.

    A key missing from every catalog is returned as-is, so a plain sentence
    can still be used where no translation exists yet.
    """

    def __init__(self, catalogs: Mapping[str, Mapping[str, str]], default: str = DEFAULT_LOCALE):
        self._catalogs = catalogs
        self._default = default

    @property
    def locales(self) -> tuple[str, ...]:
        return tuple(self._catalogs)

    def supports(self, locale: str | None) -> bool:
        return locale in self._catalogs

    def t(self, locale: str | None, key: str, /, **params) -> str:
        template = self._catalogs.get(locale or "", {}).get(key) or self._catalogs[self._default].get(key) or key
        return template.format(**params) if params else template

    def negotiate(self, header: str | None) -> str:
        """Pick a locale from an Accept-Language header or a bare code ("uk-UA,uk;q=0.9,en")."""
        for part in (header or "").split(","):
            code = part.split(";")[0].strip().lower().split("-")[0]
            if code in self._catalogs:
                return code
        return self._default
