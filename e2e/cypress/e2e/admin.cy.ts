import { uniqueEmail } from '../support/commands';

describe('Service management', () => {
  it('ADM-1 is hidden from regular users', () => {
    cy.signIn(uniqueEmail('regular'));
    cy.visit('/admin');
    cy.location('pathname').should('eq', '/listings');
    cy.get('[data-cy=nav-admin]').should('not.exist');
  });

  it('ADM-2 shows accounts and can change a plan for admins', () => {
    const customer = uniqueEmail('customer');
    cy.signIn(customer);
    cy.signIn(Cypress.env('adminEmail'));
    cy.visit('/admin');
    cy.get('[data-cy=admin-users]').invoke('text').then(Number).should('be.gte', 2);
    cy.contains('[data-cy=admin-user-row]', customer).within(() => cy.contains('Make pro').click());
    cy.contains('[data-cy=admin-user-row]', customer).find('td').eq(1).should('have.text', 'pro');
  });

  it('ADM-3 shows the health of the running instance', () => {
    cy.signIn(Cypress.env('adminEmail'));
    cy.visit('/admin');
    cy.get('[data-cy=system-health]').within(() => {
      cy.get('[data-cy=memory]').should('contain', 'Memory').and('contain', 'MB');
      cy.get('[data-cy=cpu]').should('contain', 'CPU');
      cy.get('[data-cy=alerts]').should('contain', 'Active alerts');
      cy.contains('Recent warnings and errors').should('exist');
    });
  });

  it('ADM-4 refreshes health and runs a scan for everyone', () => {
    cy.signIn(uniqueEmail('scanned'));
    cy.api('POST', '/api/searches', { name: 'Admin scan', city: 'krakow', max_price: 600000, min_area: 40, sources: ['otodom'] });
    cy.signIn(Cypress.env('adminEmail'));
    cy.visit('/admin');
    cy.get('[data-cy=system-refresh]').click();
    cy.get('[data-cy=memory]').should('contain', 'MB');
    cy.get('[data-cy=scan-all]').click();
    cy.get('[data-cy=scan-all-report]').should('contain', 'searches').and('contain', 'page fetches');
  });
});
