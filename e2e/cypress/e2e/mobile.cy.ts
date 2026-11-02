import { DEFAULT_SEARCH, uniqueEmail } from '../support/commands';

const PAGES = ['/listings', '/searches', '/searches/new', '/alerts', '/database', '/billing'];

function noSidewaysScroll() {
  cy.window().should((win) => expect(win.document.documentElement.scrollWidth).to.be.at.most(win.innerWidth));
}

describe('On a phone', () => {
  beforeEach(() => cy.viewport(375, 812));

  it('MOB-1 navigates with the bottom tab bar', () => {
    cy.signIn(uniqueEmail('mobile'));
    cy.visit('/listings');
    cy.get('.tabs').should('have.css', 'position', 'fixed').and('have.css', 'bottom', '0px');
    cy.get('[data-cy=nav-searches]').click();
    cy.location('pathname').should('eq', '/searches');
    cy.get('[data-cy=nav-alerts]').click();
    cy.location('pathname').should('eq', '/alerts');
  });

  it('MOB-2 no page scrolls sideways', () => {
    cy.signIn(uniqueEmail('mobile'));
    cy.api('POST', '/api/searches', DEFAULT_SEARCH);
    cy.api('POST', '/api/scan/mine');
    PAGES.forEach((page) => {
      cy.visit(page);
      cy.get('h1').should('be.visible');
      noSidewaysScroll();
    });
  });

  it('MOB-3 the landing page fits the screen', () => {
    cy.visit('/');
    cy.get('[data-cy=email]').should('be.visible');
    noSidewaysScroll();
  });
});
