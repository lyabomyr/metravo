import { Component, ElementRef, OnDestroy, effect, input, output, viewChild } from '@angular/core';
import type { FeatureGroup, Map as LeafletMap } from 'leaflet';

import { Place } from './search.model';

/** Before a place is chosen the map shows the whole country. */
const POLAND: [number, number] = [52.07, 19.48];

/**
 * The chosen places and the circles the search covers, on an OpenStreetMap map.
 * Clicking the map asks for the place at that point. Leaflet loads only here.
 */
@Component({
  selector: 'app-place-map',
  template: `<div #map class="place-map" data-cy="place-map"></div>`,
  styles: `
    .place-map { height: 240px; border-radius: 12px; overflow: hidden; z-index: 0; }
  `,
})
export class PlaceMapComponent implements OnDestroy {
  readonly places = input<Place[]>([]);
  readonly radiusKm = input(0);
  readonly picked = output<{ lat: number; lon: number }>();

  private readonly element = viewChild.required<ElementRef<HTMLElement>>('map');
  private map?: LeafletMap;
  private layers?: FeatureGroup;

  constructor() {
    effect(() => void this.draw(this.places(), this.radiusKm()));
  }

  ngOnDestroy(): void {
    this.map?.stop();
    this.map?.remove();
  }

  private async draw(places: Place[], radiusKm: number): Promise<void> {
    // Leaflet is CommonJS: depending on the bundler it arrives as the module or as its `default`.
    const module = await import('leaflet');
    const L = ((module as unknown as { default?: typeof module }).default ?? module) as typeof module;
    if (!this.map) {
      this.map = L.map(this.element().nativeElement, { scrollWheelZoom: false });
      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 18,
        attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      }).addTo(this.map);
      this.map.on('click', (event) => this.picked.emit({ lat: event.latlng.lat, lon: event.latlng.lng }));
      this.layers = L.featureGroup().addTo(this.map);
    }
    this.layers!.clearLayers();
    // No animation: the form can close mid-zoom (Save), and Leaflet fails on a map removed while it zooms.
    if (!places.length) {
      this.map.setView(POLAND, 6, { animate: false });
      return;
    }
    for (const place of places) {
      const centre: [number, number] = [place.lat, place.lon];
      L.circleMarker(centre, { radius: 7, color: '#007aff', fillOpacity: 1 }).addTo(this.layers!);
      if (radiusKm) L.circle(centre, { radius: radiusKm * 1000, color: '#007aff', fillOpacity: 0.12, weight: 1 }).addTo(this.layers!);
    }
    if (places.length === 1 && !radiusKm) this.map.setView([places[0].lat, places[0].lon], 12, { animate: false });
    else this.map.fitBounds(this.layers!.getBounds(), { padding: [12, 12], maxZoom: 12, animate: false });
  }
}
