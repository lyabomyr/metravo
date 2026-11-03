import { Component, computed, inject, input, output, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { FormsModule } from '@angular/forms';
import { Observable, Subject, catchError, debounceTime, distinctUntilChanged, finalize, map, of, switchMap } from 'rxjs';

import { toApiError } from '../../core/api/api-error';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PlaceMapComponent } from './place-map.component';
import { PlacesApiService } from './places-api.service';
import { MAX_PLACES, Place } from './search.model';

/** Pause after the last key before asking: each lookup reaches OpenStreetMap through the API. */
export const TYPING_PAUSE_MS = 300;

/**
 * Where to look: any city, town or village, suggested while the user types or picked on
 * the map, plus how far around it. A new search starts with no place at all; once it has
 * one, the next place picked is added (up to MAX_PLACES), and ✕ takes one away.
 */
@Component({
  selector: 'app-place-picker',
  imports: [FormsModule, ErrorBannerComponent, PlaceMapComponent, TranslatePipe],
  template: `
    <div class="list">
      <div class="list__row">
        <span>{{ 'form.place' | t }}</span>
        @if (place(); as chosen) {
          <span class="place-chosen">
            <b data-cy="place-name">{{ chosen.name }}</b> <span class="muted small">{{ chosen.detail }}</span>
            <button class="place-remove" type="button" (click)="removeMain()" [attr.aria-label]="'form.placeRemove' | t" data-cy="place-remove">✕</button>
          </span>
        } @else {
          <span class="muted" data-cy="place-name">{{ 'form.placeNone' | t }}</span>
        }
      </div>
      @for (extra of morePlaces(); track extra.path; let i = $index) {
        <div class="list__row" data-cy="place-extra">
          <span>{{ 'form.placeAlso' | t }}</span>
          <span class="place-chosen">
            <b>{{ extra.name }}</b> <span class="muted small">{{ extra.detail }}</span>
            <button class="place-remove" type="button" (click)="removeExtra(i)" [attr.aria-label]="'form.placeRemove' | t" data-cy="place-extra-remove">✕</button>
          </span>
        </div>
      }
      <div class="list__row list__row--stacked" [hidden]="full()">
        <div class="place-input">
          <input
            [ngModel]="query()"
            [ngModelOptions]="{ standalone: true }"
            (ngModelChange)="type($event)"
            (keydown.arrowdown)="$event.preventDefault(); move(1)"
            (keydown.arrowup)="$event.preventDefault(); move(-1)"
            (keydown.enter)="$event.preventDefault(); chooseActive()"
            (keydown.escape)="close()"
            [placeholder]="(place() ? 'form.placeAdd' : 'form.placeSearch') | t"
            role="combobox"
            aria-autocomplete="list"
            [attr.aria-expanded]="results().length > 0"
            autocomplete="off"
            enterkeyhint="search"
            data-cy="place-query"
          />
          @if (searching() || loading()) {
            <span class="spinner place-input__spinner" role="status" [attr.aria-label]="'common.loading' | t" data-cy="place-loading"></span>
          }
        </div>
      </div>
      @for (option of results(); track option.path; let i = $index) {
        <button
          class="list__row list__row--button"
          [class.place-option--active]="i === active()"
          type="button"
          role="option"
          [attr.aria-selected]="i === active()"
          (click)="choose(option)"
          data-cy="place-result"
        >
          <span><b>{{ option.name }}</b> <span class="muted small">{{ option.detail }}</span></span>
          <span aria-hidden="true">›</span>
        </button>
      }
      @if (searched() && !searching() && !results().length) {
        <div class="list__row muted" data-cy="place-none">{{ 'form.noPlaces' | t }}</div>
      }
      <label class="list__row">
        <span>{{ 'form.radius' | t }}</span>
        <select [ngModel]="radiusKm()" [ngModelOptions]="{ standalone: true }" (ngModelChange)="radiusChange.emit(+$event)" data-cy="search-radius">
          @for (km of radiusChoices(); track km) {
            <option [value]="km">{{ km ? ('form.radiusKm' | t: { n: km }) : ('form.radiusNone' | t) }}</option>
          }
        </select>
      </label>
    </div>
    <app-error-banner [error]="error()" />
    <app-place-map [places]="places()" [radiusKm]="radiusKm()" (picked)="pickOnMap($event)" />
    <p class="section-note">{{ 'form.placeHint' | t }}</p>
  `,
  styles: `
    .place-input { position: relative; display: flex; align-items: center; }
    .place-input input { flex: 1; padding-right: 32px; }
    .place-input__spinner { position: absolute; right: 10px; color: var(--muted); }
    .place-chosen { text-align: right; }
    .place-remove { margin-left: 6px; padding: 2px 6px; border: 0; background: none; color: var(--muted); font-size: 15px; cursor: pointer; }
    .place-option--active { background: var(--fill); }
  `,
})
export class PlacePickerComponent extends BasePage {
  readonly place = input<Place | null>(null);
  readonly morePlaces = input<Place[]>([]);
  readonly radiusKm = input(0);
  readonly radiusChoices = input<number[]>([0]);
  readonly placeChange = output<Place | null>();
  readonly morePlacesChange = output<Place[]>();
  protected readonly places = computed(() => [this.place(), ...this.morePlaces()].filter((place): place is Place => !!place));
  protected readonly full = computed(() => this.places().length >= MAX_PLACES);
  readonly radiusChange = output<number>();

