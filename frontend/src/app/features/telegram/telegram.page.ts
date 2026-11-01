import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';

import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { TelegramConnectComponent } from './telegram-connect.component';
import { TelegramChat } from './telegram.model';
import { TelegramApiService } from './telegram-api.service';

@Component({
  selector: 'app-telegram-page',
  imports: [DatePipe, ErrorBannerComponent, PageHeaderComponent, TelegramConnectComponent],
  template: `
    <app-page-header title="Telegram" subtitle="Where new listings are delivered." />
    <app-error-banner [error]="error()" />

    <section class="card stack" style="margin-bottom: 16px">
      <h2>Connected chats</h2>
      @for (chat of chats(); track chat.chat_id) {
        <div class="row" style="justify-content: space-between" data-cy="telegram-chat">
          <span>
            {{ chat.title || chat.chat_id }}
            <span class="muted">· since {{ chat.linked_at | date: 'mediumDate' }} {{ chat.paused ? '· paused' : '' }}</span>
          </span>
          <button class="button button--danger" type="button" (click)="disconnect(chat)">Disconnect</button>
        </div>
      } @empty {
        <p class="muted" data-cy="no-chats">No chat connected yet.</p>
      }
    </section>

    <section class="card stack">
      <h2>Connect {{ chats().length ? 'another' : 'a' }} chat</h2>
      <app-telegram-connect (connected)="chats.set($event)" />
    </section>
  `,
})
export class TelegramPage extends BasePage implements OnInit {
  private readonly api = inject(TelegramApiService);
  protected readonly chats = signal<TelegramChat[]>([]);

  ngOnInit(): void {
    this.load();
  }

  protected disconnect(chat: TelegramChat): void {
    this.run(this.api.disconnect(chat.chat_id), () => this.load());
  }

  private load(): void {
    this.run(this.api.chats(), (chats) => this.chats.set(chats));
  }
}
