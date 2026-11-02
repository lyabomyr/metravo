import { COMMON } from './common';
import { INTRO } from './intro';
import { LANDING } from './landing';
import { PAGES } from './pages';

/** English — the reference. Every other language must define exactly these keys. */
export const EN = { ...COMMON, ...LANDING, ...INTRO, ...PAGES };

export type TranslationKey = keyof typeof EN;
export type Dictionary = Record<TranslationKey, string>;
/** One section of another language, checked against the English section. */
export type Section<T> = Record<keyof T, string>;
