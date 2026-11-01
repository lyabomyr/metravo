import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ApiError } from '../api/api-error';

/** Shows an API error; a plan limit gets a link to upgrade instead of a dead end. */
@Component({
  selector: 'app-error-banner',
  imports: [RouterLink],
  template: `
    @if (error(); as error) {
      <div class="banner banner--error" data-cy="error">
        {{ error.message }}
        @if (error.code === 'LimitReached') {
          <a routerLink="/billing" data-cy="upgrade-link">Upgrade to Pro →</a>
        }
      </div>
    }
  `,
})
export class ErrorBannerComponent {
  readonly error = input<ApiError | null>(null);
}
