import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';
import { TelegramChat, TelegramLink } from './telegram.model';

@Injectable({ providedIn: 'root' })
export class TelegramApiService extends BaseApiService {
  protected readonly path = '/api/telegram';

  createLink(): Observable<TelegramLink> {
    return this.post<TelegramLink>('/link');
  }

  chats(): Observable<TelegramChat[]> {
    return this.get<TelegramChat[]>('/chats');
  }

  disconnect(chatId: string): Observable<void> {
    return this.delete(`/chats/${chatId}`);
  }
}
