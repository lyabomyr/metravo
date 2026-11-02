import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { from } from 'rxjs';

import { Session } from '../../core/auth/auth.models';
import { FirebaseAuthClient } from '../../core/auth/firebase-auth.client';
import { SessionStore } from '../../core/auth/session.store';
import { PublicConfigService } from '../../core/config/public-config.service';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';

/**
 * Google with Firebase (email links are off for now: opened on a phone they land in a
 * different browser than the one that asked). Any email in local and e2e runs.
 */
@Component({
  selector: 'app-sign-in-card',
  imports: [FormsModule, ErrorBannerComponent, TranslatePipe],
  template: `
    <section class="card stack sign-in" id="start">
      <div class="stack stack--tight">
        <h2>{{ 'auth.title' | t }}</h2>
        <p class="muted small">{{ (usesFirebase() ? 'auth.subtitleGoogle' : 'auth.subtitle') | t }}</p>
      </div>
      <app-error-banner [error]="error()" />
      @if (usesFirebase()) {
        @if (inAppBrowser) {
          <div class="banner banner--warning stack stack--tight" data-cy="in-app-browser">
            <span>{{ 'auth.inApp' | t }}</span>
            <button class="button button--small" type="button" (click)="copyLink()" data-cy="copy-link">
              {{ (copied() ? 'auth.copied' : 'auth.copyLink') | t }}
            </button>
          </div>
        }
        <button class="google" type="button" (click)="signInWithGoogle()" [disabled]="loading()" data-cy="google">
          <svg class="google__logo" viewBox="0 0 48 48" aria-hidden="true">
            <path fill="#EA4335" d="M24 9.5c3.54 0 6.71 1.22 9.21 3.6l6.85-6.85C35.9 2.38 30.47 0 24 0 14.62 0 6.51 5.38 2.56 13.22l7.98 6.19C12.43 13.72 17.74 9.5 24 9.5z"/>
            <path fill="#4285F4" d="M46.98 24.55c0-1.57-.15-3.09-.38-4.55H24v9.02h12.94c-.58 2.96-2.26 5.48-4.78 7.18l7.73 6c4.51-4.18 7.09-10.36 7.09-17.65z"/>
            <path fill="#FBBC05" d="M10.53 28.59c-.48-1.45-.76-2.99-.76-4.59s.27-3.14.76-4.59l-7.98-6.19C.92 16.46 0 20.12 0 24c0 3.88.92 7.54 2.56 10.78l7.97-6.19z"/>
            <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.89-5.81l-7.73-6c-2.15 1.45-4.92 2.3-8.16 2.3-6.26 0-11.57-4.22-13.47-9.91l-7.98 6.19C6.51 42.62 14.62 48 24 48z"/>
          </svg>
          <span>{{ 'auth.google' | t }}</span>
        </button>
      } @else {
        <!-- Local and e2e runs: any email signs in, no account needed. -->
        <form class="stack" (ngSubmit)="signInDev()">
          <input
            type="email"
            name="email"
            required
            autocomplete="email"
            placeholder="you@example.com"
            [attr.aria-label]="'auth.email' | t"
            [ngModel]="email()"
            (ngModelChange)="email.set($event)"
            data-cy="email"
          />
          <button class="button button--primary button--block" type="submit" [disabled]="loading() || !email()" data-cy="sign-in">
            {{ 'auth.signIn' | t }}
          </button>
        </form>
        <p class="muted small">{{ 'auth.devNote' | t }}</p>
      }
    </section>
  `,
  // Google's own sign-in button look: neutral surface, the four-colour logo, never recoloured.
  styles: `
    .google {
      display: flex; align-items: center; justify-content: center; gap: 12px; width: 100%;
      min-height: 48px; padding: 0 16px; border-radius: 999px; cursor: pointer;
      font: 500 16px/1 'Roboto', -apple-system, system-ui, sans-serif;
      background: #fff; color: #1f1f1f; border: 1px solid #747775;
      transition: box-shadow 0.15s var(--ease), opacity 0.15s;
    }
    .google:hover:not(:disabled) { box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25); }
    .google:disabled { opacity: 0.6; cursor: default; }
    .google__logo { width: 20px; height: 20px; flex: none; }
    @media (prefers-color-scheme: dark) {
      .google { background: #131314; color: #e3e3e3; border-color: #8e918f; }
    }
  `,
})
export class SignInCardComponent extends BasePage {
  private readonly session = inject(SessionStore);
  private readonly firebase = inject(FirebaseAuthClient);
  private readonly router = inject(Router);
  private readonly providers = inject(PublicConfigService).value.auth_providers;

  protected readonly email = signal('');
  protected readonly copied = signal(false);
  /** Google refuses to sign in inside apps' own browsers (Instagram, Facebook, TikTok, …). */
  protected readonly inAppBrowser = isInAppBrowser(navigator.userAgent);
  protected readonly usesFirebase = computed(() => this.providers.includes('firebase'));

  protected signInDev(): void {
    this.run(this.session.signIn('dev', this.email()), (session) => this.continue(session));
  }

  protected copyLink(): void {
    void navigator.clipboard?.writeText(location.href).then(() => this.copied.set(true));
  }

  protected signInWithGoogle(): void {
    this.run(from(this.firebase.signInWithGoogle()), (idToken) =>
      this.run(this.session.signIn('firebase', idToken), (session) => this.continue(session)),
    );
  }

  private continue(_: Session): void {
    this.router.navigateByUrl('/welcome');
  }
}

/** An app's built-in browser, where Google sign-in is blocked: iOS web views lack "Safari/", Android ones say "; wv)". */
export function isInAppBrowser(userAgent: string): boolean {
  if (/FBAN|FBAV|Instagram|Line\/|TikTok|musical_ly|; wv\)|Snapchat|LinkedInApp/.test(userAgent)) return true;
  return /iPhone|iPad|iPod/.test(userAgent) && !/Safari\//.test(userAgent);
}
