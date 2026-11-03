import { Component, OnInit, inject, signal } from '@angular/core';

import { WhenPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { AdminApiService, MailAlertStatus } from './admin-api.service';

/** OLX and Otodom offers that arrive as the portals' own alert emails: is the mailbox read, and what came in. */
@Component({
  selector: 'app-mail-alerts',
  imports: [ErrorBannerComponent, TranslatePipe, WhenPipe],
  template: `
    <section class="card stack" style="margin-bottom: 16px" data-cy="mail-alerts">
      <div class="row row--between">
        <h2>{{ 'admin.mail.title' | t }}</h2>
        @if (status()?.state !== 'off') {
          <button class="button button--small" type="button" (click)="check()" [disabled]="loading()" data-cy="mail-check">
            {{ 'admin.mail.check' | t }}
          </button>
        }
      </div>
      <app-error-banner [error]="error()" />
      @if (status(); as status) {
        @if (status.state === 'off') {
          <p class="muted" data-cy="mail-off">{{ 'admin.mail.off' | t }}</p>
        } @else {
          <div class="list">
            <div class="list__row"><span>{{ 'admin.mail.mailbox' | t }}</span><span class="muted small" data-cy="mail-mailbox">{{ status.mailbox }}</span></div>
            <div class="list__row"><span>{{ 'admin.mail.owner' | t }}</span><span class="muted small">{{ status.owner }}</span></div>
            <div class="list__row">
              <span>{{ 'admin.lastScan' | t }}</span>
              <span class="small" [class.danger]="status.state === 'error'" data-cy="mail-last">
                @if (status.state === 'error') {
                  {{ status.error }}
                } @else if (status.checked_at) {
                  {{ 'admin.mail.last' | t: { mails: status.mails, offers: status.offers, fresh: status.new, sent: status.sent } }} · {{ status.checked_at | when }}
                } @else {
                  {{ 'admin.notSinceStart' | t }}
                }
              </span>
            </div>
            <div class="list__row">
              <span>{{ 'admin.mail.total' | t }}</span>
              <span class="muted small" data-cy="mail-total">{{ 'admin.mail.last' | t: { mails: status.totals.mails, offers: status.totals.offers, fresh: status.totals.new, sent: status.totals.sent } }}</span>
            </div>
          </div>
        }
      }
      <p class="section-note">{{ 'admin.mail.hint' | t }}</p>
    </section>
  `,
})
export class MailAlertsComponent extends BasePage implements OnInit {
  private readonly api = inject(AdminApiService);
  protected readonly status = signal<MailAlertStatus | null>(null);

  ngOnInit(): void {
    this.run(this.api.mailAlerts(), (status) => this.status.set(status));
  }

  protected check(): void {
    this.run(this.api.checkMailAlerts(), (status) => this.status.set(status));
  }
}
