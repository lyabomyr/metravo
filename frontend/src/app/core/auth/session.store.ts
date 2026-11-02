import { Injectable, computed, inject, signal } from '@angular/core';
import { Observable, firstValueFrom, tap } from 'rxjs';

import { AuthApiService } from './auth-api.service';
import { Session, User } from './auth.models';

const TOKEN_KEY = 'metravo.token';

/** The signed-in user. The one source of truth every component reads from. */
@Injectable({ providedIn: 'root' })
export class SessionStore {
  private readonly api = inject(AuthApiService);

  readonly token = signal<string | null>(readToken());
  readonly user = signal<User | null>(null);
  readonly isSignedIn = computed(() => this.user() !== null);
  readonly isPro = computed(() => this.user()?.plan === 'pro');

  /** Exchange a provider credential (email, Firebase ID token…) for our session. */
  signIn(provider: string, credential: string): Observable<Session> {
    return this.api.createSession(provider, credential).pipe(
      tap((session) => {
        writeToken(session.token);
        this.token.set(session.token);
        this.user.set(session.user);
      }),
    );
  }

  /** Called once at startup: turn a stored token back into a user, or forget it. */
  async restore(): Promise<void> {
    if (!this.token()) return;
    try {
      this.user.set(await firstValueFrom(this.api.me()));
    } catch {
      this.signOut();
    }
  }

  /** Keep the profile's language (used for Telegram) in step with the website's. */
  syncLocale(locale: string): void {
    const user = this.user();
    if (user && user.locale !== locale) this.api.setLocale(locale).subscribe((updated) => this.user.set(updated));
  }

  refresh(): Observable<User> {
    return this.api.me().pipe(tap((user) => this.user.set(user)));
  }

  signOut(): void {
    writeToken(null);
    this.token.set(null);
    this.user.set(null);
  }
}

function readToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

function writeToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage blocked (private mode): the session lasts until the tab closes.
  }
}
