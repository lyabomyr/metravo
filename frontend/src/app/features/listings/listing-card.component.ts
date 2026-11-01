import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, input, signal } from '@angular/core';

import { Listing } from './listing.model';

@Component({
  selector: 'app-listing-card',
  imports: [DatePipe, DecimalPipe],
  template: `
    @let item = listing();
    <a class="card card--interactive listing" [href]="item.url" target="_blank" rel="noopener" data-cy="listing">
      @if (item.image_url && !imageFailed()) {
        <img class="listing__photo" [src]="item.image_url" alt="" loading="lazy" (error)="imageFailed.set(true)" />
      } @else {
        <div class="listing__photo"></div>
      }
      <div class="listing__body">
        <div class="listing__price">
          {{ item.price !== null ? (item.price | number: '1.0-0') + ' zł' : 'Price on request' }}
          @if (item.price !== null && item.deal_type === 'rent') {
            <span class="muted small">/ month</span>
          }
        </div>
        <div class="listing__meta">
          @if (item.area) {
            <span class="chip">{{ item.area }} m²</span>
          }
          @if (item.rooms) {
            <span class="chip">{{ item.rooms }} rooms</span>
          }
          @if (item.area && item.price && item.deal_type === 'sale') {
            <span class="chip">{{ item.price / item.area | number: '1.0-0' }} zł/m²</span>
          }
        </div>
        <div class="listing__title">{{ item.title || 'Open listing' }}</div>
        <div class="listing__meta">{{ item.location }}</div>
        <div class="listing__meta">
          <span class="badge">{{ item.source }}</span>
          <span>{{ item.first_seen_at | date: 'd MMM, HH:mm' }}</span>
        </div>
      </div>
    </a>
  `,
})
export class ListingCardComponent {
  readonly listing = input.required<Listing>();
  protected readonly imageFailed = signal(false);
}
