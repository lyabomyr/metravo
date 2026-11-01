import { DatePipe, DecimalPipe } from '@angular/common';
import { Component, input } from '@angular/core';

import { Listing } from './listing.model';

@Component({
  selector: 'app-listing-card',
  imports: [DatePipe, DecimalPipe],
  template: `
    @let item = listing();
    <article class="card listing" data-cy="listing">
      @if (item.image_url) {
        <img [src]="item.image_url" alt="" loading="lazy" (error)="$any($event.target).removeAttribute('src')" />
      } @else {
        <img alt="" />
      }
      <div class="stack" style="gap: 4px">
        <div class="listing__price">
          {{ item.price !== null ? (item.price | number: '1.0-0') + ' zł' : 'price n/a' }}
          @if (item.area) {
            <span class="muted">· {{ item.area }} m²</span>
          }
        </div>
        <a [href]="item.url" target="_blank" rel="noopener">{{ item.title || 'Open listing' }}</a>
        <div class="muted">{{ item.location }}</div>
        <div class="muted">
          <span class="badge">{{ item.source }}</span> found {{ item.first_seen_at | date: 'short' }}
        </div>
      </div>
    </article>
  `,
})
export class ListingCardComponent {
  readonly listing = input.required<Listing>();
}
