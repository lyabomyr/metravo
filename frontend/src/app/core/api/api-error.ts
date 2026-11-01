import { HttpErrorResponse } from '@angular/common/http';

/** Error shape the backend returns: `{ detail, code }` (see backend core/errors.py). */
export interface ApiError {
  message: string;
  code: string | null;
}

export function toApiError(error: unknown): ApiError {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) return { message: 'Cannot reach the server. Is it running?', code: null };
    const detail = error.error?.detail;
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg : null;
    return { message: message ?? `Request failed (${error.status})`, code: error.error?.code ?? null };
  }
  return { message: error instanceof Error ? error.message : 'Something went wrong', code: null };
}
