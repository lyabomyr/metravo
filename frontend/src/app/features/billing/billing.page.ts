import { Component, OnInit, inject, input, signal } from '@angular/core';
import { forkJoin } from 'rxjs';

import { SessionStore } from '../../core/auth/session.store';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { BillingApiService, Plan, Subscription } from './billing-api.service';

@Component({
  selector: 'app-billing-page',
  imports: [ErrorBannerComponent, PageHeaderComponent],
  templateUrl: './billing.page.html',
})
export class BillingPage extends BasePage implements OnInit {
  /** `?status=success|cancelled` after returning from checkout. */
  readonly status = input<string>();

  private readonly api = inject(BillingApiService);
  protected readonly session = inject(SessionStore);
  protected readonly plans = signal<Plan[]>([]);
  protected readonly subscription = signal<Subscription | null>(null);

  ngOnInit(): void {
    this.run(forkJoin([this.api.plans(), this.api.subscription(), this.session.refresh()]), ([plans, subscription]) => {
      this.plans.set(plans);
      this.subscription.set(subscription);
    });
  }

  protected upgrade(plan: Plan): void {
    this.run(this.api.checkout(plan.code), ({ url }) => location.assign(url));
  }

  protected manage(): void {
    this.run(this.api.portal(), ({ url }) => location.assign(url));
  }
}
