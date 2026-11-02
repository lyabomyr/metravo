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

/** Email link and Google with Firebase; any email in local and e2e runs. A new account goes to onboarding. */
@Component({
  selector: 'app-sign-in-card',
  imports: [FormsModule, ErrorBannerComponent, TranslatePipe],
  template: `
    <section class="card stack sign-in" id="start">
      <div class="stack stack--tight">
        <h2>{{ 'auth.title' | t }}</h2>
        <p class="muted small">{{ 'auth.subtitle' | t }}</p>
      </div>
      <app-error-banner [error]="error()" />
      @if (linkSent()) {
        <div class="banner banner--success" data-cy="link-sent">{{ 'auth.linkSent' | t: { email: email() } }}</div>
      } @else {
        <form class="stack" (ngSubmit)="usesFirebase() ? sendEmailLink() : signInDev()">
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
            {{ (usesFirebase() ? 'auth.sendLink' : 'auth.signIn') | t }}
          </button>
        </form>
        @if (usesFirebase()) {
          <div class="divider small muted">{{ 'auth.or' | t }}</div>
          <button class="button button--block" type="button" (click)="signInWithGoogle()" [disabled]="loading()" data-cy="google">
            <span aria-hidden="true">G</span> {{ 'auth.google' | t }}
          </button>
        }
        @if (usesDevLogin() && !usesFirebase()) {
          <p class="muted small">{{ 'auth.devNote' | t }}</p>
        }
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
  protected readonly linkSent = signal(false);
  protected readonly usesFirebase = computed(() => this.providers.includes('firebase'));
  protected readonly usesDevLogin = computed(() => this.providers.includes('dev'));

  protected signInDev(): void {
    this.run(this.session.signIn('dev', this.email()), (session) => this.continue(session));
  }

  protected sendEmailLink(): void {
    this.run(from(this.firebase.sendEmailLink(this.email())), () => this.linkSent.set(true));
  }

  protected signInWithGoogle(): void {
    this.run(from(this.firebase.signInWithGoogle()), (idToken) =>
      this.run(this.session.signIn('firebase', idToken), (session) => this.continue(session)),
    );
  }

  private continue(session: Session): void {
    this.router.navigateByUrl(session.is_new ? '/welcome' : '/listings');
  }
}
