import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { SessionStore } from '../../core/auth/session.store';
import { PublicConfigService } from '../../core/config/public-config.service';
import { DEFAULT_BUDGET, DEFAULT_SEARCH, DealType, PropertyType, SearchDraft, describeInterval } from './search.model';

/** The one search form, used by the editor and the onboarding wizard alike. */
@Component({
  selector: 'app-search-form',
  imports: [ReactiveFormsModule],
  templateUrl: './search-form.component.html',
})
export class SearchFormComponent {
  readonly value = input<SearchDraft>(DEFAULT_SEARCH);
  readonly submitLabel = input('Save');
  readonly busy = input(false);
  readonly saved = output<SearchDraft>();

  protected readonly config = inject(PublicConfigService).value;
  protected readonly form = inject(FormBuilder).nonNullable.group({
    name: ['', Validators.required],
    city: ['', Validators.required],
    deal_type: ['sale' as DealType],
    property_type: ['flat' as PropertyType],
    min_price: [null as number | null],
    max_price: [0, [Validators.required, Validators.min(1)]],
    min_area: [0, [Validators.required, Validators.min(1)]],
    max_area: [null as number | null],
    min_rooms: [null as number | null],
    max_rooms: [null as number | null],
    max_price_per_m2: [null as number | null],
    min_build_year: [null as number | null],
    required_keywords: [''],
    interval_minutes: [DEFAULT_SEARCH.interval_minutes],
    enabled: [true],
  });
  protected readonly selectedSources = signal(new Set<string>());
  protected readonly describe = describeInterval;
  private readonly session = inject(SessionStore);
  /** The most often the user's plan may scan; faster options are shown but locked. */
  protected readonly planFloor = computed(() => this.config.plan_min_intervals[this.session.user()?.plan ?? 'free'] ?? 0);
  private readonly dealType = toSignal(this.form.controls.deal_type.valueChanges, { initialValue: 'sale' as DealType });
  private readonly propertyType = toSignal(this.form.controls.property_type.valueChanges, { initialValue: 'flat' as PropertyType });

  constructor() {
    effect(() => {
      const value = this.value();
      this.form.reset({ ...value, required_keywords: value.required_keywords.join(', ') });
      this.selectedSources.set(new Set(value.sources));
    });
    // Switching between buying and renting swaps in a budget of the right size.
    this.form.controls.deal_type.valueChanges.pipe(takeUntilDestroyed()).subscribe((deal) => {
      const budget = this.form.controls.max_price.value;
      const looksLikeOtherDeal = deal === 'rent' ? budget > 50000 : budget <= 50000;
      if (looksLikeOtherDeal) this.form.controls.max_price.setValue(DEFAULT_BUDGET[deal]);
    });
  }

  /** Can this portal search the chosen deal and property type? */
  protected supports(source: string): boolean {
    const capabilities = this.config.source_capabilities[source] ?? [];
    return capabilities.some((c) => c.deal_type === this.dealType() && c.property_type === this.propertyType());
  }

  protected toggleSource(source: string, checked: boolean): void {
    const next = new Set(this.selectedSources());
    if (checked) next.add(source);
    else next.delete(source);
    this.selectedSources.set(next);
  }

  protected submit(): void {
    if (this.form.invalid) return;
    const { required_keywords, ...values } = this.form.getRawValue();
    this.saved.emit({
      ...values,
      required_keywords: required_keywords.split(',').map((word) => word.trim()).filter(Boolean),
      sources: [...this.selectedSources()].filter((source) => this.supports(source)),
    });
  }
}
