import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { I18nService } from '../../core/i18n/i18n.service';
import { MoneyPipe, WhenPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { IntervalPipe } from './interval.pipe';
import { DEAL_LABEL, PROPERTY_LABEL, Search, outcomeReason } from './search.model';
import { SearchesApiService } from './searches-api.service';

@Component({
  selector: 'app-searches-page',
  imports: [RouterLink, ErrorBannerComponent, PageHeaderComponent, IntervalPipe, MoneyPipe, TranslatePipe, WhenPipe],
  templateUrl: './searches.page.html',
})
export class SearchesPage extends BasePage implements OnInit {
  protected readonly dealLabel = DEAL_LABEL;
  protected readonly propertyLabel = PROPERTY_LABEL;
  private readonly i18n = inject(I18nService);
  private readonly api = inject(SearchesApiService);
  protected readonly searches = signal<Search[]>([]);
  protected readonly outcomeReason = outcomeReason;

  ngOnInit(): void {
    this.load();
  }

  protected remove(search: Search): void {
    if (!confirm(this.i18n.t('searches.confirmDelete', { name: search.name }))) return;
    this.run(this.api.remove(search.id), () => this.load());
  }

  private load(): void {
    this.run(this.api.list(), (searches) => this.searches.set(searches));
  }
}
