import { Component, OnInit, inject, signal } from '@angular/core';

import { WhenPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { TelegramConnectComponent } from '../telegram/telegram-connect.component';
import { TelegramChat } from '../telegram/telegram.model';
import { TelegramApiService } from '../telegram/telegram-api.service';
import { ChannelSettingsComponent } from './channel-settings.component';

/** Where listings go: Telegram chats, plus the extra Pro channels. */
@Component({
  selector: 'app-alerts-page',
  imports: [ChannelSettingsComponent, ErrorBannerComponent, PageHeaderComponent, TelegramConnectComponent, TranslatePipe, WhenPipe],
  template: `
    <app-page-header [title]="'alerts.title' | t" [subtitle]="'alerts.subtitle' | t" />
    <app-error-banner [error]="error()" />

    <h3 class="section-title">{{ 'alerts.telegram' | t }}</h3>
    <div class="list" style="margin-bottom: 8px">
      @for (chat of chats(); track chat.chat_id) {
        <div class="list__row" data-cy="telegram-chat">
          <span>
            ✈️ {{ chat.title || chat.chat_id }}
            <span class="muted small">
              · {{ 'alerts.since' | t: { date: (chat.linked_at | when: 'date') } }}
              @if (chat.paused) {
                · {{ 'alerts.paused' | t }}
              }
            </span>
          </span>
          <button class="button button--small button--danger" type="button" (click)="disconnect(chat)">{{ 'alerts.disconnect' | t }}</button>
        </div>
      } @empty {
        <div class="list__row muted" data-cy="no-chats">{{ 'alerts.noChats' | t }}</div>
      }
    </div>

    <section class="card stack" style="margin: 16px 0 24px">
      <h2>{{ 'alerts.connect' | t }}</h2>
      <app-telegram-connect (connected)="chats.set($event)" />
    </section>

    <app-channel-settings />
  `,
})
export class AlertsPage extends BasePage implements OnInit {
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
