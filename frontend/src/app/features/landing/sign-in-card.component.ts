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
        <button class="button button--primary button--block" type="button" (click)="signInWithGoogle()" [disabled]="loading()" data-cy="google">
          <span aria-hidden="true">G</span> {{ 'auth.google' | t }}
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
