import { Component, effect, inject, input, output } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';

import { PublicConfigService } from '../../core/config/public-config.service';
import { DEFAULT_SEARCH, SearchDraft } from './search.model';

/** The one search form, used by the editor and the onboarding wizard alike. */
@Component({
  selector: 'app-search-form',
  imports: [ReactiveFormsModule],
  templateUrl: './search-form.component.html',
})
export class SearchFormComponent {
  readonly value = input<SearchDraft>(DEFAULT_SEARCH);
  readonly submitLabel = input('Save');
  readonly busy = input(false);
  readonly saved = output<SearchDraft>();

  protected readonly config = inject(PublicConfigService).value;
  protected readonly form = inject(FormBuilder).nonNullable.group({
    name: ['', Validators.required],
    city: ['', Validators.required],
    max_price: [0, [Validators.required, Validators.min(1)]],
    min_area: [0, [Validators.required, Validators.min(1)]],
    max_area: [null as number | null],
    min_build_year: [null as number | null],
    enabled: [true],
  });
  protected selectedSources = new Set<string>();

  constructor() {
    effect(() => {
      const value = this.value();
      this.form.reset(value);
      this.selectedSources = new Set(value.sources);
    });
  }

  protected toggleSource(source: string, checked: boolean): void {
    if (checked) this.selectedSources.add(source);
    else this.selectedSources.delete(source);
  }

  protected submit(): void {
    if (this.form.invalid) return;
    this.saved.emit({ ...this.form.getRawValue(), sources: [...this.selectedSources] });
  }
}
