import { Injectable } from '@angular/core';

/**
 * Deploy-time settings read from `/runtime-config.json`.
 *
 * Kept out of the build so one bundle works against any backend: CI writes
 * the file for each environment instead of rebuilding.
 */
@Injectable({ providedIn: 'root' })
export class RuntimeConfig {
  apiUrl = 'http://localhost:8000';

  async load(): Promise<void> {
    const response = await fetch('/runtime-config.json', { cache: 'no-store' });
    if (response.ok) {
      const values = (await response.json()) as Partial<RuntimeConfig>;
      this.apiUrl = (values.apiUrl ?? this.apiUrl).replace(/\/$/, '');
    }
  }
}
