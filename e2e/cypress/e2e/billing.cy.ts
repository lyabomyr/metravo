import { uniqueEmail } from '../support/commands';

describe('Upgrading and cancelling', () => {
  beforeEach(() => cy.signIn(uniqueEmail('billing')));

  it('PLAN-1 free → pay → pro → cancel → free', () => {
    cy.visit('/billing');
    cy.get('[data-cy=plan-free] [data-cy=current-plan]').should('exist');
    cy.get('[data-cy=plan-pro]').should('contain', '$10');
    cy.get('[data-cy=upgrade]').click();
    cy.location('pathname').should('eq', '/billing/test-checkout');
    cy.get('[data-cy=test-pay]').click();

    cy.get('[data-cy=billing-success]').should('be.visible');
    cy.get('[data-cy=plan-badge]').should('have.text', 'pro');

    cy.visit('/billing');
    cy.get('[data-cy=manage-subscription]').click();
    cy.get('[data-cy=test-cancel]').click();
    cy.get('[data-cy=subscription-status]').should('contain', 'cancelled');
    cy.get('[data-cy=plan-badge]').should('have.text', 'free');
  });

  it('PLAN-2 cancelling at checkout keeps the plan and says so', () => {
    cy.visit('/billing');
    cy.get('[data-cy=upgrade]').click();
    cy.get('[data-cy=test-checkout-cancel]').click();
    cy.location('search').should('contain', 'status=cancelled');
    cy.get('[data-cy=billing-cancelled]').should('be.visible');
    cy.get('[data-cy=plan-badge]').should('have.text', 'free');
  });

  it('PLAN-3 leaving the subscription page without changes', () => {
    cy.upgradeToPro();
    cy.visit('/billing');
    cy.get('[data-cy=manage-subscription]').click();
    cy.get('[data-cy=test-portal-back]').click();
    cy.location('pathname').should('eq', '/billing');
    cy.get('[data-cy=plan-badge]').should('have.text', 'pro');
  });

  it('PLAN-4 Free is a week: the days left are shown, and the plan says so', () => {
    cy.visit('/listings');
    cy.get('[data-cy=free-week-left]').should('contain', '7 day(s) left');
    cy.visit('/billing');
    cy.get('[data-cy=plan-free]').should('contain', 'Free for 7 days');
    cy.api('GET', '/api/auth/me').its('body').should((me: { active: boolean; free_until: string }) => {
      expect(me.active).to.eq(true);
      expect(Date.parse(me.free_until) - Date.now()).to.be.within(6.9 * 864e5, 7 * 864e5);
    });
    cy.upgradeToPro();
    cy.reload();
    cy.get('[data-cy=free-week-left]').should('not.exist'); // Pro has no end date
  });
});
