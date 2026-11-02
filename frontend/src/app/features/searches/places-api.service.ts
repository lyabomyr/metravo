import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';
import { Place } from './search.model';

/** Cities, towns and villages, by name or by a point on the map (OpenStreetMap, via the API). */
@Injectable({ providedIn: 'root' })
export class PlacesApiService extends BaseApiService {
  protected readonly path = '/api/places';

  search(text: string): Observable<Place[]> {
    return this.get<Place[]>('', { q: text });
  }

  at(lat: number, lon: number): Observable<Place | null> {
    return this.get<Place | null>('/at', { lat: lat.toFixed(5), lon: lon.toFixed(5) });
  }
}
