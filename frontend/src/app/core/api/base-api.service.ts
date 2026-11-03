import { HttpClient, HttpParams } from '@angular/common/http';
import { inject } from '@angular/core';
import { Observable, map, retry, throwError, timer } from 'rxjs';

import { RuntimeConfig } from '../config/runtime-config';

type QueryParams = Record<string, string | number | boolean | null | undefined>;

/** No answer, or the host is swapping instances (a deploy, a free instance waking up): worth asking again. */
const PASSING_FAILURES = [0, 502, 503, 504];
export const READ_RETRIES = 2;
export const RETRY_DELAY_MS = 1500;

/**
 * Base for every feature's API service.
 *
 * A subclass names its `path` (e.g. `/api/searches`) and exposes typed
 * methods; URL building, query params and file downloads live here once.
 */
export abstract class BaseApiService {
  private readonly http = inject(HttpClient);
  private readonly runtime = inject(RuntimeConfig);

  protected abstract readonly path: string;

  protected get<T>(suffix = '', params: QueryParams = {}): Observable<T> {
    // Only reads are repeated: asking twice changes nothing.
    return this.http.get<T>(this.url(suffix), { params: this.toParams(params) }).pipe(
      retry({
        count: READ_RETRIES,
        delay: (error: { status?: number }, attempt) =>
          PASSING_FAILURES.includes(error.status ?? -1) ? timer(RETRY_DELAY_MS * attempt) : throwError(() => error),
      }),
    );
  }

  protected post<T>(suffix = '', body: unknown = {}): Observable<T> {
    return this.http.post<T>(this.url(suffix), body);
  }

  protected put<T>(suffix: string, body: unknown): Observable<T> {
    return this.http.put<T>(this.url(suffix), body);
  }

  protected delete(suffix: string): Observable<void> {
    return this.http.delete<void>(this.url(suffix));
  }

  /** Fetch a file with the session token and hand it to the browser as a download. */
  protected download(suffix: string, filename: string): Observable<void> {
    return this.http.get(this.url(suffix), { responseType: 'blob' }).pipe(
      map((blob) => {
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
        URL.revokeObjectURL(link.href);
      }),
    );
  }

  private url(suffix: string): string {
    return `${this.runtime.apiUrl}${this.path}${suffix}`;
  }

  private toParams(params: QueryParams): HttpParams {
    let result = new HttpParams();
    for (const [key, value] of Object.entries(params)) {
      if (value !== null && value !== undefined && value !== '') result = result.set(key, String(value));
    }
    return result;
  }
}
