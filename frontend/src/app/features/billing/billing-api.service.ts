import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';

export interface Plan {
  code: string;
  name: string;
  price_pln: number;
  max_searches: number;
  scan_interval_minutes: number;
  sources: string[];
  price_alerts: boolean;
  database_credentials: boolean;
}

export interface Subscription {
  provider: string;
  plan: string;
  status: string;
  updated_at: string;
}

@Injectable({ providedIn: 'root' })
export class BillingApiService extends BaseApiService {
  protected readonly path = '/api/billing';

  plans(): Observable<Plan[]> {
    return this.get<Plan[]>('/plans');
  }

  subscription(): Observable<Subscription | null> {
    return this.get<Subscription | null>('/subscription');
  }

  checkout(plan: string): Observable<{ url: string }> {
    return this.post<{ url: string }>('/checkout', { plan });
  }

  portal(): Observable<{ url: string }> {
    return this.post<{ url: string }>('/portal');
  }

  /** Test mode only: play the payment provider and call our own webhook. */
  sendTestWebhook(event: Record<string, string>): Observable<unknown> {
    return this.post('/webhook', event);
  }
}
