import { uniqueEmail } from '../support/commands';

describe('Alerts', () => {
  let email: string;
  beforeEach(() => {
    email = uniqueEmail('alerts');
    cy.signIn(email);
  });

  it('ALR-1 connects and disconnects a Telegram chat', () => {
    cy.visit('/alerts');
    cy.get('[data-cy=no-chats]').should('be.visible');
    cy.get('[data-cy=telegram-open]')
      .should('have.attr', 'href')
      .then((href) => cy.telegramStart(String(href), Date.now() % 1e9));
    cy.get('[data-cy=telegram-chat]', { timeout: 10000 }).should('contain', 'e2e chat');
    cy.contains('[data-cy=telegram-chat] button', 'Disconnect').click();
    cy.get('[data-cy=no-chats]').should('be.visible');
  });

  it('ALR-2 extra channels are Pro on the Free plan', () => {
    cy.visit('/alerts');
    ['email', 'whatsapp', 'viber', 'signal'].forEach((code) => {
      cy.get(`[data-cy=channel-${code}]`).should('contain', 'Pro');
      cy.get(`[data-cy=channel-toggle-${code}]`).should('be.disabled');
    });
  });

  it('ALR-3 Pro switches WhatsApp on with a phone number', () => {
    cy.upgradeToPro();
    cy.visit('/alerts');
    cy.get('[data-cy=channel-whatsapp]').should('contain', 'soon');
    cy.get('[data-cy=channel-toggle-whatsapp]').check();
    cy.get('[data-cy=channel-address-whatsapp]').type('+48 600 100 200').blur();
    cy.get('[data-cy=channel-saved]').should('be.visible');
    cy.reload();
    cy.get('[data-cy=channel-toggle-whatsapp]').should('be.checked');
    cy.get('[data-cy=channel-address-whatsapp]').should('have.value', '+48 600 100 200');
  });

  it('ALR-4 email defaults to the account address', () => {
    cy.upgradeToPro();
    cy.visit('/alerts');
    cy.get('[data-cy=channel-toggle-email]').check();
    cy.get('[data-cy=channel-address-email]').should('have.value', email);
    cy.get('[data-cy=channel-saved]').should('be.visible');
    cy.api('GET', '/api/notifications/channels').its('body').should((channels: { code: string; enabled: boolean }[]) => {
      expect(channels.find((channel) => channel.code === 'email')?.enabled).to.equal(true);
    });
  });

  it('ALR-5 the old Telegram address still works', () => {
    cy.visit('/telegram');
    cy.location('pathname').should('eq', '/alerts');
  });
});
