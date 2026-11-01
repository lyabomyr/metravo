import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';
import { Listing, PriceChange } from './listing.model';

@Injectable({ providedIn: 'root' })
export class ListingsApiService extends BaseApiService {
  protected readonly path = '/api/listings';

  latest(searchId?: string, limit = 100): Observable<Listing[]> {
    return this.get<Listing[]>('', { search_id: searchId, limit });
  }

  priceChanges(limit = 20): Observable<PriceChange[]> {
    return this.get<PriceChange[]>('/price-changes', { limit });
  }
}
