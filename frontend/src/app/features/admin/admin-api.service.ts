import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';
import { User } from '../../core/auth/auth.models';

export interface Overview {
  users: number;
  users_by_plan: Record<string, number>;
  tenant_databases: number;
  telegram_chats: number;
}

@Injectable({ providedIn: 'root' })
export class AdminApiService extends BaseApiService {
  protected readonly path = '/api/admin';

  overview(): Observable<Overview> {
    return this.get<Overview>('/overview');
  }

  users(): Observable<User[]> {
    return this.get<User[]>('/users');
  }

  setPlan(userId: string, plan: string): Observable<User> {
    return this.put<User>(`/users/${userId}/plan`, { plan });
  }
}
