import { Component, OnInit, inject, input, signal } from '@angular/core';
import { Router } from '@angular/router';

import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';
import { PageHeaderComponent } from '../../core/ui/page-header.component';
import { DEFAULT_SEARCH, SearchDraft, SearchFormValue } from './search.model';
import { SearchFormComponent } from './search-form.component';
import { SearchesApiService } from './searches-api.service';

/** Creates a search at `/searches/new`, edits one at `/searches/:id`. */
@Component({
  selector: 'app-search-edit-page',
  imports: [ErrorBannerComponent, PageHeaderComponent, SearchFormComponent, TranslatePipe],
  template: `
    <app-page-header [title]="(id() ? 'searches.editTitle' : 'searches.newTitle') | t" />
    <app-error-banner [error]="error()" />
    <section class="card">
      <app-search-form [value]="draft()" [busy]="loading()" (saved)="save($event)" />
    </section>
  `,
})
export class SearchEditPage extends BasePage implements OnInit {
  /** Route parameter, bound by `withComponentInputBinding`. */
  readonly id = input<string>();

  private readonly api = inject(SearchesApiService);
  private readonly router = inject(Router);
  protected readonly draft = signal<SearchFormValue>(DEFAULT_SEARCH);

  ngOnInit(): void {
    const id = this.id();
    if (id) this.run(this.api.one(id), (search) => this.draft.set(search));
  }

  protected save(draft: SearchDraft): void {
    const id = this.id();
    if (id) {
      this.run(this.api.update(id, draft), () => this.router.navigateByUrl('/searches'));
      return;
    }
    // A new search goes straight on to where its listings should be sent.
    this.run(this.api.create(draft), (search) => this.router.navigate(['/searches', search.id, 'notifications']));
  }
}
