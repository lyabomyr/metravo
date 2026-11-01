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

  it('explains an unreachable server', () => {
    expect(toApiError(new HttpErrorResponse({ status: 0 })).message).toContain('Cannot reach the server');
  });
});
