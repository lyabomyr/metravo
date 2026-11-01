import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

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
  imports: [RouterLink, ErrorBannerComponent, PageHeaderComponent, SearchFormComponent, TelegramConnectComponent],
  template: `
    <app-page-header title="Welcome to Metravo" subtitle="Two steps and new flats start arriving in Telegram." />
    <app-error-banner [error]="error()" />

    <div class="steps">
      <section class="card stack step" [class.step--done]="searchSaved()">
        <h2><span class="step__number">{{ searchSaved() ? '✓' : '1' }}</span>What are you looking for?</h2>
        @if (!searchSaved()) {
          <app-search-form submitLabel="Save and continue" [busy]="loading()" (saved)="saveSearch($event)" />
        } @else {
          <p class="muted" data-cy="onboarding-search-saved">Saved. You can fine-tune it later under Searches.</p>
        }
      </section>

      <section class="card stack step" [class.step--done]="connected()">
        <h2><span class="step__number">{{ connected() ? '✓' : '2' }}</span>Connect Telegram</h2>
        @if (connected()) {
          <p data-cy="onboarding-done">All set! <a routerLink="/listings">See your listings →</a></p>
        } @else if (searchSaved()) {
          <app-telegram-connect (connected)="connected.set(true)" />
        } @else {
          <p class="muted">Save your search first.</p>
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
