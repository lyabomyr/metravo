import { uniqueEmail } from '../support/commands';

const SEARCH = { name: 'Export test', city: 'krakow', max_price: 610000, min_area: 39, sources: ['otodom', 'morizon'] };

describe('Listings export as CSV, on every plan', () => {
  it('DATA-1 the page offers a CSV with a header and one row per match', () => {
    cy.signIn(uniqueEmail('export'));
    cy.api('POST', '/api/searches', SEARCH);
    cy.api('POST', '/api/scan/mine');

    cy.visit('/database');
    cy.get('[data-cy=download-csv]').should('be.enabled');
    cy.api('GET', '/api/export/listings.csv').then((response) => {
      expect(response.headers['content-disposition']).to.contain('metravo-listings.csv');
      const lines = String(response.body).trim().split(/\r?\n/);
      expect(lines[0]).to.eq('search,source,title,price,area,rooms,price_per_m2,location,url,first_seen_at,last_seen_at');
      expect(lines).to.have.length(4); // header + 3 matches from otodom and morizon
      expect(lines[1]).to.match(/^Export test,/);
    });
  });

  it('DATA-2 another user gets none of those rows', () => {
    cy.signIn(uniqueEmail('export-a'));
    cy.api('POST', '/api/searches', SEARCH);
    cy.api('POST', '/api/scan/mine');

    cy.signIn(uniqueEmail('export-b'));
    cy.api('GET', '/api/searches').its('body').should('have.length', 0);
    cy.api('GET', '/api/listings').its('body').should('have.length', 0);
    cy.api('GET', '/api/export/listings.csv').then((response) => {
      expect(String(response.body).trim().split(/\r?\n/)).to.have.length(1); // the header alone
    });
  });
});
