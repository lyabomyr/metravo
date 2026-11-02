import { Component, inject } from '@angular/core';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { ExportApiService } from './export-api.service';

/** "My data": the user's listings as a spreadsheet, for their own analysis. */
@Component({
  selector: 'app-database-page',
  imports: [ErrorBannerComponent, PageHeaderComponent, TranslatePipe],
  templateUrl: './database.page.html',
})
export class DatabasePage extends BasePage {
  private readonly exports = inject(ExportApiService);

  protected downloadCsv(): void {
    this.run(this.exports.downloadListingsCsv());
  }
}
