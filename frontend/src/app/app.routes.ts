import { Routes } from '@angular/router';

import { adminGuard, signedInGuard, signedOutGuard } from './core/auth/guards';

/** Every page is lazy-loaded, so the first screen only downloads itself. */
export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    canActivate: [signedOutGuard],
    loadComponent: () => import('./features/landing/landing.page').then((m) => m.LandingPage),
  },
  { path: 'login', redirectTo: '' },
  { path: 'auth/finish', loadComponent: () => import('./features/auth/finish-sign-in.page').then((m) => m.FinishSignInPage) },
  {
    path: '',
    canActivate: [signedInGuard],
    children: [
      { path: 'welcome', loadComponent: () => import('./features/onboarding/onboarding.page').then((m) => m.OnboardingPage) },
      { path: 'listings', loadComponent: () => import('./features/listings/listings.page').then((m) => m.ListingsPage) },
      { path: 'searches', loadComponent: () => import('./features/searches/searches.page').then((m) => m.SearchesPage) },
      { path: 'searches/new', loadComponent: () => import('./features/searches/search-edit.page').then((m) => m.SearchEditPage) },
      { path: 'searches/:id', loadComponent: () => import('./features/searches/search-edit.page').then((m) => m.SearchEditPage) },
      { path: 'alerts', loadComponent: () => import('./features/alerts/alerts.page').then((m) => m.AlertsPage) },
      { path: 'telegram', redirectTo: 'alerts' },
      { path: 'database', loadComponent: () => import('./features/database/database.page').then((m) => m.DatabasePage) },
      { path: 'billing', loadComponent: () => import('./features/billing/billing.page').then((m) => m.BillingPage) },
      {
        path: 'billing/test-checkout',
        loadComponent: () => import('./features/billing/test-checkout.page').then((m) => m.TestCheckoutPage),
      },
      {
        path: 'billing/test-portal',
        loadComponent: () => import('./features/billing/test-portal.page').then((m) => m.TestPortalPage),
      },
      {
        path: 'admin',
        canActivate: [adminGuard],
        loadComponent: () => import('./features/admin/admin.page').then((m) => m.AdminPage),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];
