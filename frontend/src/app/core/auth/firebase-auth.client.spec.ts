import { TestBed } from '@angular/core/testing';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { FIREBASE_LOADER, Firebase, FirebaseAuthClient } from './firebase-auth.client';

function fakeFirebase(popup: () => Promise<unknown>) {
  const user = { getIdToken: () => Promise.resolve('id-token') };
  const sdk = {
    GoogleAuthProvider: class {},
    signInWithPopup: vi.fn(popup),
    signInWithRedirect: vi.fn(() => Promise.resolve()),
    getRedirectResult: vi.fn(() => Promise.resolve({ user })),
  };
  return { firebase: { auth: {}, sdk } as unknown as Firebase, sdk, user };
}

describe('FirebaseAuthClient', () => {
  let fake: ReturnType<typeof fakeFirebase>;

  beforeEach(() => {
    fake = fakeFirebase(() => Promise.resolve({ user: { getIdToken: () => Promise.resolve('id-token') } }));
    TestBed.configureTestingModule({ providers: [{ provide: FIREBASE_LOADER, useValue: () => Promise.resolve(fake.firebase) }] });
  });

  it('opens the Google window within the tap once the SDK is ready', async () => {
    const client = TestBed.inject(FirebaseAuthClient);
    await client.prepare();
    const token = client.signInWithGoogle();
    // Called synchronously: a phone would block a window opened after any wait.
    expect(fake.sdk.signInWithPopup).toHaveBeenCalledTimes(1);
    expect(await token).toBe('id-token');
  });

  it('goes to Google in the same tab when the browser blocks the window', async () => {
    fake.sdk.signInWithPopup.mockImplementation(() => Promise.reject(Object.assign(new Error('blocked'), { code: 'auth/popup-blocked' })));
    const client = TestBed.inject(FirebaseAuthClient);
    await client.prepare();
    void client.signInWithGoogle();
    await vi.waitFor(() => expect(fake.sdk.signInWithRedirect).toHaveBeenCalledTimes(1));
  });

  it('passes other failures on, such as a closed window', async () => {
    fake.sdk.signInWithPopup.mockImplementation(() => Promise.reject(Object.assign(new Error('closed'), { code: 'auth/popup-closed-by-user' })));
    const client = TestBed.inject(FirebaseAuthClient);
    await expect(client.signInWithGoogle()).rejects.toMatchObject({ code: 'auth/popup-closed-by-user' });
    expect(fake.sdk.signInWithRedirect).not.toHaveBeenCalled();
  });

  it('finishes a sign-in that came back from Google', async () => {
    const client = TestBed.inject(FirebaseAuthClient);
    expect(await client.redirectResult()).toBe('id-token');
    fake.sdk.getRedirectResult.mockImplementation(() => Promise.resolve(null as never));
    expect(await client.redirectResult()).toBeNull();
  });
});
