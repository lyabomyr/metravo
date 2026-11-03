import { Component, computed, effect, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed, toSignal } from '@angular/core/rxjs-interop';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { SessionStore } from '../../core/auth/session.store';
import { PublicConfigService } from '../../core/config/public-config.service';
import { SourcesPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { IntervalPipe } from './interval.pipe';
import { PlacePickerComponent } from './place-picker.component';
import { DEFAULT_SEARCH, DealType, FLOORS, Market, PROPERTY_LABEL, PROPERTY_TYPES, Place, PropertyType, SearchDraft, SearchFormValue, isHome } from './search.model';

/** The one search form, used by the editor and the onboarding wizard alike. */
@Component({
  selector: 'app-search-form',
  imports: [ReactiveFormsModule, IntervalPipe, PlacePickerComponent, SourcesPipe, TranslatePipe],
  templateUrl: './search-form.component.html',
})
export class SearchFormComponent {
  readonly value = input<SearchFormValue>(DEFAULT_SEARCH);
  /** Empty = the translated “Save”. */
  readonly submitLabel = input('');
  readonly busy = input(false);
  readonly saved = output<SearchDraft>();

  protected readonly config = inject(PublicConfigService).value;
  protected readonly form = inject(FormBuilder).nonNullable.group({
    name: [''],
    place: [null as Place | null, Validators.required],
    radius_km: [0],
    more_places: [[] as Place[]],
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
    market: [null as Market | null],
    private_only: [false],
    min_floor: [null as number | null],
    max_floor: [null as number | null],
  });
  protected readonly floors = FLOORS;
  protected readonly propertyTypes = PROPERTY_TYPES;
  protected readonly propertyLabel = PROPERTY_LABEL;
  protected readonly isHome = isHome;
  protected readonly selectedSources = signal(new Set<string>());
  private readonly session = inject(SessionStore);
  /** The most often the user's plan may scan; faster options are shown but locked. */
  protected readonly planFloor = computed(() => this.config.plan_min_intervals[this.session.user()?.plan ?? 'free'] ?? 0);
  protected readonly dealType = toSignal(this.form.controls.deal_type.valueChanges, { initialValue: 'sale' as DealType });
  private readonly rejectWords = toSignal(this.form.controls.reject_keywords.valueChanges, { initialValue: '' });
  /** Still the server's suggested words: shown grey, so it is clear they stay unless edited. */
  protected readonly rejectIsSuggested = computed(
    () => sameWords(words(this.rejectWords()), this.config.default_reject_keywords),
  );
  protected readonly propertyType = toSignal(this.form.controls.property_type.valueChanges, { initialValue: 'flat' as PropertyType });
  private readonly market = toSignal(this.form.controls.market.valueChanges, { initialValue: null as Market | null });
  private readonly privateOnly = toSignal(this.form.controls.private_only.valueChanges, { initialValue: false });
  /** Floors run from the ground up; "up to" never sits below "from". */
  protected readonly lowestFloor = toSignal(this.form.controls.min_floor.valueChanges, { initialValue: null as number | null });

  constructor() {
    effect(() => {
      const value = this.value();
      const reject = value.reject_keywords ?? this.config.default_reject_keywords;
      this.form.reset({ ...value, required_keywords: value.required_keywords.join(', '), reject_keywords: reject.join(', ') });
      // A new search starts with every portal the plan includes: track everything, narrow later.
      const sources = value.sources.length ? value.sources : this.config.sources.filter((source) => this.planAllows(source));
      this.selectedSources.set(new Set(sources));
    });
    // Rooms are only rented and plots only sold: picking one sets the deal, and the other deal sets a flat.
    this.form.controls.property_type.valueChanges.pipe(takeUntilDestroyed()).subscribe((kind) => {
      const deal = kind === 'room' ? 'rent' : kind === 'plot' ? 'sale' : null;
      if (deal && this.form.controls.deal_type.value !== deal) this.form.controls.deal_type.setValue(deal);
    });
    this.form.controls.deal_type.valueChanges.pipe(takeUntilDestroyed()).subscribe((deal) => {
      const kind = this.form.controls.property_type.value;
      if ((deal === 'sale' && kind === 'room') || (deal === 'rent' && kind === 'plot')) this.form.controls.property_type.setValue('flat');
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
    return capabilities.some((c) => c.deal_type === this.dealType() && c.property_type === this.propertyType()) && this.filters(source);
  }

  /** Can this portal show only the chosen market and only private sellers? If not, it sits the search out. */
  protected filters(source: string): boolean {
    const filters = this.config.source_filters?.[source] ?? [];
    const market = this.dealType() === 'sale' ? this.market() : null;
    return (!market || filters.includes(`market:${market}`)) && (!this.privateOnly() || filters.includes('private'));
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
    const { required_keywords, reject_keywords, name, place, ...values } = this.form.getRawValue();
    if (!place) return;
    this.saved.emit({
      ...values,
      place,
      // Left empty, the search is called after its place ("Zabierzów").
      name: name.trim() || place.name,
      required_keywords: words(required_keywords),
      reject_keywords: words(reject_keywords),
      // Sent as chosen; the server drops floors for a house and the market for a rental.
      sources: [...this.selectedSources()].filter((source) => this.supports(source)),
    });
  }
}

function words(text: string): string[] {
  return text.split(',').map((word) => word.trim()).filter(Boolean);
}

function sameWords(a: string[], b: string[]): boolean {
  const lower = (list: string[]) => list.map((word) => word.toLowerCase()).sort().join('|');
  return a.length > 0 && lower(a) === lower(b);
}
