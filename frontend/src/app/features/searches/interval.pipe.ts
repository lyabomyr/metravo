import { Pipe, PipeTransform, inject } from '@angular/core';

import { I18nService } from '../../core/i18n/i18n.service';

/** `{{ 180 | interval }}` → "Every 3 h"; 5 → "Every 5 min"; 60 → "Every hour"; 1440 → "Once a day". */
@Pipe({ name: 'interval', pure: false })
export class IntervalPipe implements PipeTransform {
  private readonly i18n = inject(I18nService);

  transform(minutes: number): string {
    if (minutes >= 1440) return this.i18n.t('interval.daily');
    if (minutes < 60) return this.i18n.t('interval.minutes', { n: minutes });
    if (minutes === 60) return this.i18n.t('interval.hourly');
    return this.i18n.t('interval.hours', { n: minutes / 60 });
  }
}
