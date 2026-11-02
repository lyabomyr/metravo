import { describe, expect, it } from 'vitest';

import { isInAppBrowser } from './sign-in-card.component';

describe('isInAppBrowser', () => {
  it('knows the browsers Google signs in from', () => {
    const safari = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Mobile/15E148 Safari/604.1';
    const chromeIos = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/130.0 Mobile/15E148 Safari/604.1';
    expect(isInAppBrowser(safari)).toBe(false);
    expect(isInAppBrowser(chromeIos)).toBe(false);
  });

  it('spots apps that open links in their own browser', () => {
    const instagram = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 350.0';
    const iosWebView = 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148';
    const androidWebView = 'Mozilla/5.0 (Linux; Android 14; Pixel 8; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/130.0 Mobile Safari/537.36';
    expect(isInAppBrowser(instagram)).toBe(true);
    expect(isInAppBrowser(iosWebView)).toBe(true);
    expect(isInAppBrowser(androidWebView)).toBe(true);
  });
});
