import { uniqueEmail } from '../support/commands';

describe('Renting, not buying', () => {
  beforeEach(() => cy.signIn(uniqueEmail('rent')));

  it('finds rentals under a monthly budget, with required keywords', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=deal-rent]').check();
    cy.get('[data-cy=search-max-price]').should('have.value', '4000'); // budget switched to a monthly one
    cy.get('[data-cy=source-komornik]').should('be.disabled'); // auctions are never rentals
    cy.get('[data-cy=search-name]').clear().type('Wynajem z balkonem');
    cy.get('[data-cy=search-min-area]').clear().type('25');
    cy.get('[data-cy=search-required]').type('balkon');
    cy.get('[data-cy=search-save]').click();

    cy.get('[data-cy=search-card]').should('contain', 'Rent flat').and('contain', '/ month');

    cy.visit('/listings');
    cy.get('[data-cy=scan-now]').click();
    cy.get('[data-cy=scan-report]').should('contain', '3 new');
    cy.get('[data-cy=listing]').should('have.length', 3).first().should('contain', 'zł / month');
  });
});
