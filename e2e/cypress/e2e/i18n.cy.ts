import { pickPlace, uniqueEmail } from '../support/commands';

describe('Languages inside the app', () => {
  beforeEach(() => cy.signIn(uniqueEmail('i18n')));

  it('I18N-1 translates the app and keeps the account language in step', () => {
    cy.intercept('PUT', '**/api/auth/me/locale').as('saveLocale');
    cy.visit('/listings');
    const labels = { pl: 'Ogłoszenia', uk: 'Оголошення', ru: 'Объявления', en: 'Listings' };
    for (const [code, label] of Object.entries(labels)) {
      cy.get('[data-cy=language]').select(code);
      cy.get('[data-cy=nav-listings]').should('contain', label);
      cy.wait('@saveLocale').its('request.body').should('deep.equal', { locale: code });
    }
    cy.get('[data-cy=language]').select('uk');
    cy.wait('@saveLocale');
    cy.api('GET', '/api/auth/me').its('body.locale').should('equal', 'uk'); // Telegram will write in Ukrainian
  });

  it('I18N-2 errors from the server arrive in the chosen language', () => {
    cy.api('POST', '/api/searches', { name: 'one', city: 'krakow', max_price: 1, min_area: 1, sources: ['otodom'] });
    cy.visit('/searches/new');
    cy.get('[data-cy=language]').select('pl');
    pickPlace('Kraków');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=error]').should('contain', 'Plan Free pozwala');
    cy.get('[data-cy=upgrade-link]').should('contain', 'Przejdź na Pro');
  });
});
