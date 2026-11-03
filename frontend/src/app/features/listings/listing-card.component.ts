import { Component, input, signal } from '@angular/core';

import { MoneyPipe, SourcesPipe, WhenPipe } from '../../core/i18n/format.pipes';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { Listing } from './listing.model';

@Component({
  selector: 'app-listing-card',
  imports: [MoneyPipe, SourcesPipe, TranslatePipe, WhenPipe],
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
          {{ item.price !== null ? (item.price | money) : ('listings.priceOnRequest' | t) }}
          @if (item.price !== null && item.deal_type === 'rent') {
            <span class="muted small">{{ 'common.perMonth' | t }}</span>
          }
        </div>
        <div class="listing__meta">
          @if (item.area) {
            <span class="chip">{{ item.area }} m²</span>
          }
          @if (item.rooms) {
            <span class="chip">{{ 'listings.rooms' | t: { n: item.rooms } }}</span>
          }
          @if (item.area && item.price && item.deal_type === 'sale') {
            <span class="chip">{{ item.price / item.area | money }}/m²</span>
          }
        </div>
        <div class="listing__title">{{ item.title || ('listings.untitled' | t) }}</div>
        <div class="listing__meta">{{ item.location }}</div>
        <div class="listing__meta">
          <span class="badge">{{ item.source | sources }}</span>
          <span>{{ item.first_seen_at | when }}</span>
        </div>
      </div>
    </a>
  `,
})
export class ListingCardComponent {
  readonly listing = input.required<Listing>();
  protected readonly imageFailed = signal(false);
}
