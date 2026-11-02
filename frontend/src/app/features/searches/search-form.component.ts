import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { SessionStore } from '../../core/auth/session.store';
import { PublicConfigService } from '../../core/config/public-config.service';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { IntervalPipe } from './interval.pipe';
import { PlacePickerComponent } from './place-picker.component';
import { DEFAULT_SEARCH, DealType, KRAKOW, Place, PropertyType, SearchDraft } from './search.model';

/** The one search form, used by the editor and the onboarding wizard alike. */
@Component({
  selector: 'app-search-form',
  imports: [ReactiveFormsModule, IntervalPipe, PlacePickerComponent, TranslatePipe],
  templateUrl: './search-form.component.html',
  styles: `
    .words { text-align: left; }
  `,
})
export class SearchFormComponent {
  readonly value = input<SearchDraft>(DEFAULT_SEARCH);
  /** Empty = the translated “Save”. */
  readonly submitLabel = input('');
  readonly busy = input(false);
  readonly saved = output<SearchDraft>();

  protected readonly config = inject(PublicConfigService).value;
  protected readonly form = inject(FormBuilder).nonNullable.group({
    name: ['', Validators.required],
    place: [KRAKOW as Place],
    radius_km: [0],
    deal_type: ['sale' as DealType],
    property_type: ['flat' as PropertyType],
    min_price: [null as number | null],
    max_price: [null as number | null, Validators.min(1)],
    min_area: [null as number | null, Validators.min(1)],
    max_area: [null as number | null],
    min_rooms: [null as number | null],
    max_rooms: [null as number | null],
    max_price_per_m2: [null as number | null],
    min_build_year: [null as number | null],
    required_keywords: [''],
    reject_keywords: [''],
    interval_minutes: [DEFAULT_SEARCH.interval_minutes],
    enabled: [true],
  });
  protected readonly selectedSources = signal(new Set<string>());
  private readonly session = inject(SessionStore);
  /** The most often the user's plan may scan; faster options are shown but locked. */
  protected readonly planFloor = computed(() => this.config.plan_min_intervals[this.session.user()?.plan ?? 'free'] ?? 0);
  private readonly dealType = toSignal(this.form.controls.deal_type.valueChanges, { initialValue: 'sale' as DealType });
  private readonly propertyType = toSignal(this.form.controls.property_type.valueChanges, { initialValue: 'flat' as PropertyType });

  constructor() {
    effect(() => {
      const value = this.value();
      const reject = value.reject_keywords ?? this.config.default_reject_keywords;
      this.form.reset({ ...value, required_keywords: value.required_keywords.join(', '), reject_keywords: reject.join(', ') });
      // A new search starts with every portal the plan includes: track everything, narrow later.
      const sources = value.sources.length ? value.sources : this.config.sources.filter((source) => this.planAllows(source));
      this.selectedSources.set(new Set(sources));
    });
    // A sale price makes no sense as a monthly rent and back: switching clears prices of the wrong size.
    this.form.controls.deal_type.valueChanges.pipe(takeUntilDestroyed()).subscribe((deal) => {
      for (const control of [this.form.controls.max_price, this.form.controls.min_price]) {
        const price = control.value;
        if (price !== null && (deal === 'rent' ? price > 50000 : price <= 50000)) control.setValue(null);
      }
    });
  }

  /** Can this portal search the chosen deal and property type? */
  protected supports(source: string): boolean {
    const capabilities = this.config.source_capabilities[source] ?? [];
    return capabilities.some((c) => c.deal_type === this.dealType() && c.property_type === this.propertyType());
  }

  /** A portal outside the user's plan gets a Pro badge; the backend refuses it on save. */
  protected planAllows(source: string): boolean {
    return (this.config.plan_sources[this.session.user()?.plan ?? 'free'] ?? []).includes(source);
  }

  protected toggleSource(source: string, checked: boolean): void {
    const next = new Set(this.selectedSources());
    if (checked) next.add(source);
    else next.delete(source);
    this.selectedSources.set(next);
  }

  protected submit(): void {
    if (this.form.invalid) return;
    const { required_keywords, reject_keywords, ...values } = this.form.getRawValue();
    this.saved.emit({
      ...values,
      required_keywords: words(required_keywords),
      reject_keywords: words(reject_keywords),
      sources: [...this.selectedSources()].filter((source) => this.supports(source)),
    });
  }
}

function words(text: string): string[] {
  return text.split(',').map((word) => word.trim()).filter(Boolean);
}
