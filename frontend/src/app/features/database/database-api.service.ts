import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';

export interface DatabaseInfo {
  provider: string;
  db_name: string;
  created_at: string;
  credentials_available: boolean;
}

export interface DatabaseCredentials {
  provider: string;
  url: string;
  token: string;
  read_only: boolean;
  how_to_connect: string;
}

@Injectable({ providedIn: 'root' })
export class DatabaseApiService extends BaseApiService {
  protected readonly path = '/api/database';

  info(): Observable<DatabaseInfo> {
    return this.get<DatabaseInfo>();
  }

  credentials(readOnly: boolean): Observable<DatabaseCredentials> {
    return this.post<DatabaseCredentials>('/credentials', { read_only: readOnly });
  }
}
