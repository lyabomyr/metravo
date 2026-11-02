import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';

@Injectable({ providedIn: 'root' })
export class ExportApiService extends BaseApiService {
  protected readonly path = '/api/export';

  downloadListingsCsv(): Observable<void> {
    return this.download('/listings.csv', 'metravo-listings.csv');
  }
}
