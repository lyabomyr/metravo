import { Component, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { ApiError } from '../api/api-error';
import { TranslatePipe } from '../i18n/translate.pipe';

/** Shows an error; a plan limit gets a link to upgrade instead of a dead end. */
@Component({
  selector: 'app-error-banner',
  imports: [RouterLink, TranslatePipe],
  template: `
    @if (error(); as error) {
      <div class="banner banner--error" role="alert" data-cy="error">
        {{ error.key ? (error.key | t) : error.message }}
        @if (error.code === 'LimitReached') {
          <a routerLink="/billing" data-cy="upgrade-link">{{ 'common.upgrade' | t }}</a>
        }
      </div>
    }
  `,
})
export class ErrorBannerComponent {
  readonly error = input<ApiError | null>(null);
}