  private readonly api = inject(PlacesApiService);
  private readonly typed = new Subject<string>();
  protected readonly query = signal('');
  protected readonly results = signal<Place[]>([]);
  /** A lookup finished, so an empty list means "nothing found" rather than "not asked yet". */
  protected readonly searched = signal(false);
  protected readonly searching = signal(false);
  protected readonly active = signal(0);

  constructor() {
    super();
    this.typed
      .pipe(
        map((text) => text.trim()),
        debounceTime(TYPING_PAUSE_MS),
        distinctUntilChanged(),
        // A newer query cancels the one in flight, so suggestions never arrive out of order.
        switchMap((text) => (text.length < 2 ? of(null) : this.lookUp(text))),
        takeUntilDestroyed(),
      )
      .subscribe((places) => {
        this.results.set(places ?? []);
        this.searched.set(places !== null);
        this.active.set(0);
      });
  }

  protected type(text: string): void {
    this.query.set(text);
    this.error.set(null);
    this.typed.next(text);
  }

  protected move(step: number): void {
    const count = this.results().length;
    if (count) this.active.set((this.active() + step + count) % count);
  }

  protected chooseActive(): void {
    const option = this.results()[this.active()];
    if (option) this.choose(option);
  }

  protected close(): void {
    this.results.set([]);
    this.searched.set(false);
  }

  protected choose(place: Place): void {
    if (!this.place()) this.placeChange.emit(place);
    else if (!this.full() && !this.places().some((chosen) => chosen.path === place.path)) {
      this.morePlacesChange.emit([...this.morePlaces(), place]);
    }
    this.close();
    this.query.set('');
    this.typed.next('');
  }

  /** The first extra place takes the main one's role: its name, its first row. */
  protected removeMain(): void {
    const [next = null, ...rest] = this.morePlaces();
    this.placeChange.emit(next);
    this.morePlacesChange.emit(rest);
  }

  protected removeExtra(index: number): void {
    this.morePlacesChange.emit(this.morePlaces().filter((_, i) => i !== index));
  }

  protected pickOnMap(point: { lat: number; lon: number }): void {
    this.run(this.api.at(point.lat, point.lon), (place) => {
      if (place) this.choose(place);
    });
  }

  /** Null on failure: the error banner explains it, and "nothing found" would be a lie. */
  private lookUp(text: string): Observable<Place[] | null> {
    this.searching.set(true);
    return this.api.search(text).pipe(
      catchError((error: unknown) => {
        this.error.set(toApiError(error));
        return of(null);
      }),
      finalize(() => this.searching.set(false)),
    );
  }
}
