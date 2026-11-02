import { Component, inject } from '@angular/core';

import { I18nService } from './i18n.service';
import { LOCALES, Locale } from './locales';

/** A compact language picker. A signed-in user's profile follows the choice (see App). */
@Component({
  selector: 'app-language-switcher',
  template: `
    <select
      class="language"
      aria-label="Language"
      (change)="choose($any($event.target).value)"
      data-cy="language"
    >
      @for (option of locales; track option.code) {
        <!-- [selected] per option, not [value] on the select: the options do not exist yet when it binds -->
        <option [value]="option.code" [selected]="option.code === i18n.locale()">{{ option.label }}</option>
      }
    </select>
  `,
})
export class LanguageSwitcherComponent {
  protected readonly i18n = inject(I18nService);
  protected readonly locales = LOCALES;

  protected async choose(locale: Locale): Promise<void> {
    await this.i18n.use(locale);
  }
}
