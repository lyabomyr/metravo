import { uniqueEmail } from '../support/commands';

describe('Data export is available on every plan', () => {
  beforeEach(() => {
    cy.signIn(uniqueEmail('export'));
    cy.api('POST', '/api/searches', {
      name: 'Export test', city: 'krakow', max_price: 610000, min_area: 39, sources: ['otodom', 'morizon'],
    });
    cy.api('POST', '/api/scan/mine');
  });

  it('DATA-1 serves a real SQLite file and a CSV of listings', () => {
    cy.visit('/database');
    cy.get('[data-cy=db-name]').should('contain', 'u-');
    cy.get('[data-cy=download-db]').should('be.enabled');

    cy.api('GET', '/api/export/database.sqlite').then((response) => {
      expect(response.headers['content-disposition']).to.contain('metravo.sqlite');
      expect(String(response.body).startsWith('SQLite format 3')).to.equal(true);
    });
    cy.api('GET', '/api/export/listings.csv').then((response) => {
      const lines = String(response.body).trim().split('\n');
      expect(lines[0]).to.contain('price');
      expect(lines).to.have.length(4); // header + 3 matches from otodom and morizon
    });
  });
});
