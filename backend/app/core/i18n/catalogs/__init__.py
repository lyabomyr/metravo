from . import en, pl, ru, uk

#: Every supported language. Adding one = a new module with the same keys as ``en``.
CATALOGS = {"en": en.MESSAGES, "pl": pl.MESSAGES, "uk": uk.MESSAGES, "ru": ru.MESSAGES}
