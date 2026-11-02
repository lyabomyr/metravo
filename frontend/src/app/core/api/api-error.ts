import { HttpErrorResponse } from '@angular/common/http';

import type { TranslationKey } from '../i18n/locales/en';

/**
 * An error ready to show. The backend already translates its own messages
 * (it reads Accept-Language); errors raised in the browser carry a `key`
 * for the frontend dictionary instead.
 */
export interface ApiError {
  message: string;
  code: string | null;
  key?: TranslationKey;
}

/** Firebase's error codes the user can act on. Anything else reads as a generic failure. */
const FIREBASE_KEYS: Record<string, TranslationKey> = {
  'auth/operation-not-allowed': 'errors.firebase.disabled',
  'auth/popup-closed-by-user': 'errors.firebase.popupClosed',
  'auth/cancelled-popup-request': 'errors.firebase.popupClosed',
  'auth/invalid-action-code': 'errors.firebase.invalidLink',
  'auth/expired-action-code': 'errors.firebase.invalidLink',
  'auth/unauthorized-domain': 'errors.firebase.domain',
  'auth/network-request-failed': 'errors.network',
  'auth/missing-email': 'auth.emailPrompt',
};

export function toApiError(error: unknown): ApiError {
  if (error instanceof HttpErrorResponse) {
    if (error.status === 0) return { message: 'Cannot reach the server', code: null, key: 'errors.network' };
    const detail = error.error?.detail;
    const message = typeof detail === 'string' ? detail : Array.isArray(detail) ? detail[0]?.msg : null;
    return { message: message ?? `Request failed (${error.status})`, code: error.error?.code ?? null };
  }
  const code = (error as { code?: unknown })?.code;
  if (typeof code === 'string' && code.startsWith('auth/')) {
    return { message: code, code, key: FIREBASE_KEYS[code] ?? 'errors.generic' };
  }
  return { message: error instanceof Error ? error.message : 'Something went wrong', code: null };
}
