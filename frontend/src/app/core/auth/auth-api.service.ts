import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../api/base-api.service';
import { Session, User } from './auth.models';

@Injectable({ providedIn: 'root' })
export class AuthApiService extends BaseApiService {
  protected readonly path = '/api/auth';

  createSession(provider: string, credential: string): Observable<Session> {
    return this.post<Session>('/session', { provider, credential });
  }

  me(): Observable<User> {
    return this.get<User>('/me');
  }

  setLocale(locale: string): Observable<User> {
    return this.put<User>('/me/locale', { locale });
  }
}
