/**
 * Shortcuts shared by every spec. UI journeys are tested once through the UI
 * (auth.cy.ts, onboarding.cy.ts); everywhere else these set state directly.
 */

const api = (path: string) => `${Cypress.env('apiUrl')}${path}`;

/** A fresh address per test, so tests never depend on each other's data. */
export const uniqueEmail = (prefix = 'user') => `${prefix}-${Date.now()}-${Cypress._.random(1e6)}@metravo.test`;

/** What the onboarding form saves when nothing is changed (frontend DEFAULT_SEARCH). */
export const DEFAULT_SEARCH = {
  name: 'My flat', city: 'krakow', deal_type: 'sale', property_type: 'flat',
  max_price: 600000, min_area: 40, sources: ['otodom', 'olx', 'morizon'],
};

/** Titles in the saved portal pages (backend/tests/fixtures/pages) that the default search matches. */
export const DEFAULT_MATCHES = ['2 pokoje przy Długiej', '3 pokoje Wielicka', '2 pokoje Bronowice', 'Duże mieszkanie Nowa Huta'];

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      /** Sign in through the API and store the session like the app does. The tour is marked seen unless `tour` is true. */
      signIn(email: string, options?: { tour?: boolean; locale?: string }): Chainable<string>;
      /** Authorised API call with the stored session token. */
      api(method: string, path: string, body?: object, failOnStatusCode?: boolean): Chainable<Response<any>>;
      /** Play Telegram: the user pressed Start on a deep link. */
      telegramStart(deepLink: string, chatId: number): Chainable<Response<any>>;
      /** Buy Pro through the test payment provider, as the checkout page would. */
      upgradeToPro(): Chainable<Response<any>>;
    }
  }
}

Cypress.Commands.add('signIn', (email: string, options: { tour?: boolean; locale?: string } = {}) =>
  cy.request('POST', api('/api/auth/session'), { provider: 'dev', credential: email }).then(({ body }) => {
    window.localStorage.setItem('metravo.token', body.token);
    window.localStorage.setItem('metravo.locale', options.locale ?? 'en');
    if (!options.tour) window.localStorage.setItem('metravo.introSeen', '1');
    return body.token as string;
  }),
);

Cypress.Commands.add('api', (method: string, path: string, body?: object, failOnStatusCode = true) =>
  cy.request({
    method,
    url: api(path),
    body,
    failOnStatusCode,
    headers: { Authorization: `Bearer ${window.localStorage.getItem('metravo.token')}` },
  }),
);

Cypress.Commands.add('telegramStart', (deepLink: string, chatId: number) => {
  const token = new URL(deepLink).searchParams.get('start');
  return cy.request({
    method: 'POST',
    url: api('/api/telegram/webhook'),
    headers: { 'X-Telegram-Bot-Api-Secret-Token': Cypress.env('telegramSecret') },
    body: { update_id: chatId, message: { text: `/start ${token}`, chat: { id: chatId, title: 'e2e chat' } } },
  });
});

Cypress.Commands.add('upgradeToPro', () =>
  cy.api('POST', '/api/billing/checkout', { plan: 'pro' }).then(({ body }) => {
    const session = new URL(body.url).searchParams.get('session');
    return cy.api('POST', '/api/billing/webhook', { type: 'checkout.completed', session_id: session });
  }),
);

/** Assert exactly these listing titles are on the page, in any order (retries until they are). */
export const expectListings = (expected: string[]) =>
  cy.get('[data-cy=listing] .listing__title').should((titles) => {
    expect([...titles].map((title) => title.textContent!.trim()).sort()).to.deep.equal([...expected].sort());
  });

/** Pick a segment (Buy/Rent, Flat/House) by its visible label, as a user does, and wait until it is selected. */
export const chooseSegment = (dataCy: string) => {
  cy.get(`[data-cy=${dataCy}]`).parent('label').click();
  cy.get(`[data-cy=${dataCy}]`).should('be.checked');
};

/** Open the app at `path` with the tour already seen, as a returning user would. */
export const visitAsReturning = (path: string) =>
  cy.visit(path, { onBeforeLoad: (win) => win.localStorage.setItem('metravo.introSeen', '1') });

export {};
