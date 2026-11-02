import { Component } from '@angular/core';

import { TranslatePipe } from '../../core/i18n/translate.pipe';

/** A looping animation of listings arriving in Telegram — the product in five seconds. */
@Component({
  selector: 'app-phone-demo',
  imports: [TranslatePipe],
  styleUrl: './phone-demo.component.css',
  template: `
    <figure class="phone" aria-hidden="true">
      <div class="phone__screen">
        <header class="phone__bar">
          <span class="phone__avatar">🏠</span>
          <span>
            <b>{{ 'landing.demo.chat' | t }}</b><br />
            <span class="phone__status">{{ 'landing.demo.online' | t }}</span>
          </span>
        </header>
        <div class="phone__chat">
          <div class="bubble" style="--i: 0">
            <b>{{ 'landing.demo.header' | t }}</b>
            <span class="bubble__line">• <u>520 000 zł · 45 m²</u> · Długa, Stare Miasto <i>[otodom]</i></span>
            <span class="bubble__line">• <u>499 000 zł · 42 m²</u> · Bronowice <i>[olx]</i></span>
            <span class="bubble__line">• <u>555 000 zł · 50 m²</u> · Wielicka, Płaszów <i>[morizon]</i></span>
          </div>
          <div class="bubble" style="--i: 1">
            <span class="bubble__line">{{ 'landing.demo.drop' | t }} · <u>535 000 zł · 52 m²</u> · Krowodrza <i>[otodom]</i></span>
          </div>
          <div class="bubble" style="--i: 2">
            <b>🏠 Wynajem Kraków</b>
            <span class="bubble__line">• <u>3 200 zł / mies. · 45 m²</u> · Lea, Krowodrza <i>[otodom]</i></span>
          </div>
        </div>
      </div>
      <figcaption class="muted small">{{ 'landing.demo.caption' | t }}</figcaption>
    </figure>
  `,
})
export class PhoneDemoComponent {}
