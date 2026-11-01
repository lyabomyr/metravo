import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { DatabaseApiService, DatabaseCredentials, DatabaseInfo } from './database-api.service';
import { ExportApiService } from './export-api.service';

@Component({
  selector: 'app-database-page',
  imports: [DatePipe, RouterLink, ErrorBannerComponent, PageHeaderComponent],
  templateUrl: './database.page.html',
})
export class DatabasePage extends BasePage implements OnInit {
  private readonly database = inject(DatabaseApiService);
  private readonly exports = inject(ExportApiService);

  protected readonly info = signal<DatabaseInfo | null>(null);
  protected readonly credentials = signal<DatabaseCredentials | null>(null);

  ngOnInit(): void {
    this.run(this.database.info(), (info) => this.info.set(info));
  }

  protected downloadDatabase(): void {
    this.run(this.exports.downloadDatabase());
  }

  protected downloadCsv(): void {
    this.run(this.exports.downloadListingsCsv());
  }

  protected showCredentials(readOnly: boolean): void {
    this.run(this.database.credentials(readOnly), (credentials) => this.credentials.set(credentials));
  }
}
