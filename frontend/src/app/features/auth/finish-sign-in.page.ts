import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { from } from 'rxjs';

import { FirebaseAuthClient } from '../../core/auth/firebase-auth.client';
import { SessionStore } from '../../core/auth/session.store';
import { TranslatePipe } from '../../core/i18n/translate.pipe';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';

/** Landing page for the Firebase email link. If it fails (e.g. opened on another device), asks for the email. */
@Component({
  selector: 'app-finish-sign-in-page',
  imports: [FormsModule, ErrorBannerComponent, TranslatePipe],
  template: `
    <section class="card stack" style="max-width: 420px; margin: 12vh auto 0">
      <h1>{{ 'auth.finish.title' | t }}</h1>
      <app-error-banner [error]="error()" />
      @if (error()) {
        <label>{{ 'auth.finish.confirm' | t }} <input type="email" [ngModel]="email()" (ngModelChange)="email.set($event)" /></label>
        <button class="button button--primary" type="button" (click)="finish(email())">{{ 'auth.finish.continue' | t }}</button>
      }
    </section>
  `,
})
export class FinishSignInPage extends BasePage implements OnInit {
  private readonly firebase = inject(FirebaseAuthClient);
  private readonly session = inject(SessionStore);
  private readonly router = inject(Router);

  protected readonly email = signal('');

  ngOnInit(): void {
    this.finish();
  }

  protected finish(email?: string): void {
    this.run(from(this.firebase.finishEmailLink(location.href, email)), (idToken) =>
      this.run(this.session.signIn('firebase', idToken), (session) =>
        this.router.navigateByUrl(session.is_new ? '/welcome' : '/listings'),
      ),
    );
  }
}
