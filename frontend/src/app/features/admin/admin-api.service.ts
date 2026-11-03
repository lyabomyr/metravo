import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';
import { User } from '../../core/auth/auth.models';

export interface Overview {
  users: number;
  users_by_plan: Record<string, number>;
  telegram_chats: number;
}

/** The running API instance, as its monitor sees it (backend services/monitoring). */
export interface SystemHealth {
  uptime_seconds: number;
  memory_used_mb: number;
  memory_limit_mb: number | null;
  memory_percent: number | null;
  cpu_percent: number | null;
  last_scan: { searches_scanned: number; new_listings: number; errors: string[] } | null;
  last_scan_failed: string | null;
  failing_sources: Record<string, number>;
  active_alerts: Record<string, string>;
  recent_logs: { at: string; level: string; logger: string; message: string }[];
}

/** One table of the database (backend services/admin/database_usage.py). */
export interface TableUsage {
  name: string;
  rows: number;
  bytes: number | null;
}

@Injectable({ providedIn: 'root' })
export class AdminApiService extends BaseApiService {
  protected readonly path = '/api/admin';

  overview(): Observable<Overview> {
    return this.get<Overview>('/overview');
  }

  system(): Observable<SystemHealth> {
    return this.get<SystemHealth>('/system');
  }

  database(): Observable<TableUsage[]> {
    return this.get<TableUsage[]>('/database');
  }

  users(): Observable<User[]> {
    return this.get<User[]>('/users');
  }

  setPlan(userId: string, plan: string): Observable<User> {
    return this.put<User>(`/users/${userId}/plan`, { plan });
  }
}
