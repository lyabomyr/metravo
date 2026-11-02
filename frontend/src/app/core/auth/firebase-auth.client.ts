import { InjectionToken, Injectable, inject } from '@angular/core';

import { PublicConfigService } from '../config/public-config.service';

const PENDING_EMAIL_KEY = 'metravo.pendingEmail';

export type Firebase = { auth: import('firebase/auth').Auth; sdk: typeof import('firebase/auth') };

/** Downloads the SDK; replaced in specs, which cannot reach Google. */
export const FIREBASE_LOADER = new InjectionToken<() => Promise<Firebase>>('firebase loader', {
  providedIn: 'root',
  factory: () => {
    const config = inject(PublicConfigService);
    return async () => {
      const [{ initializeApp, getApps }, sdk] = await Promise.all([import('firebase/app'), import('firebase/auth')]);
      const app = getApps()[0] ?? initializeApp(config.value.firebase ?? {});
      const auth = sdk.getAuth(app);
      auth.languageCode = document.documentElement.lang || 'en'; // sign-in emails in the user's language
      return { auth, sdk };
    };
  },
});

/**
 * Firebase Auth, loaded only when the backend enables it — local and e2e
 * runs never download the SDK.
 *
 * Firebase only proves who the user is; the backend then issues our own
 * session (see `SessionStore.signIn('firebase', idToken)`).
 */
@Injectable({ providedIn: 'root' })
export class FirebaseAuthClient {
  private readonly load = inject(FIREBASE_LOADER);
  private ready?: Promise<Firebase>;
  private loaded?: Firebase;

  async sendEmailLink(email: string): Promise<void> {
    const { auth, sdk } = await this.prepare();
    await sdk.sendSignInLinkToEmail(auth, email, { url: `${location.origin}/auth/finish`, handleCodeInApp: true });
    localStorage.setItem(PENDING_EMAIL_KEY, email);
  }

  async isEmailLink(url: string): Promise<boolean> {
    const { auth, sdk } = await this.prepare();
    return sdk.isSignInWithEmailLink(auth, url);
  }

  /** Complete an email-link sign-in. `email` is only needed on another device. */
  async finishEmailLink(url: string, email?: string): Promise<string> {
    const { auth, sdk } = await this.prepare();
    const address = email ?? localStorage.getItem(PENDING_EMAIL_KEY);
    // The link was opened on another device: the page asks for the address (the key maps to a translated prompt).
    if (!address) throw Object.assign(new Error('missing email'), { code: 'auth/missing-email' });
    const credential = await sdk.signInWithEmailLink(auth, address, url);
    localStorage.removeItem(PENDING_EMAIL_KEY);
    return credential.user.getIdToken();
  }

  /**
   * Download the SDK ahead of the click. A phone opens the Google window only straight from a
   * tap; loading the SDK first used up that moment and the window was blocked.
   */
  prepare(): Promise<Firebase> {
    this.ready ??= this.load().then((firebase) => (this.loaded = firebase));
    return this.ready;
  }

  /** The ID token; on a redirect it never resolves, the page leaves and `redirectResult` finishes. */
  signInWithGoogle(): Promise<string> {
    // No `await` before the popup opens: it must stay inside the tap that asked for it.
    return this.loaded ? this.popup(this.loaded) : this.prepare().then((firebase) => this.popup(firebase));
  }

  /** The ID token after coming back from Google's page, or null when the user did not go there. */
  async redirectResult(): Promise<string | null> {
    const { auth, sdk } = await this.prepare();
    const credential = await sdk.getRedirectResult(auth);
    return credential ? credential.user.getIdToken() : null;
  }

  private async popup({ auth, sdk }: Firebase): Promise<string> {
    const provider = new sdk.GoogleAuthProvider();
    try {
      const credential = await sdk.signInWithPopup(auth, provider);
      return await credential.user.getIdToken();
    } catch (error) {
      // Some browsers refuse every new window: go to Google in this tab and come back.
      if ((error as { code?: string }).code !== 'auth/popup-blocked') throw error;
      await sdk.signInWithRedirect(auth, provider);
      return new Promise<string>(() => undefined);
    }
  }
}
