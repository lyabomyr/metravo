import { HttpErrorResponse } from '@angular/common/http';
import { describe, expect, it } from 'vitest';

import { toApiError } from './api-error';

describe('toApiError', () => {
  it('reads the backend error shape', () => {
    const error = new HttpErrorResponse({ status: 402, error: { detail: 'Upgrade needed', code: 'LimitReached' } });
    expect(toApiError(error)).toEqual({ message: 'Upgrade needed', code: 'LimitReached' });
  });

  it('reads FastAPI validation errors', () => {
    const error = new HttpErrorResponse({ status: 422, error: { detail: [{ msg: 'field required' }] } });
    expect(toApiError(error).message).toBe('field required');
  });

  it('explains an unreachable server in the user language', () => {
    expect(toApiError(new HttpErrorResponse({ status: 0 })).key).toBe('errors.network');
  });

  it('turns a disabled Firebase sign-in method into advice', () => {
    const error = Object.assign(new Error('Firebase: Error (auth/operation-not-allowed).'), { code: 'auth/operation-not-allowed' });
    expect(toApiError(error).key).toBe('errors.firebase.disabled');
  });
});
