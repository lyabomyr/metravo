import { Component } from '@angular/core';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { TelegramChannelComponent } from '../telegram/telegram-channel.component';
import { ChannelSettingsComponent } from './channel-settings.component';

/** Where listings go: one list of channels, Telegram among them. */
@Component({
  selector: 'app-alerts-page',
  imports: [ChannelSettingsComponent, PageHeaderComponent, TelegramChannelComponent, TranslatePipe],
  template: `
    <app-page-header [title]="'alerts.title' | t" [subtitle]="'alerts.subtitle' | t" />
    <app-channel-settings>
      <app-telegram-channel />
    </app-channel-settings>
  `,
})
export class AlertsPage {}
