import { DEFAULT_SEARCH, uniqueEmail } from '../support/commands';

describe('Listings', () => {
  beforeEach(() => cy.signIn(uniqueEmail('listings')));

  it('LST-1 explains what to do when there is nothing yet', () => {
    cy.visit('/listings');
    cy.get('[data-cy=no-listings]').should('contain', 'Check now').find('a').should('have.attr', 'href', '/searches');
  });

  it('LST-2/3 checks on demand and then respects the daily schedule', () => {
    cy.api('POST', '/api/searches', DEFAULT_SEARCH);
    cy.visit('/listings');
    cy.get('[data-cy=scan-now]').click();
    cy.get('[data-cy=scan-report]').should('contain', 'Checked 1 search(es): 4 new');

    cy.contains('[data-cy=listing]', '3 pokoje Wielicka').within(() => {
      cy.root().should('have.attr', 'target', '_blank').and('have.attr', 'href').and('contain', 'otodom');
      cy.root().should('contain', '555').and('contain', '50 m²').and('contain', '3 rooms').and('contain', '/m²').and('contain', 'otodom');
    });

    cy.get('[data-cy=scan-now]').click();
    cy.get('[data-cy=scan-report]').should('contain', 'Nothing to check right now');
    cy.get('[data-cy=listing]').should('have.length', 4);
  });
});
