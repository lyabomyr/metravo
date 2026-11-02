import { Component, inject, input, signal } from '@angular/core';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { NotificationsApiService } from './notifications-api.service';

/** "Send a test message": the user sees for themselves that alerts reach them. */
@Component({
  selector: 'app-test-channel',
  imports: [ErrorBannerComponent, TranslatePipe],
  template: `
    <div class="row">
      <button class="button button--small" type="button" (click)="send()" [disabled]="loading()" [attr.data-cy]="'test-' + code()">
        {{ 'alerts.test' | t }}
      </button>
      @if (sent()) {
        <span class="muted small" [attr.data-cy]="'test-sent-' + code()">✓ {{ 'alerts.testSent' | t }}</span>
      }
    </div>
    <app-error-banner [error]="error()" />
  `,
})
export class TestChannelComponent extends BasePage {
  readonly code = input.required<string>();
  private readonly api = inject(NotificationsApiService);
  protected readonly sent = signal(false);

  protected send(): void {
    this.sent.set(false);
    this.run(this.api.sendTest(this.code()), () => this.sent.set(true));
  }
}
