import type { Dictionary } from './locales/en';

export type Locale = 'en' | 'pl' | 'uk' | 'ru';

export interface LocaleOption {
  code: Locale;
  label: string;
}

export const LOCALES: LocaleOption[] = [
  { code: 'en', label: 'English' },
  { code: 'pl', label: 'Polski' },
  { code: 'uk', label: 'Українська' },
  { code: 'ru', label: 'Русский' },
];

/** English ships with the app; the others are downloaded only when chosen. */
export const LOADERS: Record<Locale, () => Promise<Dictionary>> = {
  en: () => import('./locales/en').then((m) => m.EN),
  pl: () => import('./locales/pl').then((m) => m.PL),
  uk: () => import('./locales/uk').then((m) => m.UK),
  ru: () => import('./locales/ru').then((m) => m.RU),
};

export function isLocale(value: string | null | undefined): value is Locale {
  return LOCALES.some((option) => option.code === value);
}
