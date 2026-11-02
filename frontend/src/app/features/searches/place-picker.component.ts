import { Component, inject, input, output, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PlaceMapComponent } from './place-map.component';
import { PlacesApiService } from './places-api.service';
import { Place } from './search.model';

/**
 * Where to look: any city, town or village, found by name or by clicking the map,
 * plus how far around it. Each lookup asks OpenStreetMap, so it runs on Find, not on every key.
 */
@Component({
  selector: 'app-place-picker',
  imports: [FormsModule, ErrorBannerComponent, PlaceMapComponent, TranslatePipe],
  template: `
    <div class="list">
      <div class="list__row">
        <span>{{ 'form.place' | t }}</span>
        <b data-cy="place-name">{{ place().name }}</b>
      </div>
      <div class="list__row list__row--stacked">
        <div class="row">
          <input
            class="place-query"
            [(ngModel)]="query"
            [ngModelOptions]="{ standalone: true }"
            (keydown.enter)="$event.preventDefault(); find()"
            [placeholder]="'form.placeSearch' | t"
            autocomplete="off"
            data-cy="place-query"
          />
          <button class="button button--small" type="button" (click)="find()" [disabled]="loading() || query.trim().length < 2" data-cy="place-find">
            {{ 'form.find' | t }}
          </button>
        </div>
      </div>
      @for (option of results(); track option.path) {
        <button class="list__row list__row--button" type="button" (click)="choose(option)" data-cy="place-result">
          <span><b>{{ option.name }}</b> <span class="muted small">{{ option.detail }}</span></span>
          <span aria-hidden="true">›</span>
        </button>
      }
      @if (searched() && !results().length) {
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
    <app-place-map [place]="place()" [radiusKm]="radiusKm()" (picked)="pickOnMap($event)" />
    <p class="section-note">{{ 'form.placeHint' | t }}</p>
  `,
  styles: `
    .place-query { flex: 1; }
  `,
})
export class PlacePickerComponent extends BasePage {
  readonly place = input.required<Place>();
  readonly radiusKm = input(0);
  readonly radiusChoices = input<number[]>([0]);
  readonly placeChange = output<Place>();
  readonly radiusChange = output<number>();

  private readonly api = inject(PlacesApiService);
  protected query = '';
  protected readonly results = signal<Place[]>([]);
  protected readonly searched = signal(false);

  protected find(): void {
    if (this.query.trim().length < 2) return;
    this.run(this.api.search(this.query.trim()), (places) => {
      this.results.set(places);
      this.searched.set(true);
    });
  }

  protected choose(place: Place): void {
    this.placeChange.emit(place);
    this.results.set([]);
    this.searched.set(false);
    this.query = '';
  }

  protected pickOnMap(point: { lat: number; lon: number }): void {
    this.run(this.api.at(point.lat, point.lon), (place) => {
      if (place) this.choose(place);
    });
  }
}
