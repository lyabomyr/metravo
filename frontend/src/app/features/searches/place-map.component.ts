import { Component, ElementRef, OnDestroy, effect, input, output, viewChild } from '@angular/core';
import type { Circle, CircleMarker, Map as LeafletMap } from 'leaflet';

import { Place } from './search.model';

/** Before a place is chosen the map shows the whole country. */
const POLAND: [number, number] = [52.07, 19.48];

/**
 * The chosen place and the circle the search covers, on an OpenStreetMap map.
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
  readonly place = input<Place | null>(null);
  readonly radiusKm = input(0);
  readonly picked = output<{ lat: number; lon: number }>();

  private readonly element = viewChild.required<ElementRef<HTMLElement>>('map');
  private map?: LeafletMap;
  private marker?: CircleMarker;
  private circle?: Circle;

  constructor() {
    effect(() => void this.draw(this.place(), this.radiusKm()));
  }

  ngOnDestroy(): void {
    this.map?.remove();
  }

  private async draw(place: Place | null, radiusKm: number): Promise<void> {
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
      this.marker = L.circleMarker(POLAND, { radius: 7, color: '#007aff', fillOpacity: 1 });
      this.circle = L.circle(POLAND, { radius: 0, color: '#007aff', fillOpacity: 0.12, weight: 1 });
    }
    if (!place) {
      this.marker!.remove();
      this.circle!.remove();
      this.map.setView(POLAND, 6);
      return;
    }
    const centre: [number, number] = [place.lat, place.lon];
    this.marker!.setLatLng(centre).addTo(this.map);
    this.circle!.addTo(this.map);
    this.circle!.setLatLng(centre).setRadius(radiusKm * 1000);
    if (radiusKm) this.map.fitBounds(this.circle!.getBounds(), { padding: [12, 12] });
    else this.map.setView(centre, 12);
  }
}
