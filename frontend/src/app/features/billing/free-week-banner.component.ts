import { Component, computed, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { SessionStore } from '../../core/auth/session.store';
import { WhenPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';

const DAY_MS = 24 * 60 * 60 * 1000;

/** How long the free week has left, or that it has ended and checks are paused. */
@Component({
  selector: 'app-free-week-banner',
  imports: [RouterLink, TranslatePipe, WhenPipe],
  template: `
    @if (session.user(); as user) {
      @if (!user.active) {
        <div class="banner banner--warning row row--between" role="status" data-cy="free-week-over">
          <span>⏸ {{ 'freeWeek.over' | t: { date: (user.free_until | when: 'date') } }}</span>
          <a class="button button--primary button--small" routerLink="/billing">{{ 'freeWeek.seePro' | t }}</a>
        </div>
      } @else if (daysLeft() !== null) {
        <div class="banner banner--info row row--between" data-cy="free-week-left">
          <span>🎁 {{ 'freeWeek.left' | t: { n: daysLeft()! } }}</span>
          <a class="link small" routerLink="/billing">{{ 'freeWeek.seePro' | t }}</a>
        </div>
      }
    }
  `,
})
export class FreeWeekBannerComponent {
  protected readonly session = inject(SessionStore);
  protected readonly daysLeft = computed(() => {
    const until = this.session.user()?.free_until;
    return until ? Math.max(1, Math.ceil((Date.parse(until) - Date.now()) / DAY_MS)) : null;
  });
}
