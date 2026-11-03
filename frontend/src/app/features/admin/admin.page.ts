import { KeyValuePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { forkJoin } from 'rxjs';

import { User } from '../../core/auth/auth.models';
import { WhenPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { ScanReport } from '../listings/listing.model';
import { ScanApiService } from '../listings/scan-api.service';
import { AdminApiService, Overview } from './admin-api.service';
import { DatabaseUsageComponent } from './database-usage.component';
import { SystemHealthComponent } from './system-health.component';

/** Service management: accounts and plans. Never shows anyone's searches or listings. */
@Component({
  selector: 'app-admin-page',
  imports: [KeyValuePipe, ErrorBannerComponent, PageHeaderComponent, SystemHealthComponent, DatabaseUsageComponent, TranslatePipe, WhenPipe],
  templateUrl: './admin.page.html',
})
export class AdminPage extends BasePage implements OnInit {
  private readonly api = inject(AdminApiService);
  private readonly scanApi = inject(ScanApiService);

  protected readonly overview = signal<Overview | null>(null);
  protected readonly users = signal<User[]>([]);
  protected readonly scanReport = signal<ScanReport | null>(null);

  ngOnInit(): void {
    this.load();
  }

  protected setPlan(user: User, plan: string): void {
    this.run(this.api.setPlan(user.id, plan), () => this.load());
  }

  protected scanAll(): void {
    this.run(this.scanApi.scanAll(), (report) => this.scanReport.set(report));
  }

  private load(): void {
    this.run(forkJoin([this.api.overview(), this.api.users()]), ([overview, users]) => {
      this.overview.set(overview);
      this.users.set(users);
    });
  }
}
