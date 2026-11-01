import { DestroyRef, Directive, inject, signal } from '@angular/core';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Observable, finalize } from 'rxjs';

import { ApiError, toApiError } from '../api/api-error';

/**
 * Base for every page. Gives `loading` / `error` state and `run()`, so no
 * page writes its own subscribe-spinner-catch boilerplate.
 */
@Directive()
export abstract class BasePage {
  protected readonly loading = signal(false);
  protected readonly error = signal<ApiError | null>(null);
  private readonly destroyRef = inject(DestroyRef);

  protected run<T>(request: Observable<T>, onSuccess?: (value: T) => void): void {
    this.loading.set(true);
    this.error.set(null);
    request
      .pipe(
        takeUntilDestroyed(this.destroyRef),
        finalize(() => this.loading.set(false)),
      )
      .subscribe({
        next: (value) => onSuccess?.(value),
        error: (error: unknown) => this.error.set(toApiError(error)),
      });
  }
}
