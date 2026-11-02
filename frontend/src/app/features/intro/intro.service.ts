import { Injectable, signal } from '@angular/core';

const SEEN_KEY = 'metravo.introSeen';

/** Whether the first-run tour is showing. It opens once by itself, and from “Help” any time. */
@Injectable({ providedIn: 'root' })
export class IntroService {
  readonly isOpen = signal(false);

  openIfFirstVisit(): void {
    if (!this.seen()) this.isOpen.set(true);
  }

  open(): void {
    this.isOpen.set(true);
  }

  close(): void {
    this.isOpen.set(false);
    try {
      localStorage.setItem(SEEN_KEY, '1');
    } catch {
      /* private mode: it may show once more next time */
    }
  }

  private seen(): boolean {
    try {
      return localStorage.getItem(SEEN_KEY) === '1';
    } catch {
      return false;
    }
  }
}
