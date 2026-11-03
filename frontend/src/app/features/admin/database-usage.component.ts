import { DecimalPipe } from '@angular/common';
import { Component, OnInit, computed, inject, signal } from '@angular/core';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { AdminApiService, TableUsage } from './admin-api.service';

/** What fills the database: each table with its rows and size, the biggest first. */
@Component({
  selector: 'app-database-usage',
  imports: [DecimalPipe, ErrorBannerComponent, TranslatePipe],
  template: `
    <section class="card stack" style="margin-bottom: 16px" data-cy="database-usage">
      <div class="row row--between">
        <h2>{{ 'admin.database' | t }}</h2>
        <b data-cy="database-total">{{ totalMb() === null ? '' : (totalMb() | number: '1.1-1') + ' MB' }}</b>
      </div>
      <app-error-banner [error]="error()" />
      <div class="list">
        @for (table of tables(); track table.name) {
          <div class="list__row" data-cy="database-table">
            <span>{{ table.name }}</span>
            <span class="muted small">
              {{ 'admin.rows' | t: { n: (table.rows | number) ?? '0' } }}{{ table.bytes === null ? '' : ' · ' + (table.bytes / 1e6 | number: '1.2-2') + ' MB' }}
            </span>
          </div>
        }
      </div>
      <p class="section-note">{{ 'admin.databaseHint' | t }}</p>
    </section>
  `,
})
export class DatabaseUsageComponent extends BasePage implements OnInit {
  private readonly api = inject(AdminApiService);
  protected readonly tables = signal<TableUsage[]>([]);
  /** Null when the engine does not report sizes, only rows. */
  protected readonly totalMb = computed(() => {
    const sized = this.tables().filter((table) => table.bytes !== null);
    return sized.length ? sized.reduce((sum, table) => sum + (table.bytes ?? 0), 0) / 1e6 : null;
  });

  ngOnInit(): void {
    this.run(this.api.database(), (tables) => this.tables.set(tables));
  }
}
