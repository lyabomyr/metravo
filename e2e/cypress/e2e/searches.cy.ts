import { uniqueEmail } from '../support/commands';

describe('Searches', () => {
  beforeEach(() => cy.signIn(uniqueEmail('searches')));

  it('creates and edits a search, and hits the free-plan limit on the second one', () => {
    cy.visit('/searches');
    cy.get('[data-cy=new-search]').click();
    cy.get('[data-cy=search-name]').clear().type('Katowice tanio');
    cy.get('[data-cy=search-city]').select('katowice');
    cy.get('[data-cy=search-max-price]').clear().type('400000');
    // Daily by default; faster checks are shown but belong to Pro.
    cy.get('[data-cy=search-interval]').find('option:selected').should('contain', 'Daily');
    cy.get('[data-cy=search-interval]').find('option').contains('Every 15 min').should('be.disabled');
    cy.get('[data-cy=search-interval]').select('Every 6 h');
    cy.get('[data-cy=search-save]').click();

    cy.location('pathname').should('eq', '/searches');
    cy.get('[data-cy=search-card]')
      .should('have.length', 1)
      .and('contain', 'Katowice tanio')
      .and('contain', 'katowice')
      .and('contain', 'Every 6 h');

    cy.get('[data-cy=new-search]').click();
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=error]').should('contain', '1 search');
    cy.get('[data-cy=upgrade-link]').should('have.attr', 'href', '/billing');
  });

  it('keeps Pro-only portals locked on the free plan', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=source-komornik]').check();
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=error]').should('contain', 'komornik');
  });
});
