import { Component, effect, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { SessionStore } from './core/auth/session.store';
import { I18nService } from './core/i18n/i18n.service';
import { LanguageSwitcherComponent } from './core/i18n/language-switcher.component';
import { TranslatePipe } from './core/i18n/translate.pipe';
import { IntroTourComponent } from './features/intro/intro-tour.component';
import { IntroService } from './features/intro/intro.service';
import { FreeWeekBannerComponent } from './features/billing/free-week-banner.component';
import { ConnectReminderComponent } from './features/telegram/connect-reminder.component';

@Component({
  selector: 'app-root',
  imports: [
    RouterOutlet, RouterLink, RouterLinkActive, ConnectReminderComponent, FreeWeekBannerComponent, IntroTourComponent, LanguageSwitcherComponent, TranslatePipe,
  ],
  templateUrl: './app.html',
})
export class App {
  protected readonly session = inject(SessionStore);
  protected readonly intro = inject(IntroService);
  private readonly i18n = inject(I18nService);
  private readonly router = inject(Router);

  constructor() {
    // Signed in: Telegram messages follow the website's language, and the tour greets first-timers.
    effect(() => {
      if (!this.session.user()) return;
      this.session.syncLocale(this.i18n.locale());
      this.intro.openIfFirstVisit();
    });
  }

  protected signOut(): void {
    this.session.signOut();
    this.router.navigateByUrl('/');
  }
}
