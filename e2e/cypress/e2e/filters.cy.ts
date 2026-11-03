import { DEFAULT_MATCHES, chooseSegment, expectListings, pickPlace, uniqueEmail } from '../support/commands';

const WIELICKA_OTODOM = '3 pokoje Wielicka';
const WIELICKA_MORIZON = 'Wielicka 3 pokoje';
const DLUGA = '2 pokoje przy Długiej';
const BRONOWICE = '2 pokoje Bronowice';
const NOWA_HUTA = 'Duże mieszkanie Nowa Huta';

/** The search the fixture table is written for: ≤ 600 000 zł, ≥ 40 m² (a new search has no limits). */
const FIXTURE_SEARCH = { 'search-max-price': '600000', 'search-min-area': '40' };
const FIXTURE_RENT = { 'search-max-price': '4000' };

/** Fill the form like a user, save, then press “Check now”. */
function searchFor(fields: Record<string, string>, options: { only?: string[]; extra?: string[]; rent?: boolean; noLimits?: boolean } = {}) {
  cy.visit('/searches/new');
  pickPlace('Kraków');
  if (options.rent) chooseSegment('deal-rent');
  const base = options.noLimits ? {} : options.rent ? FIXTURE_RENT : FIXTURE_SEARCH;
  for (const [field, value] of Object.entries({ ...base, ...fields })) cy.get(`[data-cy=${field}]`).clear().type(value);
  if (options.only) {
    ['otodom', 'olx', 'morizon'].filter((source) => !options.only!.includes(source)).forEach((source) => cy.get(`[data-cy=source-${source}]`).uncheck());
  }
  options.extra?.forEach((source) => cy.get(`[data-cy=source-${source}]`).check());
  cy.get('[data-cy=search-save]').click();
  cy.get('[data-cy=search-alerts-done]').click(); // a new search opens its notifications first
  cy.location('pathname').should('eq', '/searches');
  cy.visit('/listings');
  cy.get('[data-cy=scan-now]').click();
  cy.get('[data-cy=scan-report]').should('contain', 'new');
}

describe('Every filter changes what arrives', () => {
  beforeEach(() => cy.signIn(uniqueEmail('filter')));

  it('FLT-1 defaults: within price and size, no TBS, no duplicates', () => {
    searchFor({});
    expectListings(DEFAULT_MATCHES);
    cy.contains('Penthouse').should('not.exist');
    cy.contains('TBS').should('not.exist');
    cy.contains('Kawalerka Czyżyny').should('not.exist');
    cy.contains(WIELICKA_MORIZON).should('not.exist');
  });

  it('FLT-14 a new search without limits tracks everything but TBS and duplicates', () => {
    searchFor({}, { noLimits: true });
    expectListings([...DEFAULT_MATCHES, 'Penthouse', 'Kawalerka Czyżyny']);
    cy.contains('TBS').should('not.exist');
    cy.contains(WIELICKA_MORIZON).should('not.exist');
  });

  it('FLT-15 “must not mention” can be changed: emptied, TBS comes back', () => {
    cy.visit('/searches/new');
    cy.get('[data-cy=search-reject]').should('contain.value', 'TBS');
    searchFor({ 'search-reject': ' ' });
    cy.contains('TBS').should('exist');
  });

  it('FLT-2 price up to', () => {
    searchFor({ 'search-max-price': '520000' });
    expectListings([DLUGA, BRONOWICE]);
  });

  it('FLT-3 minimum price', () => {
    searchFor({ 'search-min-price': '550000' });
    expectListings([WIELICKA_OTODOM, NOWA_HUTA]);
  });

  it('FLT-4 minimum area', () => {
    searchFor({ 'search-min-area': '50' });
    expectListings([WIELICKA_OTODOM, NOWA_HUTA]);
  });

  it('FLT-5 maximum area', () => {
    searchFor({ 'search-max-area': '45' });
    expectListings([DLUGA, BRONOWICE]);
  });

  it('FLT-6 rooms from — unknown room counts are kept', () => {
    searchFor({ 'search-min-rooms': '3' });
    expectListings([WIELICKA_OTODOM, NOWA_HUTA, BRONOWICE]);
  });

  it('FLT-7 rooms up to', () => {
    searchFor({ 'search-max-rooms': '2' });
    expectListings([DLUGA, BRONOWICE]);
  });

  it('FLT-8 price per m²', () => {
    searchFor({ 'search-max-per-m2': '11000' });
    expectListings([NOWA_HUTA]);
  });

  it('FLT-9 built after — the twin without a year takes the place of the rejected copy', () => {
    searchFor({ 'search-build-year': '2020' });
    expectListings([DLUGA, BRONOWICE, NOWA_HUTA, WIELICKA_MORIZON]);
  });

  it('FLT-10 must mention cannot drop an offer whose description we never saw', () => {
    // Results pages show titles only; a missing word there proves nothing.
    searchFor({ 'search-required': 'Bronowice' });
    expectListings(DEFAULT_MATCHES);
  });

  it('FLT-11 one portal only', () => {
    searchFor({}, { only: ['olx'] });
    expectListings([BRONOWICE]);
    cy.get('[data-cy=listing]').should('contain', 'OLX');
  });

  it('FLT-12 Pro adds bailiff auctions', () => {
    cy.upgradeToPro();
    searchFor({}, { extra: ['komornik'] });
    expectListings([...DEFAULT_MATCHES, 'Mieszkanie 48,5 m2 w Krakowie']);
  });

  it('FLT-13 rentals with a required word keep title-only offers', () => {
    searchFor({ 'search-min-area': '25', 'search-required': 'winda' }, { rent: true });
    expectListings(['Kawalerka z balkonem', '2 pokoje, balkon, winda', '3 pokoje Ruczaj, balkon']);
  });
});
