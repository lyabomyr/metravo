import { Component, OnInit, inject, signal } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { SearchDraft } from '../searches/search.model';
import { SearchFormComponent } from '../searches/search-form.component';
import { SearchesApiService } from '../searches/searches-api.service';
import { TelegramApiService } from '../telegram/telegram-api.service';
import { TelegramConnectComponent } from '../telegram/telegram-connect.component';

/**
 * Setup: a search (click 1), then Telegram (click 2, then Start there). Every
 * sign-in lands here and it skips what is already done, so an account that
 * was created but never finished setup is taken through the rest. Once
 * Telegram connects, the server sends what it has found and scans at once.
 */
@Component({
  selector: 'app-onboarding-page',
  imports: [RouterLink, ErrorBannerComponent, PageHeaderComponent, SearchFormComponent, TelegramConnectComponent, TranslatePipe],
  template: `
    <app-page-header [title]="'onboarding.title' | t" [subtitle]="'onboarding.subtitle' | t" />
    <app-error-banner [error]="error()" />

    @if (ready()) {
      <div class="steps">
        <section class="card stack step" [class.step--done]="searchSaved()">
          <h2><span class="step__number">{{ searchSaved() ? '✓' : '1' }}</span>{{ 'onboarding.step1' | t }}</h2>
          @if (!searchSaved()) {
            <app-search-form [submitLabel]="'onboarding.saveContinue' | t" [busy]="loading()" (saved)="saveSearch($event)" />
          } @else {
            <p class="muted" data-cy="onboarding-search-saved">{{ 'onboarding.saved' | t }}</p>
          }
        </section>

        <section class="card stack step" [class.step--done]="connected()">
          <h2><span class="step__number">{{ connected() ? '✓' : '2' }}</span>{{ 'onboarding.step2' | t }}</h2>
          @if (connected()) {
            <p data-cy="onboarding-done">{{ 'onboarding.done' | t }}</p>
            <a class="button button--primary" routerLink="/listings" data-cy="onboarding-listings">{{ 'onboarding.seeListings' | t }}</a>
          } @else if (searchSaved()) {
            <app-telegram-connect (connected)="connected.set(true)" />
          } @else {
            <p class="muted">{{ 'onboarding.saveFirst' | t }}</p>
          }
        </section>
      </div>
    } @else {
      <p class="muted"><span class="spinner"></span></p>
    }
  `,
})
export class OnboardingPage extends BasePage implements OnInit {
  private readonly searches = inject(SearchesApiService);
  private readonly telegram = inject(TelegramApiService);
  private readonly router = inject(Router);
  protected readonly ready = signal(false);
  protected readonly searchSaved = signal(false);
  protected readonly connected = signal(false);

  ngOnInit(): void {
    this.run(forkJoin({ searches: this.searches.list(), chats: this.telegram.chats() }), ({ searches, chats }) => {
      if (searches.length && chats.length) {
        this.router.navigateByUrl('/listings', { replaceUrl: true });
        return;
      }
      this.searchSaved.set(searches.length > 0);
      this.connected.set(chats.length > 0);
      this.ready.set(true);
    });
  }

  protected saveSearch(draft: SearchDraft): void {
    this.run(this.searches.create(draft), () => this.searchSaved.set(true));
  }
}
