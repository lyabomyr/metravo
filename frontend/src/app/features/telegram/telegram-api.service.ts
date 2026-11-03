import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { BaseApiService } from '../../core/api/base-api.service';
import { TelegramChat, TelegramLink } from './telegram.model';

@Injectable({ providedIn: 'root' })
export class TelegramApiService extends BaseApiService {
  protected readonly path = '/api/telegram';

  /** With a search, the chat it connects gets that search only. */
  createLink(searchId?: string): Observable<TelegramLink> {
    return this.post<TelegramLink>('/link', searchId ? { search_id: searchId } : {});
  }

  searchChats(searchId: string): Observable<TelegramChat[]> {
    return this.get<TelegramChat[]>(`/searches/${searchId}/chats`);
  }

  route(chatId: string, searchId: string, receives: boolean): Observable<TelegramChat> {
    return this.put<TelegramChat>(`/chats/${chatId}/searches/${searchId}`, { receives });
  }

  chats(): Observable<TelegramChat[]> {
    return this.get<TelegramChat[]>('/chats');
  }

  disconnect(chatId: string): Observable<void> {
    return this.delete(`/chats/${chatId}`);
  }
}
