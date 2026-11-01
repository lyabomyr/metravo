import { uniqueEmail } from '../support/commands';

describe('Upgrading unlocks direct access to your own database', () => {
  beforeEach(() => cy.signIn(uniqueEmail('billing')));

  it('free → pay → pro with credentials → cancel → free', () => {
    cy.visit('/database');
    cy.get('[data-cy=credentials-locked]').should('be.visible');

    cy.visit('/billing');
    cy.get('[data-cy=plan-free] [data-cy=current-plan]').should('exist');
    cy.get('[data-cy=upgrade]').click();
    cy.location('pathname').should('eq', '/billing/test-checkout');
    cy.get('[data-cy=test-pay]').click();

    cy.get('[data-cy=billing-success]').should('be.visible');
    cy.get('[data-cy=plan-badge]').should('have.text', 'pro');

    cy.visit('/database');
    cy.get('[data-cy=credentials-read]').click();
    cy.get('[data-cy=credentials]').should('contain', 'URL');

    cy.visit('/billing');
    cy.get('[data-cy=manage-subscription]').click();
    cy.get('[data-cy=test-cancel]').click();
    cy.get('[data-cy=subscription-status]').should('contain', 'cancelled');
    cy.get('[data-cy=plan-badge]').should('have.text', 'free');
  });
});
