import { Pipe, PipeTransform, inject } from '@angular/core';

import { I18nService, Params } from './i18n.service';
import { TranslationKey } from './locales/en';

/** `{{ 'nav.listings' | t }}` or `{{ 'search.limit' | t: { n: 1 } }}`. Re-renders when the language changes. */
@Pipe({ name: 't', pure: false })
export class TranslatePipe implements PipeTransform {
  private readonly i18n = inject(I18nService);

  transform(key: TranslationKey, params?: Params): string {
    return this.i18n.t(key, params);
  }
}
