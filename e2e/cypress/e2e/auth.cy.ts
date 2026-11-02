import { uniqueEmail, visitAsReturning } from '../support/commands';

describe('Sign-in and session', () => {
  it('AUTH-1 a new email gets an account and starts onboarding', () => {
    visitAsReturning('/');
    cy.get('[data-cy=email]').type(uniqueEmail('new'));
    cy.get('[data-cy=sign-in]').click();
    cy.location('pathname').should('eq', '/welcome');
    cy.api('GET', '/api/auth/me').its('body.plan').should('eq', 'free');
  });

  it('AUTH-2 a known email goes to the listings', () => {
    const email = uniqueEmail('known');
    cy.signIn(email);
    cy.clearLocalStorage('metravo.token');
    visitAsReturning('/');
    cy.get('[data-cy=email]').type(email);
    cy.get('[data-cy=sign-in]').click();
    cy.location('pathname').should('eq', '/listings');
    cy.get('[data-cy=user-email]').should('have.text', email);
  });

  it('AUTH-3 refuses an address without a domain', () => {
    visitAsReturning('/');
    cy.get('[data-cy=email]').type('anna@nowhere');
    cy.get('[data-cy=sign-in]').click();
    cy.get('[data-cy=error]').should('contain', 'valid email');
    cy.location('pathname').should('eq', '/');
  });

  it('AUTH-4 signing out returns to the landing page and locks the app', () => {
    cy.signIn(uniqueEmail('out'));
    cy.visit('/listings');
    cy.get('[data-cy=sign-out]').click();
    cy.location('pathname').should('eq', '/');
    cy.get('[data-cy=hero-title]').should('be.visible');
    cy.visit('/listings');
    cy.location('pathname').should('eq', '/');
  });

  it('AUTH-5 forgets a broken session', () => {
    visitAsReturning('/');
    cy.window().then((win) => win.localStorage.setItem('metravo.token', 'not-a-real-token'));
    cy.visit('/listings');
    cy.location('pathname').should('eq', '/');
    cy.window().its('localStorage').invoke('getItem', 'metravo.token').should('be.null');
  });

  it('AUTH-6 offers only the sign-in methods the backend enables', () => {
    visitAsReturning('/');
    cy.get('[data-cy=sign-in]').should('contain', 'Sign in'); // dev sign-in in e2e
    cy.get('[data-cy=google]').should('not.exist');
  });
});
