import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { SessionStore } from './core/auth/session.store';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, RouterLink, RouterLinkActive],
  templateUrl: './app.html',
})
export class App {
  protected readonly session = inject(SessionStore);
  private readonly router = inject(Router);

  protected signOut(): void {
    this.session.signOut();
    this.router.navigateByUrl('/login');
  }
}
