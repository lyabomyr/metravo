import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';

import { SessionStore } from './session.store';

export const signedInGuard: CanActivateFn = () =>
  inject(SessionStore).isSignedIn() || inject(Router).createUrlTree(['/']);

export const signedOutGuard: CanActivateFn = () =>
  !inject(SessionStore).isSignedIn() || inject(Router).createUrlTree(['/listings']);

export const adminGuard: CanActivateFn = () =>
  inject(SessionStore).user()?.is_admin === true || inject(Router).createUrlTree(['/listings']);
