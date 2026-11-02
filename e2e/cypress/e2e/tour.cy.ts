import { uniqueEmail } from '../support/commands';

const TITLES = [
  'Welcome to Metravo',
  'Searches — what to look for',
  'Alerts — where to send it',
  'Listings — everything we found',
  'Your data stays yours',
];

describe('First-run tour', () => {
  beforeEach(() => {
    cy.signIn(uniqueEmail('tour'), { tour: true });
    cy.visit('/listings');
  });

  it('TOUR-1/2 opens once, walks through five steps and stays closed', () => {
    cy.get('[data-cy=tour]').should('be.visible').and('contain', 'Step 1 of 5');
    TITLES.forEach((title, index) => {
      cy.get('[data-cy=tour-title]').should('contain', title);
      if (index < TITLES.length - 1) cy.get('[data-cy=tour-next]').click();
    });
    cy.contains('[data-cy=tour] button', 'Back').click();
    cy.get('[data-cy=tour-title]').should('contain', TITLES[3]);
    cy.get('[data-cy=tour-next]').click();
    cy.get('[data-cy=tour-done]').click();
    cy.get('[data-cy=tour]').should('not.exist');
    cy.reload();
    cy.get('[data-cy=nav-listings]').should('be.visible');
    cy.get('[data-cy=tour]').should('not.exist');
  });

  it('TOUR-3 Help opens it again', () => {
    cy.get('[data-cy=tour-skip]').click();
    cy.get('[data-cy=help]').click();
    cy.get('[data-cy=tour-title]').should('contain', TITLES[0]);
  });

  it('TOUR-4 Escape closes it', () => {
    cy.get('[data-cy=tour]').should('be.visible');
    cy.get('body').type('{esc}');
    cy.get('[data-cy=tour]').should('not.exist');
  });
});
