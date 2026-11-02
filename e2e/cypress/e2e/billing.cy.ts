import { uniqueEmail } from '../support/commands';

describe('Upgrading and cancelling', () => {
  beforeEach(() => cy.signIn(uniqueEmail('billing')));

  it('PLAN-1 free → pay → pro → cancel → free', () => {
    cy.visit('/billing');
    cy.get('[data-cy=plan-free] [data-cy=current-plan]').should('exist');
    cy.get('[data-cy=plan-pro]').should('contain', '$10');
    cy.get('[data-cy=upgrade]').click();
    cy.location('pathname').should('eq', '/billing/test-checkout');
    cy.get('[data-cy=test-pay]').click();

    cy.get('[data-cy=billing-success]').should('be.visible');
    cy.get('[data-cy=plan-badge]').should('have.text', 'pro');

    cy.visit('/billing');
    cy.get('[data-cy=manage-subscription]').click();
    cy.get('[data-cy=test-cancel]').click();
    cy.get('[data-cy=subscription-status]').should('contain', 'cancelled');
    cy.get('[data-cy=plan-badge]').should('have.text', 'free');
  });
});
