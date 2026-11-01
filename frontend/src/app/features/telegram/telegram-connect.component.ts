import { Component, DestroyRef, OnInit, inject, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { switchMap, timer } from 'rxjs';

import { TelegramChat, TelegramLink } from './telegram.model';
import { TelegramApiService } from './telegram-api.service';

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
  template: `
    @if (link(); as link) {
      <div class="row">
        <a class="button button--primary" [href]="link.private_url" target="_blank" rel="noopener" data-cy="telegram-open">
          Open Telegram
        </a>
        <a class="button" [href]="link.group_url" target="_blank" rel="noopener" data-cy="telegram-group">Add to a group</a>
      </div>
      <p class="muted">Then press <b>Start</b> in Telegram. This page updates by itself.</p>
    } @else {
      <p class="muted">Preparing your link…</p>
    }
  `,
})
export class TelegramConnectComponent implements OnInit {
  readonly connected = output<TelegramChat[]>();

  private readonly api = inject(TelegramApiService);
  private readonly destroyRef = inject(DestroyRef);
  protected readonly link = signal<TelegramLink | null>(null);

  ngOnInit(): void {
    this.api.createLink().pipe(takeUntilDestroyed(this.destroyRef)).subscribe((link) => this.link.set(link));
    timer(POLL_MS, POLL_MS)
      .pipe(
        switchMap(() => this.api.chats()),
        takeUntilDestroyed(this.destroyRef),
      )
      .subscribe((chats) => {
        if (chats.length) this.connected.emit(chats);
      });
  }
}
