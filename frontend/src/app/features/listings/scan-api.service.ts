import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';
import { ScanReport } from './listing.model';

@Injectable({ providedIn: 'root' })
export class ScanApiService extends BaseApiService {
  protected readonly path = '/api/scan';

  /** Scan the caller's searches that are due under their plan. */
  scanMine(): Observable<ScanReport> {
    return this.post<ScanReport>('/mine');
  }

  /** Admin only: every user's due searches. */
  scanAll(): Observable<ScanReport> {
    return this.post<ScanReport>('/all');
  }
}
