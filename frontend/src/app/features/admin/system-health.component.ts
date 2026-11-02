import { DecimalPipe, KeyValuePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';

import { WhenPipe } from '../../core/i18n/format.pipes';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { AdminApiService, SystemHealth } from './admin-api.service';

/** Health of the API instance: the same numbers the monitor alerts on, plus recent warnings. Admin-only, English. */
@Component({
  selector: 'app-system-health',
  imports: [DecimalPipe, KeyValuePipe, ErrorBannerComponent, WhenPipe],
  template: `
    <section class="card stack" style="margin-bottom: 16px" data-cy="system-health">
      <div class="row row--between">
        <h2>System</h2>
        <button class="button button--small" type="button" (click)="load()" [disabled]="loading()">Refresh</button>
      </div>
      <app-error-banner [error]="error()" />
      @if (health(); as health) {
        <div class="grid">
          <div class="meter" [class.meter--bad]="(health.memory_percent ?? 0) >= 80" data-cy="memory">
            <span class="muted small">Memory</span>
            <b>{{ health.memory_percent ?? '—' }}%</b>
            <span class="muted small">{{ health.memory_used_mb }} of {{ health.memory_limit_mb ?? '?' }} MB</span>
            <progress max="100" [value]="health.memory_percent ?? 0"></progress>
          </div>
          <div class="meter" [class.meter--bad]="(health.cpu_percent ?? 0) >= 80" data-cy="cpu">
            <span class="muted small">CPU (of the limit)</span>
            <b>{{ health.cpu_percent ?? '—' }}%</b>
            <span class="muted small">up {{ health.uptime_seconds / 3600 | number: '1.0-1' }} h</span>
            <progress max="100" [value]="health.cpu_percent ?? 0"></progress>
          </div>
          <div class="meter">
            <span class="muted small">Last scan</span>
            @if (health.last_scan_failed) {
              <b class="danger">crashed</b><span class="small">{{ health.last_scan_failed }}</span>
            } @else if (health.last_scan; as scan) {
              <b>{{ scan.searches_scanned }} searches · {{ scan.new_listings }} new</b>
              <span class="small muted">{{ scan.errors.length ? scan.errors.join('; ') : 'no portal errors' }}</span>
            } @else {
              <b>—</b><span class="small muted">not since start</span>
            }
          </div>
        </div>
        <div data-cy="alerts">
          <h3 class="section-title">Active alerts</h3>
          <div class="list">
            @for (alert of health.active_alerts | keyvalue; track alert.key) {
              <div class="list__row">🚨 {{ alert.value }}</div>
            } @empty {
              <div class="list__row muted">✅ None — memory, CPU, scans and portals are fine.</div>
            }
          </div>
        </div>
        <div>
          <h3 class="section-title">Recent warnings and errors</h3>
          <div class="list log">
            @for (entry of health.recent_logs; track $index) {
              <div class="list__row list__row--stacked">
                <span class="small"><b [class.danger]="entry.level === 'ERROR'">{{ entry.level }}</b> · {{ entry.at | when }} · {{ entry.logger }}</span>
                <code>{{ entry.message }}</code>
              </div>
            } @empty {
              <div class="list__row muted">Nothing logged.</div>
            }
          </div>
        </div>
      }
    </section>
  `,
  styles: `
    .meter { display: grid; gap: 4px; padding: 14px; border-radius: 14px; background: var(--fill); }
    .meter b { font-size: 22px; }
    .meter progress { width: 100%; accent-color: var(--success); }
    .meter--bad progress { accent-color: var(--danger); }
    .danger { color: var(--danger); }
    .log { max-height: 320px; overflow-y: auto; }
  `,
})
export class SystemHealthComponent extends BasePage implements OnInit {
  private readonly api = inject(AdminApiService);
  protected readonly health = signal<SystemHealth | null>(null);

  ngOnInit(): void {
    this.load();
  }

  protected load(): void {
    this.run(this.api.system(), (health) => this.health.set(health));
  }
}
