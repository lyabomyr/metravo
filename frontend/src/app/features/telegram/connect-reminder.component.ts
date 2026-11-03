import { Component, OnInit, computed, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { NavigationEnd, Router, RouterLink } from '@angular/router';
import { filter, map } from 'rxjs';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { TelegramStatusService } from './telegram-status.service';

/** Pages where connecting is already the thing on screen (a search's own notifications page too). */
const CONNECT_PAGES = ['/welcome', '/notifications'];

/** Shown on every page until a messenger is connected: without one, no notification reaches the user. */
@Component({
  selector: 'app-connect-reminder',
  imports: [RouterLink, TranslatePipe],
  template: `
    @if (visible()) {
      <div class="banner banner--warning row row--between" role="status" data-cy="connect-reminder">
        <span>🔕 {{ 'reminder.text' | t }}</span>
        <a class="button button--primary button--small" routerLink="/welcome" data-cy="connect-reminder-action">{{ 'reminder.action' | t }}</a>
      </div>
    }
  `,
})
export class ConnectReminderComponent implements OnInit {
  private readonly status = inject(TelegramStatusService);
  private readonly router = inject(Router);
  private readonly url = toSignal(
    this.router.events.pipe(
      filter((event) => event instanceof NavigationEnd),
      map(() => this.router.url),
    ),
    { initialValue: this.router.url },
  );

  protected readonly visible = computed(
    () => this.status.connected() === false && !CONNECT_PAGES.some((page) => this.url().startsWith(page) || this.url().endsWith(page)),
  );

  ngOnInit(): void {
    this.status.refresh();
  }
}
