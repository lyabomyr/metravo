export type DealType = 'sale' | 'rent';
export type PropertyType = 'flat' | 'house';

export interface SearchDraft {
  name: string;
  city: string;
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
  city: 'krakow',
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

/** 15 → "Every 15 min", 180 → "Every 3 h", 1440 → "Daily". */
export function describeInterval(minutes: number): string {
  if (minutes >= 1440) return minutes === 1440 ? 'Daily' : `Every ${minutes / 1440} days`;
  if (minutes >= 60) return minutes === 60 ? 'Hourly' : `Every ${minutes / 60} h`;
  return `Every ${minutes} min`;
}
