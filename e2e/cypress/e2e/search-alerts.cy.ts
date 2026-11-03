import { pickPlace, uniqueEmail } from '../support/commands';

/** Telegram posts this when the bot joins a group through a "startgroup" link or a channel owner posts the code. */
const post = (update: object) =>
  cy.request({
    method: 'POST',
    url: `${Cypress.env('apiUrl')}/api/telegram/webhook`,
    headers: { 'X-Telegram-Bot-Api-Secret-Token': Cypress.env('telegramSecret') },
    body: { update_id: Date.now() % 1e9, ...update },
  });

describe('Notifications belong to a search', () => {
  beforeEach(() => cy.signIn(uniqueEmail('routes')));

  it('SAL-1 a new search goes straight to its notifications; a group connected there gets that search only', () => {
    cy.visit('/searches/new');
    pickPlace('Kraków');
    cy.get('[data-cy=search-name]').type('Dla rodziny');
    cy.get('[data-cy=search-save]').click();
    cy.location('pathname').should('match', /^\/searches\/[^/]+\/notifications$/);
    cy.contains('h1', 'Dla rodziny');
    cy.get('[data-cy=search-chats-none]').should('be.visible');
    cy.get('[data-cy=telegram-group]')
      .should('have.attr', 'href')
      .then((href) => {
        const token = new URL(String(href)).searchParams.get('startgroup');
        post({ message: { text: `/start@metravo_bot ${token}`, chat: { id: -7001, title: 'Rodzina' } } });
      });
    cy.contains('[data-cy=search-chat]', 'Rodzina', { timeout: 10000 }).should('contain', 'selected searches');
    cy.contains('[data-cy=search-chat]', 'Rodzina').find('[data-cy=search-chat-toggle]').should('be.checked');
    cy.get('[data-cy=search-alerts-done]').click();
    cy.location('pathname').should('eq', '/searches');
  });

  it('SAL-2 a chat that hears every search can be switched off for one', () => {
    cy.api('POST', '/api/searches', { name: 'Jedno', city: 'krakow', sources: ['otodom'] }).then(({ body: search }) => {
      cy.api('POST', '/api/telegram/link').then(({ body }) => cy.telegramStart(body.private_url, Date.now() % 1e9));
      cy.visit('/searches');
      cy.get('[data-cy=search-alerts]').click();
      cy.location('pathname').should('eq', `/searches/${search.id}/notifications`);
      cy.get('[data-cy=search-chat]').should('have.length', 1).and('contain', 'every search');
      cy.get('[data-cy=search-chat-toggle]').should('be.checked').uncheck();
      cy.get('[data-cy=search-chat]').should('contain', 'selected searches');
      cy.reload();
      cy.get('[data-cy=search-chat-toggle]').should('not.be.checked');
    });
  });

  it('SAL-3 a channel is connected by posting the code shown', () => {
    cy.api('POST', '/api/searches', { name: 'Kanał', city: 'krakow', sources: ['otodom'] }).then(({ body: search }) => {
      cy.visit(`/searches/${search.id}/notifications`);
      cy.get('[data-cy=telegram-channel]').click();
      cy.get('[data-cy=telegram-channel-steps] a').should('have.attr', 'href').and('contain', 'startchannel');
      cy.get('[data-cy=telegram-channel-code]')
        .invoke('text')
        .then((code) => post({ channel_post: { text: code.trim(), chat: { id: -1009001, title: 'Mieszkania' } } }));
      cy.contains('[data-cy=search-chat]', 'Mieszkania', { timeout: 10000 }).find('[data-cy=search-chat-toggle]').should('be.checked');
    });
  });

  it('SAL-4 a search that finds nothing says why on its card', () => {
    cy.api('POST', '/api/searches', { name: 'Za tanio', city: 'krakow', max_price: 1, sources: ['otodom'] });
    cy.api('POST', '/api/scan/mine');
    cy.visit('/searches');
    cy.get('[data-cy=search-outcome]').should('contain', 'found').and('contain', '0 fit').and('contain', 'price limits');
  });
});
