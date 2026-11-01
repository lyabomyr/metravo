export interface Listing {
  search_id: string;
  key: string;
  source: string;
  deal_type: 'sale' | 'rent';
  url: string;
  title: string;
  price: number | null;
  area: number | null;
  rooms: number | null;
  location: string | null;
  image_url: string | null;
  first_seen_at: string;
  last_seen_at: string;
}

export interface PriceChange {
  search_id: string;
  key: string;
  title: string;
  url: string;
  old_price: number;
  new_price: number;
  changed_at: string;
}

export interface ScanReport {
  searches_scanned: number;
  fetches: number;
  listings_seen: number;
  new_listings: number;
  price_changes: number;
  messages_sent: number;
  errors: string[];
}
