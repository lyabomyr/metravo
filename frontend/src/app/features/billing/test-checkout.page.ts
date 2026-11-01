import { Component, inject, input } from '@angular/core';
import { Router } from '@angular/router';

import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { BillingApiService } from './billing-api.service';

/**
 * Stands in for Stripe's hosted checkout when the backend runs the fake
 * payment provider (local, e2e). It sends the same webhook Stripe would.
 */
@Component({
  selector: 'app-test-checkout-page',
  imports: [ErrorBannerComponent],
  template: `
    <section class="card stack" style="max-width: 440px; margin: 48px auto">
      <span class="badge">test mode</span>
      <h1>Pay for {{ plan() }}</h1>
      <p class="muted">No real money moves. In production this page is Stripe Checkout.</p>
      <app-error-banner [error]="error()" />
      <button class="button button--primary" type="button" (click)="pay()" [disabled]="loading()" data-cy="test-pay">Pay (test)</button>
      <button class="link" type="button" (click)="cancel()">Cancel</button>
    </section>
  `,
})
export class TestCheckoutPage extends BasePage {
  readonly session = input<string>();
  readonly plan = input<string>();

  private readonly api = inject(BillingApiService);
  private readonly router = inject(Router);

  protected pay(): void {
    this.run(this.api.sendTestWebhook({ type: 'checkout.completed', session_id: this.session() ?? '' }), () =>
      this.router.navigateByUrl('/billing?status=success'),
    );
  }

  protected cancel(): void {
    this.router.navigateByUrl('/billing?status=cancelled');
  }
}
