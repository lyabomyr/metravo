import { Component, OnInit, inject, output, signal } from '@angular/core';

import { PublicConfigService } from '../../core/config/public-config.service';
import { WhenPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { TestChannelComponent } from '../alerts/test-channel.component';
import { TelegramChat } from './telegram.model';
import { TelegramApiService } from './telegram-api.service';
import { TelegramConnectComponent } from './telegram-connect.component';
import { TelegramStatusService } from './telegram-status.service';

/** Telegram as one row of the channel list: its chats, connect, test, disconnect. */
@Component({
  selector: 'app-telegram-channel',
  imports: [ErrorBannerComponent, TelegramConnectComponent, TestChannelComponent, TranslatePipe, WhenPipe],
  template: `
    <div class="list__row list__row--stacked" data-cy="channel-telegram">
      <div class="row row--between">
        <span class="row">
          Telegram
          @if (chats().length) {
            <span class="badge badge--success">{{ 'alerts.connected' | t }}</span>
          } @else {
            <span class="badge">{{ 'alerts.availableNow' | t }}</span>
          }
        </span>
      </div>
      <app-error-banner [error]="error()" />
      @for (chat of chats(); track chat.chat_id) {
        <div class="row row--between" data-cy="telegram-chat">
          <span>
            ✈️ {{ chat.title || chat.chat_id }}
            <span class="muted small">
              · {{ 'alerts.since' | t: { date: (chat.linked_at | when: 'date') } }}
              @if (chat.paused) {
                · {{ 'alerts.paused' | t }}
              }
            </span>
          </span>
          <button class="button button--small button--danger" type="button" (click)="disconnect(chat)" data-cy="telegram-disconnect">
            {{ 'alerts.disconnect' | t }}
          </button>
        </div>
      } @empty {
        <span class="muted small" data-cy="no-chats">{{ 'alerts.noChats' | t }}</span>
      }
      @if (chats().length) {
        <app-test-channel code="telegram" />
      } @else {
        <app-telegram-connect (connected)="onConnected($event)" />
        <p class="muted small" data-cy="first-batch-note">{{ 'alerts.firstBatch' | t: { n: firstBatch } }}</p>
      }
    </div>
  `,
})
export class TelegramChannelComponent extends BasePage implements OnInit {
  readonly connected = output<void>();
  private readonly api = inject(TelegramApiService);
  private readonly status = inject(TelegramStatusService);
  protected readonly chats = signal<TelegramChat[]>([]);
  protected readonly firstBatch = inject(PublicConfigService).value.first_batch;

  ngOnInit(): void {
    this.load();
  }

  protected onConnected(chats: TelegramChat[]): void {
    this.chats.set(chats);
    this.connected.emit();
  }

  protected disconnect(chat: TelegramChat): void {
    this.run(this.api.disconnect(chat.chat_id), () => this.load());
  }

  private load(): void {
    this.run(this.api.chats(), (chats) => {
      this.chats.set(chats);
      this.status.update(chats);
    });
  }
}
