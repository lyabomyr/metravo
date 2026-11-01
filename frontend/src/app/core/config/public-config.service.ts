import { Injectable, signal } from '@angular/core';
import { firstValueFrom } from 'rxjs';

import { BaseApiService } from '../api/base-api.service';

export interface City {
  key: string;
  label: string;
}

export interface SourceCapability {
  deal_type: 'sale' | 'rent';
  property_type: 'flat' | 'house';
}

export interface PublicConfig {
  env: string;
  auth_providers: string[];
  firebase: Record<string, string> | null;
  telegram_bot: string;
  billing_provider: string;
  sources: string[];
  source_capabilities: Record<string, SourceCapability[]>;
  cities: City[];
}

/** What the backend says the frontend may offer: sign-in methods, cities, portals. */
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
