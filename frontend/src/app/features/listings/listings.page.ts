import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';
import { forkJoin } from 'rxjs';

import { MoneyPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { ListingCardComponent } from './listing-card.component';
import { Listing, PriceChange, ScanReport } from './listing.model';
import { ListingsApiService } from './listings-api.service';
import { ScanApiService } from './scan-api.service';

@Component({
  selector: 'app-listings-page',
  imports: [RouterLink, ErrorBannerComponent, PageHeaderComponent, ListingCardComponent, MoneyPipe, TranslatePipe],
  templateUrl: './listings.page.html',
})
export class ListingsPage extends BasePage implements OnInit {
  private readonly listingsApi = inject(ListingsApiService);
  private readonly scanApi = inject(ScanApiService);

  protected readonly listings = signal<Listing[]>([]);
  protected readonly priceChanges = signal<PriceChange[]>([]);
  protected readonly lastScan = signal<ScanReport | null>(null);

  ngOnInit(): void {
    this.load();
  }

  protected scanNow(): void {
    this.run(this.scanApi.scanMine(), (report) => {
      this.lastScan.set(report);
      this.load();
    });
  }

  private load(): void {
    this.run(forkJoin([this.listingsApi.latest(), this.listingsApi.priceChanges()]), ([listings, changes]) => {
      this.listings.set(listings);
      this.priceChanges.set(changes);
    });
  }
}
