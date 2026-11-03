import { Component, DestroyRef, OnInit, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { filter, switchMap, timer } from 'rxjs';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { TelegramChat, TelegramLink } from './telegram.model';
import { TelegramApiService } from './telegram-api.service';
import { TelegramStatusService } from './telegram-status.service';

/** How often to check whether the user has pressed Start in Telegram. */
const POLL_MS = 3000;

/**
 * The two-click connection.
 *
 * The deep link is created as soon as this renders, so the button is a real
 * link: click 1 opens Telegram, click 2 is Telegram's own “Start”. The
 * component then notices the new chat by itself.
 */
@Component({
  selector: 'app-telegram-connect',
  imports: [TranslatePipe],
  template: `
    @if (link(); as link) {
      <div class="row">
        <a class="button button--primary" [href]="link.private_url" target="_blank" rel="noopener" data-cy="telegram-open">
          ✈️ {{ 'alerts.open' | t }}
        </a>
        <a class="button" [href]="link.group_url" target="_blank" rel="noopener" data-cy="telegram-group">{{ 'alerts.group' | t }}</a>
        @if (searchId()) {
          <button class="button" type="button" (click)="showChannel.set(!showChannel())" data-cy="telegram-channel">{{ 'searchAlerts.channel' | t }}</button>
        }
      </div>
      <p class="muted small">{{ 'alerts.pressStart' | t }}</p>
      @if (showChannel()) {
        <div class="banner stack stack--tight" data-cy="telegram-channel-steps">
          <span>1. <a [href]="link.channel_url" target="_blank" rel="noopener">{{ 'searchAlerts.channelAdd' | t }}</a></span>
          <span>2. {{ 'searchAlerts.channelPost' | t }}</span>
          <code data-cy="telegram-channel-code">{{ link.channel_code }}</code>
        </div>
      }
    } @else {
      <p class="muted"><span class="spinner"></span> {{ 'alerts.preparing' | t }}</p>
    }
  `,
})
export class TelegramConnectComponent implements OnInit {
  /** Connect a chat for this search only, from the search's page. */
  readonly searchId = input<string>();
  readonly connected = output<TelegramChat[]>();

  private readonly api = inject(TelegramApiService);
  private readonly status = inject(TelegramStatusService);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly link = signal<TelegramLink | null>(null);
  protected readonly showChannel = signal(false);
  /** Chats that existed before: only a new one means the user just connected. */
  private known: Set<string> | null = null;

  ngOnInit(): void {
    // Note the chats that exist first, then hand out the link: any chat after that is the new one.
    this.api
      .chats()
      .pipe(
        switchMap((chats) => {
          this.known = new Set(chats.map((chat) => chat.chat_id));
          return this.api.createLink(this.searchId());
        }),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((link) => this.link.set(link));
    timer(POLL_MS, POLL_MS)
      .pipe(
        filter(() => this.known !== null),
        switchMap(() => this.api.chats()),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((chats) => {
        const fresh = chats.filter((chat) => !this.known!.has(chat.chat_id));
        if (!fresh.length) return;
        this.known = new Set(chats.map((chat) => chat.chat_id));
        this.status.update(chats);
        this.connected.emit(chats);
      });
  }
}
