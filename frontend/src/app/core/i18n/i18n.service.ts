import { Injectable, computed, signal } from '@angular/core';

import { LOADERS, Locale, isLocale } from './locales';
import { Dictionary, EN, TranslationKey } from './locales/en';

const STORAGE_KEY = 'metravo.locale';

export type Params = Record<string, string | number>;

/**
 * The UI language. Everything visible goes through `t()` (or the `t` pipe),
 * so switching language re-renders the page in place.
 */
@Injectable({ providedIn: 'root' })
export class I18nService {
  readonly locale = signal<Locale>('en');
  private readonly dictionary = signal<Dictionary>(EN);
  /** BCP-47 tag for Intl number and date formatting. */
  readonly intlLocale = computed(() => ({ en: 'en-GB', pl: 'pl-PL', uk: 'uk-UA', ru: 'ru-RU' })[this.locale()]);

  /** Called once at startup: the saved choice, else the browser's language, else English. */
  async init(): Promise<void> {
    await this.use(this.saved() ?? this.fromBrowser() ?? 'en', false);
  }

  async use(locale: Locale, remember = true): Promise<void> {
    this.dictionary.set(await LOADERS[locale]());
    this.locale.set(locale);
    document.documentElement.lang = locale;
    if (remember) {
      try {
        localStorage.setItem(STORAGE_KEY, locale);
      } catch {
        /* private mode: the choice lasts until reload */
      }
    }
  }

  t(key: TranslationKey, params: Params = {}): string {
    const template = this.dictionary()[key] ?? EN[key] ?? key;
    return template.replace(/\{(\w+)\}/g, (match, name: string) => (name in params ? String(params[name]) : match));
  }

  private saved(): Locale | null {
    try {
      const value = localStorage.getItem(STORAGE_KEY);
      return isLocale(value) ? value : null;
    } catch {
      return null;
    }
  }

  private fromBrowser(): Locale | null {
    const code = navigator.language?.slice(0, 2).toLowerCase();
    return isLocale(code) ? code : null;
  }
}
