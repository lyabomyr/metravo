import type { TranslationKey } from '../../core/i18n/locales/en';

export type DealType = 'sale' | 'rent';
export type PropertyType = 'flat' | 'house';

/** Any city, town or village in Poland (see backend ``places``). */
export interface Place {
  name: string;
  /** voivodeship/county/municipality/locality, as the portals spell it. */
  path: string;
  region_name: string;
  lat: number;
  lon: number;
  /** "gmina Zabierzów, powiat krakowski, …" — tells same-named villages apart. */
  detail: string;
}

export const KRAKOW: Place = {
  name: 'Kraków',
  path: 'malopolskie/krakow/krakow/krakow',
  region_name: 'małopolskie',
  lat: 50.0614,
  lon: 19.9366,
  detail: 'małopolskie',
};

export interface SearchDraft {
  name: string;
  place: Place;
  /** Kilometres around the place; 0 = the place itself. */
  radius_km: number;
  deal_type: DealType;
  property_type: PropertyType;
  min_price: number | null;
  max_price: number;
  min_area: number;
  max_area: number | null;
  min_rooms: number | null;
  max_rooms: number | null;
  max_price_per_m2: number | null;
  min_build_year: number | null;
  sources: string[];
  required_keywords: string[];
  interval_minutes: number;
  enabled: boolean;
}

export interface Search extends SearchDraft {
  id: string;
  reject_keywords: string[];
  last_scanned_at: string | null;
  created_at: string;
}

/** A budget that makes sense for each deal: a flat to buy vs a month's rent. */
export const DEFAULT_BUDGET: Record<DealType, number> = { sale: 600000, rent: 4000 };

export const DEFAULT_SEARCH: SearchDraft = {
  name: 'My flat',
  place: KRAKOW,
  radius_km: 0,
  deal_type: 'sale',
  property_type: 'flat',
  min_price: null,
  max_price: DEFAULT_BUDGET.sale,
  min_area: 40,
  max_area: null,
  min_rooms: null,
  max_rooms: null,
  max_price_per_m2: null,
  min_build_year: null,
  sources: ['otodom', 'olx', 'morizon'],
  required_keywords: [],
  interval_minutes: 1440,
  enabled: true,
};

/** How each choice reads in the UI. */
export const DEAL_LABEL: Record<DealType, TranslationKey> = { sale: 'deal.sale', rent: 'deal.rent' };
export const PROPERTY_LABEL: Record<PropertyType, TranslationKey> = { flat: 'property.flat', house: 'property.house' };
