import { Injectable, inject, signal } from '@angular/core';

import { TelegramChat } from './telegram.model';
import { TelegramApiService } from './telegram-api.service';

/**
 * Whether listings can reach the user at all. Until a chat is connected the
 * app keeps pointing the way; ``null`` while it is not known yet.
 */
@Injectable({ providedIn: 'root' })
export class TelegramStatusService {
  private readonly api = inject(TelegramApiService);
  readonly connected = signal<boolean | null>(null);

  refresh(): void {
    this.api.chats().subscribe({ next: (chats) => this.update(chats), error: () => this.connected.set(null) });
  }

  update(chats: TelegramChat[]): void {
    this.connected.set(chats.length > 0);
  }
}
