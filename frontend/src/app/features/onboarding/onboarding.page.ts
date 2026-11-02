import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { SearchDraft } from '../searches/search.model';
import { SearchFormComponent } from '../searches/search-form.component';
import { SearchesApiService } from '../searches/searches-api.service';
import { TelegramConnectComponent } from '../telegram/telegram-connect.component';

/**
 * First run: save a pre-filled search (click 1), open Telegram (click 2),
 * press Start there. Defaults are sensible, so most people change nothing.
 */
@Component({
  selector: 'app-onboarding-page',
  imports: [RouterLink, ErrorBannerComponent, PageHeaderComponent, SearchFormComponent, TelegramConnectComponent, TranslatePipe],
  template: `
    <app-page-header [title]="'onboarding.title' | t" [subtitle]="'onboarding.subtitle' | t" />
    <app-error-banner [error]="error()" />

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
          <p data-cy="onboarding-done">{{ 'onboarding.done' | t }} <a routerLink="/listings">{{ 'onboarding.seeListings' | t }}</a></p>
        } @else if (searchSaved()) {
          <app-telegram-connect (connected)="connected.set(true)" />
        } @else {
          <p class="muted">{{ 'onboarding.saveFirst' | t }}</p>
        }
      </section>
    </div>
  `,
})
export class OnboardingPage extends BasePage {
  private readonly searches = inject(SearchesApiService);
  protected readonly searchSaved = signal(false);
  protected readonly connected = signal(false);

  protected saveSearch(draft: SearchDraft): void {
    this.run(this.searches.create(draft), () => this.searchSaved.set(true));
  }
}
