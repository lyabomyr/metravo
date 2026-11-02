import { Injectable, inject } from '@angular/core';

import { PublicConfigService } from '../config/public-config.service';

const PENDING_EMAIL_KEY = 'metravo.pendingEmail';

/**
 * Firebase Auth, loaded only when the backend enables it — local and e2e
 * runs never download the SDK.
 *
 * Firebase only proves who the user is; the backend then issues our own
 * session (see `SessionStore.signIn('firebase', idToken)`).
 */
@Injectable({ providedIn: 'root' })
export class FirebaseAuthClient {
  private readonly publicConfig = inject(PublicConfigService);

  async sendEmailLink(email: string): Promise<void> {
    const { auth, sdk } = await this.load();
    await sdk.sendSignInLinkToEmail(auth, email, { url: `${location.origin}/auth/finish`, handleCodeInApp: true });
    localStorage.setItem(PENDING_EMAIL_KEY, email);
  }

  async isEmailLink(url: string): Promise<boolean> {
    const { auth, sdk } = await this.load();
    return sdk.isSignInWithEmailLink(auth, url);
  }

  /** Complete an email-link sign-in. `email` is only needed on another device. */
  async finishEmailLink(url: string, email?: string): Promise<string> {
    const { auth, sdk } = await this.load();
    const address = email ?? localStorage.getItem(PENDING_EMAIL_KEY);
    // The link was opened on another device: the page asks for the address (the key maps to a translated prompt).
    if (!address) throw Object.assign(new Error('missing email'), { code: 'auth/missing-email' });
    const credential = await sdk.signInWithEmailLink(auth, address, url);
    localStorage.removeItem(PENDING_EMAIL_KEY);
    return credential.user.getIdToken();
  }

  async signInWithGoogle(): Promise<string> {
    const { auth, sdk } = await this.load();
    const credential = await sdk.signInWithPopup(auth, new sdk.GoogleAuthProvider());
    return credential.user.getIdToken();
  }

  private async load() {
    const [{ initializeApp, getApps }, sdk] = await Promise.all([import('firebase/app'), import('firebase/auth')]);
    const app = getApps()[0] ?? initializeApp(this.publicConfig.value.firebase ?? {});
    const auth = sdk.getAuth(app);
    auth.languageCode = document.documentElement.lang || 'en'; // sign-in emails in the user's language
    return { auth, sdk };
  }
}
