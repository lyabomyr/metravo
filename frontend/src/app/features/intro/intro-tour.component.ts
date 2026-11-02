import { Component, HostListener, inject, signal } from '@angular/core';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import type { TranslationKey } from '../../core/i18n/locales/en';
import { IntroService } from './intro.service';

interface Slide {
  icon: string;
  title: TranslationKey;
  text: TranslationKey;
}

const SLIDES: Slide[] = [
  { icon: '👋', title: 'intro.s1.title', text: 'intro.s1.text' },
  { icon: '🔍', title: 'intro.s2.title', text: 'intro.s2.text' },
  { icon: '🔔', title: 'intro.s3.title', text: 'intro.s3.text' },
  { icon: '🏠', title: 'intro.s4.title', text: 'intro.s4.text' },
  { icon: '🗄️', title: 'intro.s5.title', text: 'intro.s5.text' },
];

/** A short guided tour of the app, shown as a bottom sheet on phones and a card on desktop. */
@Component({
  selector: 'app-intro-tour',
  imports: [TranslatePipe],
  styleUrl: './intro-tour.component.css',
  template: `
    @if (intro.isOpen()) {
      @let slide = slides[index()];
      <div class="tour" role="dialog" aria-modal="true" [attr.aria-label]="slide.title | t" data-cy="tour">
        <div class="tour__card">
          <div class="tour__icon" aria-hidden="true">{{ slide.icon }}</div>
          <p class="muted small">{{ 'intro.step' | t: { n: index() + 1, total: slides.length } }}</p>
          <h2 data-cy="tour-title">{{ slide.title | t }}</h2>
          <p>{{ slide.text | t }}</p>
          <div class="tour__dots" aria-hidden="true">
            @for (item of slides; track item.title; let n = $index) {
              <span [class.active]="n === index()"></span>
            }
          </div>
          <div class="row row--between">
            <button class="link" type="button" (click)="finish()" data-cy="tour-skip">{{ 'common.skip' | t }}</button>
            <span class="row">
              @if (index() > 0) {
                <button class="button button--small" type="button" (click)="go(index() - 1)" data-cy="tour-back">{{ 'common.back' | t }}</button>
              }
              @if (index() < slides.length - 1) {
                <button class="button button--small button--primary" type="button" (click)="go(index() + 1)" data-cy="tour-next">
                  {{ (index() === 0 ? 'intro.start' : 'common.next') | t }}
                </button>
              } @else {
                <button class="button button--small button--primary" type="button" (click)="finish()" data-cy="tour-done">
                  {{ 'intro.finish' | t }}
                </button>
              }
            </span>
          </div>
        </div>
      </div>
    }
  `,
})
export class IntroTourComponent {
  protected readonly intro = inject(IntroService);
  protected readonly slides = SLIDES;
  protected readonly index = signal(0);

  // The tour stays on the current page: a new user meets it in the middle of onboarding.
  protected go(index: number): void {
    this.index.set(index);
  }

  @HostListener('document:keydown.escape')
  protected finish(): void {
    if (!this.intro.isOpen()) return;
    this.intro.close();
    this.index.set(0);
  }
}
