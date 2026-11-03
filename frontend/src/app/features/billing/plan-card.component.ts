import { Component, computed, inject, input } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import type { TranslationKey } from '../../core/i18n/locales/en';
import { Plan } from './billing-api.service';

interface Feature {
  key: TranslationKey;
  params?: Record<string, string | number>;
  included: boolean;
}

/** One plan: price and what it includes. Actions (upgrade, sign up) go in the slot. */
@Component({
  selector: 'app-plan-card',
  imports: [TranslatePipe],
  template: `
    @let item = plan();
    <article class="card stack plan" [class.plan--featured]="item.price_usd > 0" [attr.data-cy]="'plan-' + item.code">
      <div class="row row--between">
        <h2>{{ item.name }}</h2>
        <ng-content select="[badge]" />
      </div>
      <div>
        <span class="plan__price">\${{ item.price_usd }}</span>
        <span class="muted"> {{ 'common.perMonth' | t }}</span>
      </div>
      <ul class="plan__features">
        @for (feature of features(); track feature.key) {
          <li [class.off]="!feature.included">{{ feature.key | t: feature.params }}</li>
        }
      </ul>
      <ng-content />
    </article>
  `,
})
export class PlanCardComponent {
  readonly plan = input.required<Plan>();
  private readonly i18n = inject(I18nService);

  protected readonly features = computed<Feature[]>(() => {
    const plan = this.plan();
    const features: Feature[] = [
      ...(plan.trial_days ? [{ key: 'plan.trialDays', params: { n: plan.trial_days }, included: true } as Feature] : []),
      { key: 'plan.searches', params: { n: plan.max_searches }, included: true },
      this.frequency(plan),
      { key: 'plan.portals', params: { sources: this.i18n.sources(plan.sources) }, included: true },
      { key: 'plan.telegram', included: true },
      { key: 'plan.channels', included: plan.channels.length > 1 },
      { key: 'plan.priceAlerts', included: plan.price_alerts },
      { key: 'plan.export', included: true },
    ];
    return features;
  });

  private frequency(plan: Plan): Feature {
    const minutes = plan.min_interval_minutes;
    if (minutes < 60) return { key: 'plan.nonstop', params: { n: minutes }, included: true };
    return { key: minutes < 1440 ? 'plan.hourly' : 'plan.daily', included: true };
  }
}
