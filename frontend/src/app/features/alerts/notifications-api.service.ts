import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';

export interface ChannelSetting {
  code: string;
  name: string;
  address_kind: 'email' | 'phone' | null;
  /** False while there is no way to deliver on it yet; the choice is still saved. */
  live: boolean;
  enabled: boolean;
  address: string;
  /** Allowed by the user's plan. */
  allowed: boolean;
}

@Injectable({ providedIn: 'root' })
export class NotificationsApiService extends BaseApiService {
  protected readonly path = '/api/notifications';

  channels(): Observable<ChannelSetting[]> {
    return this.get<ChannelSetting[]>('/channels');
  }

  update(code: string, enabled: boolean, address: string): Observable<ChannelSetting> {
    return this.put<ChannelSetting>(`/channels/${code}`, { enabled, address });
  }

  /** Sends a short message on the channel, to prove it reaches the user. */
  sendTest(code: string): Observable<void> {
    return this.post<void>(`/channels/${code}/test`);
  }
}
