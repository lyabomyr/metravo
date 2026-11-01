import { uniqueEmail } from '../support/commands';

describe('Service management', () => {
  it('is hidden from regular users', () => {
    cy.signIn(uniqueEmail('regular'));
    cy.visit('/admin');
    cy.location('pathname').should('eq', '/listings');
    cy.get('[data-cy=nav-admin]').should('not.exist');
  });

  it('shows accounts and can change a plan for admins', () => {
    const customer = uniqueEmail('customer');
    cy.signIn(customer);
    cy.signIn(Cypress.env('adminEmail'));
    cy.visit('/admin');
    cy.get('[data-cy=admin-users]').invoke('text').then(Number).should('be.gte', 2);
    cy.contains('[data-cy=admin-user-row]', customer).within(() => cy.contains('Make pro').click());
    cy.contains('[data-cy=admin-user-row]', customer).find('td').eq(1).should('have.text', 'pro');
  });
});
