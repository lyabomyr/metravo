import { Injectable, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { BaseApiService } from '../api/base-api.service';

export interface SourceCapability {
  deal_type: 'sale' | 'rent';
  property_type: 'flat' | 'house' | 'room' | 'plot' | 'commercial';
}

export interface PublicConfig {
  env: string;
  auth_providers: string[];
  firebase: Record<string, string> | null;
  telegram_bot: string;
  billing_provider: string;
  sources: string[];
  source_capabilities: Record<string, SourceCapability[]>;
  /** What else each portal can filter by: "market:primary", "market:secondary", "private". */
  source_filters: Record<string, string[]>;
  /** How often a search may be scanned, in minutes. */
  scan_intervals: number[];
  /** The most often each plan allows, in minutes. */
  plan_min_intervals: Record<string, number>;
  /** The portals each plan includes. */
  plan_sources: Record<string, string[]>;
  /** Kilometres a search may reach around its place. */
  radius_choices: number[];
  /** Words a new search excludes unless the user changes them. */
  default_reject_keywords: string[];
  /** How many already-found listings a newly connected channel gets at once. */
  first_batch: number;
}

/** What the backend says the frontend may offer: sign-in methods, portals, schedules. */
@Injectable({ providedIn: 'root' })
export class PublicConfigService extends BaseApiService {
  protected readonly path = '/api/config';
  readonly config = signal<PublicConfig | null>(null);

  async load(): Promise<void> {
    this.config.set(await firstValueFrom(this.get<PublicConfig>()));
  }

  get value(): PublicConfig {
    const config = this.config();
    if (!config) throw new Error('Public config is not loaded yet');
    return config;
  }
}
