import { TestBed } from '@angular/core/testing';
import { of, throwError } from 'rxjs';
import { beforeEach, describe, expect, it } from 'vitest';

import { AuthApiService } from './auth-api.service';
import { Session } from './auth.models';
import { SessionStore } from './session.store';

const session: Session = {
  token: 't-1',
  is_new: true,
  user: { id: 'u1', email: 'a@b.pl', plan: 'free', is_admin: false, created_at: '2026-11-01', locale: 'en' },
};

describe('SessionStore', () => {
  let me: () => ReturnType<AuthApiService['me']>;

  beforeEach(() => {
    localStorage.clear();
    me = () => of(session.user);
    TestBed.configureTestingModule({
      providers: [{ provide: AuthApiService, useValue: { createSession: () => of(session), me: () => me() } }],
    });
  });

  it('keeps the token and user after signing in', () => {
    const store = TestBed.inject(SessionStore);
    store.signIn('dev', 'a@b.pl').subscribe();
    expect(store.isSignedIn()).toBe(true);
    expect(localStorage.getItem('metravo.token')).toBe('t-1');
  });

  it('forgets a token the server no longer accepts', async () => {
    localStorage.setItem('metravo.token', 'stale');
    me = () => throwError(() => new Error('401'));
    const store = TestBed.inject(SessionStore);
    await store.restore();
    expect(store.token()).toBeNull();
    expect(localStorage.getItem('metravo.token')).toBeNull();
  });
});
