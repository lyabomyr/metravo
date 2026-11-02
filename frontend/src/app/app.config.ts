import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, inject, provideAppInitializer, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter, withComponentInputBinding, withViewTransitions } from '@angular/router';

import { routes } from './app.routes';
import { authInterceptor } from './core/auth/auth.interceptor';
import { I18nService } from './core/i18n/i18n.service';
import { SessionStore } from './core/auth/session.store';
import { PublicConfigService } from './core/config/public-config.service';
import { RuntimeConfig } from './core/config/runtime-config';

/** Startup order matters: where the API is → what it offers → who is signed in. */
async function bootstrap(): Promise<void> {
  const i18n = inject(I18nService);
  const runtime = inject(RuntimeConfig);
  const publicConfig = inject(PublicConfigService);
  const session = inject(SessionStore);
  await Promise.all([i18n.init(), runtime.load()]);
  await publicConfig.load();
  await session.restore();
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes, withComponentInputBinding(), withViewTransitions()),
    provideHttpClient(withInterceptors([authInterceptor])),
    provideAppInitializer(bootstrap),
  ],
};
