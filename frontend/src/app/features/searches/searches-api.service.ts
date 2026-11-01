import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';
import { Search, SearchDraft } from './search.model';

@Injectable({ providedIn: 'root' })
export class SearchesApiService extends BaseApiService {
  protected readonly path = '/api/searches';

  list(): Observable<Search[]> {
    return this.get<Search[]>();
  }

  one(id: string): Observable<Search> {
    return this.get<Search>(`/${id}`);
  }

  create(draft: SearchDraft): Observable<Search> {
    return this.post<Search>('', draft);
  }

  update(id: string, draft: SearchDraft): Observable<Search> {
    return this.put<Search>(`/${id}`, draft);
  }

  remove(id: string): Observable<void> {
    return this.delete(`/${id}`);
  }
}
