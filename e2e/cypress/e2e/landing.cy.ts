import { uniqueEmail } from '../support/commands';

describe('Landing page', () => {
  beforeEach(() => cy.visit('/', { onBeforeLoad: (win) => win.localStorage.setItem('metravo.locale', 'en') }));

  it('LND-1 explains the product from top to bottom', () => {
    cy.get('[data-cy=hero-title]').should('contain', 'before anyone else calls');
    cy.get('.lnav a[href^="#"]').should('not.exist'); // no menu: the page reads top to bottom
    cy.contains('h2', 'Good flats are gone within hours').should('be.visible');
    cy.get('#how li').should('have.length', 3);
    cy.get('[data-cy=use-case]').should('have.length', 4).each((card) => {
      cy.wrap(card).find('img').should(($img) => expect(($img[0] as HTMLImageElement).naturalWidth).to.be.greaterThan(0));
    });
    cy.contains('h2', 'Everything in one place').should('exist');
    cy.get('#faq details').should('have.length', 6);
    cy.get('footer').should('contain', 'Wikimedia Commons');
  });

  it('LND-2 opens a FAQ answer', () => {
    cy.get('#faq details').first().as('question').should('not.have.attr', 'open');
    cy.get('@question').find('summary').click();
    cy.get('@question').should('have.attr', 'open');
    cy.get('@question').should('contain', 'one search checked once a day');
  });

  it('LND-3 sign-in buttons lead to the form', () => {
    cy.get('[data-cy=cta]').click();
    cy.focused().should('have.attr', 'data-cy', 'email');
    cy.scrollTo('bottom');
    cy.get('[data-cy=landing-sign-in]').click();
    cy.focused().should('have.attr', 'data-cy', 'email');
  });

  it('LND-4 speaks four languages and remembers the choice', () => {
    const headlines = { pl: 'Nowe mieszkania', uk: 'Нові квартири', ru: 'Новые квартиры', en: 'New flats' };
    for (const [code, text] of Object.entries(headlines)) {
      cy.get('[data-cy=language]').select(code);
      cy.get('[data-cy=hero-title]').should('contain', text);
    }
    cy.get('[data-cy=language]').select('pl');
    cy.reload();
    cy.get('[data-cy=hero-title]').should('contain', 'Nowe mieszkania');
    cy.get('html').should('have.attr', 'lang', 'pl');
  });

  it('LND-5 sends a signed-in user straight to the app', () => {
    cy.signIn(uniqueEmail('landing'));
    cy.visit('/');
    cy.location('pathname').should('eq', '/listings');
  });

  it('LND-6 shows both plans', () => {
    cy.get('#pricing [data-cy=plan-free]').should('contain', '$0').and('contain', 'Start free');
    cy.get('#pricing [data-cy=plan-pro]').should('contain', '$15').and('contain', 'WhatsApp, Viber, Signal');
    cy.get('#pricing [data-cy=plan-pro]').should('contain', 'Checked non-stop, every 5 minutes').and('contain', 'Otodom, OLX, Morizon, bailiff auctions');
    cy.get('#pricing [data-cy=plan-free]').should('contain', 'Otodom, OLX, Morizon').and('contain', 'Notifications in Telegram');
  });

  it('LND-7 on a phone, each icon and step number sits on its title line', () => {
    cy.viewport(375, 812);
    cy.get('.tile__head').should('have.length.at.least', 12).each((head) => {
      const title = head[0].getBoundingClientRect();
      const marker = head.find('.tile__icon, .step__number')[0].getBoundingClientRect();
      expect(marker.top, 'marker inside the title line').to.be.at.least(title.top - 1);
      expect(marker.bottom, 'marker inside the title line').to.be.at.most(title.bottom + 1);
      expect(marker.right, 'marker left of the title').to.be.lessThan(title.left + 48);
    });
    cy.get('[data-cy=how-step]').first().find('.tile__head').should('contain', '1').and('contain', 'Describe what you want');
  });
});
