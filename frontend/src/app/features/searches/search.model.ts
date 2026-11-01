export interface SearchDraft {
  name: string;
  city: string;
  max_price: number;
  min_area: number;
  max_area: number | null;
  min_build_year: number | null;
  sources: string[];
  enabled: boolean;
}

export interface Search extends SearchDraft {
  id: string;
  reject_keywords: string[];
  last_scanned_at: string | null;
  created_at: string;
}

export const DEFAULT_SEARCH: SearchDraft = {
  name: 'My flat',
  city: 'krakow',
  max_price: 600000,
  min_area: 40,
  max_area: null,
  min_build_year: null,
  sources: ['otodom', 'olx', 'morizon'],
  enabled: true,
};
