import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { ChannelSetting, NotificationsApiService } from './notifications-api.service';

/** WhatsApp, Viber, Signal, email: tick to get the same listings there too. Pro only. */
@Component({
  selector: 'app-channel-settings',
  imports: [FormsModule, RouterLink, ErrorBannerComponent, TranslatePipe],
  template: `
    <h3 class="section-title">{{ 'alerts.more' | t }}</h3>
    <app-error-banner [error]="error()" />
    <div class="list">
      @for (channel of others(); track channel.code) {
        <div class="list__row list__row--stacked" [class.list__row--disabled]="!channel.allowed" [attr.data-cy]="'channel-' + channel.code">
          <label class="row row--between">
            <span class="row">
              {{ channel.name }}
              @if (!channel.allowed) {
                <a class="badge badge--pro" routerLink="/billing">{{ 'common.pro' | t }}</a>
              } @else if (!channel.live) {
                <span class="badge">{{ 'common.soon' | t }}</span>
              }
            </span>
            <input
              class="switch"
              type="checkbox"
              [checked]="channel.enabled"
              [disabled]="!channel.allowed"
              (change)="toggle(channel, $any($event.target).checked)"
              [attr.data-cy]="'channel-toggle-' + channel.code"
            />
          </label>
          @if (channel.enabled && channel.address_kind) {
            <input
              [type]="channel.address_kind === 'email' ? 'email' : 'tel'"
              [placeholder]="(channel.address_kind === 'email' ? 'alerts.emailAddress' : 'alerts.phone') | t"
              [(ngModel)]="channel.address"
              (blur)="save(channel)"
              [attr.data-cy]="'channel-address-' + channel.code"
            />
          }
        </div>
      }
    </div>
    <p class="section-note">{{ 'alerts.moreHint' | t }}</p>
    @if (saved()) {
      <p class="section-note" data-cy="channel-saved">✓ {{ 'alerts.saved' | t }}</p>
    }
  `,
})
export class ChannelSettingsComponent extends BasePage implements OnInit {
  private readonly api = inject(NotificationsApiService);
  protected readonly others = signal<ChannelSetting[]>([]);
  protected readonly saved = signal(false);

  ngOnInit(): void {
    this.run(this.api.channels(), (channels) => this.others.set(channels.filter((channel) => channel.code !== 'telegram')));
  }

  protected toggle(channel: ChannelSetting, enabled: boolean): void {
    channel.enabled = enabled;
    this.others.set([...this.others()]);
    // A channel that needs an address is saved once the address is typed.
    if (!enabled || !channel.address_kind || channel.address) this.save(channel);
  }

  protected save(channel: ChannelSetting): void {
    this.saved.set(false);
    this.run(this.api.update(channel.code, channel.enabled, channel.address), (updated) => {
      this.others.set(this.others().map((item) => (item.code === updated.code ? updated : item)));
      this.saved.set(true);
    });
  }
}
