import { Component, computed, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { from } from 'rxjs';

import { Session } from '../../core/auth/auth.models';
import { FirebaseAuthClient } from '../../core/auth/firebase-auth.client';
import { SessionStore } from '../../core/auth/session.store';
import { PublicConfigService } from '../../core/config/public-config.service';
import { BasePage } from '../../core/ui/base-page';
import { ErrorBannerComponent } from '../../core/ui/error-banner.component';

@Component({
  selector: 'app-login-page',
  imports: [FormsModule, ErrorBannerComponent],
  templateUrl: './login.page.html',
})
export class LoginPage extends BasePage {
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
