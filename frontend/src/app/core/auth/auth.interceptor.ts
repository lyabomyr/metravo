import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { Router } from '@angular/router';
import { catchError, throwError } from 'rxjs';

import { RuntimeConfig } from '../config/runtime-config';
import { I18nService } from '../i18n/i18n.service';
import { SessionStore } from './session.store';

/** Attaches the session token to our API calls; a 401 sends the user to sign in. */
export const authInterceptor: HttpInterceptorFn = (request, next) => {
  const session = inject(SessionStore);
  const router = inject(Router);
  const token = session.token();
  const isOurApi = request.url.startsWith(inject(RuntimeConfig).apiUrl);

  const headers: Record<string, string> = { 'Accept-Language': inject(I18nService).locale() };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const authorised = isOurApi ? request.clone({ setHeaders: headers }) : request;
  return next(authorised).pipe(
    catchError((error: unknown) => {
      if (error instanceof HttpErrorResponse && error.status === 401 && token) {
        session.signOut();
        router.navigateByUrl('/');
      }
      return throwError(() => error);
    }),
  );
};
