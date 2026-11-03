import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it } from 'vitest';

import { I18nService } from './i18n.service';
import { EN } from './locales/en';
import { PL } from './locales/pl';
import { RU } from './locales/ru';
import { UK } from './locales/uk';

describe('I18nService', () => {
  let i18n: I18nService;

  beforeEach(() => {
    localStorage.clear();
    i18n = TestBed.inject(I18nService);
  });

  it('fills placeholders', () => {
    expect(i18n.t('listings.rooms', { n: 3 })).toBe('3 rooms');
  });

  it('switches language and remembers it', async () => {
    await i18n.use('uk');
    expect(i18n.t('nav.listings')).toBe('Оголошення');
    expect(localStorage.getItem('metravo.locale')).toBe('uk');
    expect(document.documentElement.lang).toBe('uk');
  });

  it('names portals the way people know them', async () => {
    expect(i18n.sources(['otodom', 'olx', 'komornik'])).toBe('Otodom, OLX, bailiff auctions');
    expect(i18n.sources('komornik')).toBe('Bailiff auctions');
    expect(i18n.sources('somewhere-new')).toBe('Somewhere-new');
    await i18n.use('pl');
    expect(i18n.sources('olx')).toBe('OLX');
  });

  it('keeps the same placeholders in every language', () => {
    const names = (text: string) => [...text.matchAll(/\{(\w+)\}/g)].map((match) => match[1]).sort().join();
    for (const dictionary of [PL, UK, RU]) {
      for (const key of Object.keys(EN) as (keyof typeof EN)[]) {
        expect(names(dictionary[key]), key).toBe(names(EN[key]));
      }
    }
  });
});
