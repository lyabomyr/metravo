/**
 * Shortcuts shared by every spec. UI journeys are tested once through the UI
 * (see sign-in-and-onboarding.cy.ts); everywhere else these set state directly.
 */

const api = (path: string) => `${Cypress.env('apiUrl')}${path}`;

/** A fresh address per test, so tests never depend on each other's data. */
export const uniqueEmail = (prefix = 'user') => `${prefix}-${Date.now()}-${Cypress._.random(1e6)}@metravo.test`;

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Cypress {
    interface Chainable {
      /** Sign in through the API and store the session like the app does. */
      signIn(email: string): Chainable<string>;
      /** Authorised API call with the stored session token. */
      api(method: string, path: string, body?: object): Chainable<Response<any>>;
      /** Play Telegram: the user pressed Start on a deep link. */
      telegramStart(deepLink: string, chatId: number): Chainable<Response<any>>;
    }
  }
}

Cypress.Commands.add('signIn', (email: string) =>
  cy
    .request('POST', api('/api/auth/session'), { provider: 'dev', credential: email })
    .then(({ body }) => {
      window.localStorage.setItem('metravo.token', body.token);
      return body.token as string;
    }),
);

Cypress.Commands.add('api', (method: string, path: string, body?: object) =>
  cy.request({
    method,
    url: api(path),
    body,
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

export {};
