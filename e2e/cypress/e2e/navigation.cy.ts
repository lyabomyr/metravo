import { uniqueEmail } from '../support/commands';

const TABS = [
  ['nav-searches', '/searches'],
  ['nav-alerts', '/notifications'],
  ['nav-database', '/database'],
  ['nav-billing', '/billing'],
  ['nav-listings', '/listings'],
] as const;

describe('Navigation', () => {
  it('NAV-1 every tab opens its page', () => {
    cy.signIn(uniqueEmail('nav'));
    cy.finishSetup();
    cy.visit('/listings');
    TABS.forEach(([tab, path]) => {
      cy.get(`[data-cy=${tab}]`).click();
      cy.location('pathname').should('eq', path);
      cy.get(`[data-cy=${tab}]`).should('have.class', 'active');
      cy.get('h1').should('be.visible');
    });
  });

  it('NAV-2 signing out returns to the landing page and closes the app', () => {
    cy.signIn(uniqueEmail('signout'));
    cy.visit('/searches');
    cy.get('[data-cy=sign-out]').click();
    cy.location('pathname').should('eq', '/');
    cy.get('[data-cy=email]').should('be.visible');
    cy.visit('/searches');
    cy.location('pathname').should('eq', '/');
  });
});
