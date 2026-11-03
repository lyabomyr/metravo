import { chooseSegment, pickPlace, uniqueEmail } from '../support/commands';

describe('Search form', () => {
  beforeEach(() => cy.signIn(uniqueEmail('form')));

  it('FORM-1 starts from sensible defaults', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=deal-sale]').should('be.checked');
    cy.get('[data-cy=property-flat]').should('be.checked');
    cy.get('[data-cy=place-name]').should('have.text', 'not chosen yet'); // no city is assumed
    cy.get('[data-cy=place-needed]').should('be.visible');
    cy.get('[data-cy=search-save]').should('be.disabled');
    cy.get('[data-cy=search-radius]').should('have.value', '0');
    cy.get('[data-cy=place-map]').should('be.visible');
    cy.get('[data-cy=search-interval]').find('option:selected').should('contain', 'Once a day');
    cy.get('[data-cy=search-max-price]').should('have.value', ''); // no limits: a new search tracks everything
    cy.get('[data-cy=search-min-area]').should('have.value', '');
    cy.get('[data-cy=search-required]').should('have.value', '');
    cy.get('[data-cy=search-reject]').should('contain.value', 'TBS'); // editable, prefilled
    ['otodom', 'olx', 'morizon'].forEach((source) => cy.get(`[data-cy=source-${source}]`).should('be.checked'));
    cy.get('[data-cy=source-komornik]').should('not.be.checked');
  });

  it('FORM-2 renting switches to a monthly price range and drops auctions', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=search-max-price]').type('600000');
    chooseSegment('deal-rent');
    cy.get('[data-cy=search-max-price]').should('have.value', ''); // a sale price is no monthly rent
    cy.get('[data-cy=source-komornik]').should('be.disabled');
    cy.get('[data-cy=search-max-price]').type('4000');
    chooseSegment('deal-sale');
    cy.get('[data-cy=search-max-price]').should('have.value', '');
    cy.get('[data-cy=source-komornik]').should('be.enabled');
  });

  it('FORM-3 Free checks once a day; faster rates are Pro', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=search-interval] option').should('have.length', 5);
    cy.get('[data-cy=search-interval] option:enabled').should('have.length', 1).and('contain', 'Once a day');
    cy.get('[data-cy=search-interval] option:disabled').first().should('contain', 'Every hour').and('contain', 'Pro');
  });

  it('FORM-4 Pro can check every hour', () => {
    cy.upgradeToPro();
    cy.visit('/searches/new');
    pickPlace('Kraków');
    cy.get('[data-cy=search-interval]').select('Every hour');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=search-alerts-done]').click(); // a new search opens its alerts first
    cy.get('[data-cy=search-card]').should('contain', 'Every hour');
  });

  it('FORM-5 refuses impossible searches with a clear message', () => {
    const cases: [Record<string, string>, string][] = [
      [{ 'search-min-area': '40', 'search-max-area': '30' }, 'Maximum area is below minimum area'],
      [{ 'search-max-price': '600000', 'search-min-price': '700000' }, '“Price from” is higher than “price up to”'],
    ];
    cases.forEach(([fields, message]) => {
      cy.visit('/searches/new');
      pickPlace('Kraków');
      Object.entries(fields).forEach(([field, value]) => cy.get(`[data-cy=${field}]`).type(value));
      cy.get('[data-cy=search-save]').click();
      cy.get('[data-cy=error]').should('contain', message);
      cy.location('pathname').should('eq', '/searches/new');
    });
    cy.visit('/searches/new');
    pickPlace('Kraków');
    cy.get('[data-cy=search-min-rooms]').type('3');
    cy.get('[data-cy=search-max-rooms]').type('2');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=error]').should('contain', 'Maximum rooms is below minimum rooms');
    cy.visit('/searches/new');
    pickPlace('Kraków');
    ['otodom', 'olx', 'morizon'].forEach((source) => cy.get(`[data-cy=source-${source}]`).uncheck());
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=error]').should('contain', 'Pick at least one portal');
  });

  it('FORM-6 edits and deletes a search', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=search-name]').clear().type('Katowice tanio');
    pickPlace('Katowice');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=search-alerts-done]').click(); // a new search opens its alerts first
    cy.get('[data-cy=search-card]').should('have.length', 1).and('contain', 'Katowice tanio').and('contain', 'Katowice');

    cy.get('[data-cy=search-edit]').click();
    cy.get('[data-cy=search-name]').should('have.value', 'Katowice tanio').clear().type('Katowice duże');
    cy.get('[data-cy=search-min-area]').clear().type('70');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=search-card]').should('contain', 'Katowice duże').and('contain', '70 m²');

    cy.get('[data-cy=search-delete]').click(); // the confirm dialog is accepted
    cy.get('[data-cy=search-card]').should('not.exist');
  });

  it('FORM-7 Free allows one search and offers an upgrade', () => {
    cy.api('POST', '/api/searches', { name: 'one', city: 'krakow', max_price: 1, min_area: 1, sources: ['otodom'] });
    cy.visit('/searches/new');
    pickPlace('Kraków');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=error]').should('contain', 'allows 1 search');
    cy.get('[data-cy=upgrade-link]').should('have.attr', 'href', '/billing');
  });

  it('FORM-9 a house search is saved as a house', () => {
    cy.visit('/searches/new');
    pickPlace('Kraków');
    cy.get('[data-cy=property-house]').parent('label').click();
    cy.get('[data-cy=property-house]').should('be.checked');
    cy.get('[data-cy=search-name]').clear().type('Dom pod Krakowem');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=search-alerts-done]').click(); // a new search opens its alerts first
    cy.get('[data-cy=search-card]').should('contain', 'Dom pod Krakowem').and('contain', 'House');
    cy.api('GET', '/api/searches').its('body.0.property_type').should('eq', 'house');
  });

  it('FORM-10 a new search starts from the empty page or the New button', () => {
    cy.visit('/searches');
    cy.get('[data-cy=create-first-search]').click();
    cy.location('pathname').should('eq', '/searches/new');
    cy.visit('/searches');
    cy.get('[data-cy=new-search]').click();
    cy.location('pathname').should('eq', '/searches/new');
    cy.get('[data-cy=search-save]').should('be.visible');
  });

  it('FORM-11 a village found by name, with a radius around it', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=place-query]').type('zab'); // suggestions come while typing, no button
    cy.get('[data-cy=place-result]').should('have.length', 1).and('contain', 'Zabierzów').click();
    cy.get('[data-cy=place-name]').should('have.text', 'Zabierzów');
    cy.get('[data-cy=search-radius]').select('15');
    cy.get('[data-cy=search-name]').clear().type('Pod Krakowem');
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=search-alerts-done]').click(); // a new search opens its alerts first
    cy.get('[data-cy=search-place]').should('contain', 'Zabierzów').and('contain', '+15 km');
    cy.api('GET', '/api/searches').its('body.0').should((search: { radius_km: number; place: { path: string } }) => {
      expect(search.radius_km).to.eq(15);
      expect(search.place.path).to.eq('malopolskie/krakowski/zabierzow/zabierzow');
    });
  });

  it('FORM-12 a place picked on the map, and a name that matches nothing', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=place-query]').type('Atlantyda');
    cy.get('[data-cy=place-none]').should('be.visible');
    pickPlace('Kraków');
    cy.get('[data-cy=place-query]').type('Katowice');
    cy.get('[data-cy=place-query]').clear(); // typed, then changed their mind
    cy.get('[data-cy=place-map]').click(); // the map is centred on Kraków
    cy.get('[data-cy=place-name]').should('have.text', 'Kraków');
  });

  it('FORM-13 the name is a hint, not text to delete', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=search-name]').should('have.value', '').and('have.attr', 'placeholder', 'Named after the place');
    pickPlace('Kraków');
    cy.get('[data-cy=search-name]').should('have.attr', 'placeholder', 'Kraków');
    cy.get('[data-cy=search-name]').type('Blisko pracy').should('have.value', 'Blisko pracy'); // typing replaces nothing
    cy.get('[data-cy=search-name]').clear();
    cy.get('[data-cy=search-save]').click();
    cy.get('[data-cy=search-alerts-done]').click(); // a new search opens its alerts first
    cy.get('[data-cy=search-card]').should('contain', 'Kraków'); // left empty, named after the place
  });

  it('FORM-8 bailiff auctions are Pro', () => {
    cy.visit('/searches/new');
    pickPlace('Kraków');
    cy.get('[data-cy=source-komornik]').parents('label').should('contain', 'Pro');
    cy.get('[data-cy=source-komornik]').check();
    cy.get('[data-cy=source-komornik]').should('be.checked'); // the list may redraw once the plan loads
    cy.get('[data-cy=search-save]').should('be.enabled').click();
    cy.get('[data-cy=error]').should('contain', 'komornik');
  });

  it('FORM-14 places are suggested while typing, with a spinner, and picked by keyboard', () => {
    cy.intercept('GET', '**/api/places?q=*', (request) => request.on('response', (response) => response.setDelay(600))).as('places');
    cy.visit('/searches/new');
    cy.get('[data-cy=place-query]').type('k');
    cy.get('[data-cy=place-loading]').should('not.exist'); // one letter is too little to ask
    cy.get('[data-cy=place-query]').type('ato');
    cy.get('[data-cy=place-loading]').should('be.visible');
    cy.wait('@places').its('request.url').should('contain', 'q=kato'); // one request for the whole word
    cy.get('[data-cy=place-loading]').should('not.exist');
    cy.get('[data-cy=place-result]').first().should('contain', 'Katowice');
    cy.get('[data-cy=place-query]').type('{enter}');
    cy.get('[data-cy=place-name]').should('have.text', 'Katowice');
    cy.get('[data-cy=place-query]').should('have.value', '');
    cy.get('@places.all').should('have.length', 1);
  });

  it('FORM-15 a placeholder steps aside as soon as a field is focused', () => {
    cy.visit('/searches/new');
    const placeholderColour = (el: JQuery<HTMLElement>) => getComputedStyle(el[0], '::placeholder').color;
    cy.get('[data-cy=search-max-price]').should((el) => expect(placeholderColour(el)).not.to.eq('rgba(0, 0, 0, 0)'));
    cy.get('[data-cy=search-max-price]').focus().should((el) => expect(placeholderColour(el)).to.eq('rgba(0, 0, 0, 0)'));
    cy.get('[data-cy=search-max-price]').type('5').should('have.value', '5');
  });

  it('FORM-16 suggested “must not mention” words read grey until edited', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=search-reject]').should('have.class', 'input--suggested').and('contain.value', 'TBS');
    cy.get('[data-cy=reject-suggested]').should('be.visible');
    cy.get('[data-cy=search-reject]').focus().should('contain.value', 'TBS'); // a value, not a hint: focus keeps it
    cy.get('[data-cy=search-reject]').type(', parter');
    cy.get('[data-cy=search-reject]').should('not.have.class', 'input--suggested');
    cy.get('[data-cy=reject-suggested]').should('not.exist');
  });
});
