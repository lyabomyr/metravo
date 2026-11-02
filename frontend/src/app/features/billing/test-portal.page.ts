import { Component, inject, input } from '@angular/core';
import { Router } from '@angular/router';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { BillingApiService } from './billing-api.service';

/** Stands in for Stripe's Customer Portal in test mode. */
@Component({
  selector: 'app-test-portal-page',
  imports: [ErrorBannerComponent, TranslatePipe],
  template: `
    <section class="card stack" style="max-width: 440px; margin: 48px auto">
      <span class="badge">{{ 'billing.testMode' | t }}</span>
      <h1>{{ 'billing.testPortalTitle' | t }}</h1>
      <app-error-banner [error]="error()" />
      <button class="button button--danger" type="button" (click)="cancelSubscription()" [disabled]="loading()" data-cy="test-cancel">
        {{ 'billing.testCancel' | t }}
      </button>
      <button class="link" type="button" (click)="back()">{{ 'common.back' | t }}</button>
    </section>
  `,
})
export class TestPortalPage extends BasePage {
  readonly customer = input<string>();

  private readonly api = inject(BillingApiService);
  private readonly router = inject(Router);

  protected cancelSubscription(): void {
    this.run(this.api.sendTestWebhook({ type: 'subscription.cancelled', customer_id: this.customer() ?? '' }), () => this.back());
  }

  protected back(): void {
    this.router.navigateByUrl('/billing');
  }
}
