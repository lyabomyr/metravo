import { uniqueEmail, visitAsReturning } from '../support/commands';

describe('First visit: sign in, save a search, connect Telegram, see listings', () => {
  it('ONB-1 takes a new user from the landing page to their first listings', () => {
    const email = uniqueEmail('onboarding');
    visitAsReturning('/');
    cy.get('[data-cy=email]').type(email);
    cy.get('[data-cy=sign-in]').click();

    // Step 1 — the defaults are fine, one click saves them.
    cy.location('pathname').should('eq', '/welcome');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=onboarding-search-saved]').should('be.visible');

    // Step 2 — the button is a real t.me deep link; Telegram's Start is played by the test.
    cy.get('[data-cy=telegram-open]')
      .should('have.attr', 'href')
      .and('match', /^https:\/\/t\.me\/\w+\?start=/)
      .then((href) => cy.telegramStart(String(href), Date.now() % 1e9));
    cy.get('[data-cy=onboarding-done]', { timeout: 10000 }).should('be.visible');

    cy.get('[data-cy=nav-listings]').click();
    cy.get('[data-cy=scan-now]').click();
    cy.get('[data-cy=scan-report]').should('contain', '4 new');
    cy.get('[data-cy=listing]').should('have.length', 4);
    cy.get('[data-cy=user-email]').should('have.text', email);
  });
});
