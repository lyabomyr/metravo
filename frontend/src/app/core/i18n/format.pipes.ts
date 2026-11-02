import { Pipe, PipeTransform, inject } from '@angular/core';

import { I18nService } from './i18n.service';

/** `{{ 520000 | money }}` → "520 000 zł" in the current language's number format. */
@Pipe({ name: 'money', pure: false })
export class MoneyPipe implements PipeTransform {
  private readonly i18n = inject(I18nService);

  transform(value: number | null | undefined): string {
    if (value === null || value === undefined) return '';
    return `${new Intl.NumberFormat(this.i18n.intlLocale(), { maximumFractionDigits: 0 }).format(value)} zł`;
  }
}

/** `{{ iso | when }}` → a short date and time; `{{ iso | when: 'date' }}` → the date only. */
@Pipe({ name: 'when', pure: false })
export class WhenPipe implements PipeTransform {
  private readonly i18n = inject(I18nService);

  transform(value: string | null | undefined, style: 'datetime' | 'date' = 'datetime'): string {
    if (!value) return '';
    const options: Intl.DateTimeFormatOptions =
      style === 'date' ? { dateStyle: 'medium' } : { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' };
    return new Intl.DateTimeFormat(this.i18n.intlLocale(), options).format(new Date(value));
  }
}
