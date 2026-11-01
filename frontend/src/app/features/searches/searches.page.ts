import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { Search, describeInterval } from './search.model';
import { SearchesApiService } from './searches-api.service';

@Component({
  selector: 'app-searches-page',
  imports: [RouterLink, DatePipe, DecimalPipe, ErrorBannerComponent, PageHeaderComponent],
  templateUrl: './searches.page.html',
})
export class SearchesPage extends BasePage implements OnInit {
  protected readonly describe = describeInterval;
  private readonly api = inject(SearchesApiService);
  protected readonly searches = signal<Search[]>([]);

  ngOnInit(): void {
    this.load();
  }

  protected remove(search: Search): void {
    if (!confirm(`Delete “${search.name}”?`)) return;
    this.run(this.api.remove(search.id), () => this.load());
  }

  private load(): void {
    this.run(this.api.list(), (searches) => this.searches.set(searches));
  }
}
