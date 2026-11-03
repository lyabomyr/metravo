import { HttpErrorResponse, provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { Injectable } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { RuntimeConfig } from '../config/runtime-config';
import { BaseApiService, RETRY_DELAY_MS } from './base-api.service';

@Injectable({ providedIn: 'root' })
class ThingsApi extends BaseApiService {
  protected readonly path = '/api/things';
  list() {
    return this.get<string[]>();
  }
  add() {
    return this.post<string>();
  }
}

describe('BaseApiService', () => {
  let http: HttpTestingController;

  beforeEach(() => {
    vi.useFakeTimers();
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), { provide: RuntimeConfig, useValue: { apiUrl: 'http://api' } }],
    });
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => vi.useRealTimers());

  it('asks again when the server could not be reached, for reads', () => {
    let result: string[] | undefined;
    TestBed.inject(ThingsApi).list().subscribe((value) => (result = value));
    http.expectOne('http://api/api/things').error(new ProgressEvent('error'), { status: 0 });
    vi.advanceTimersByTime(RETRY_DELAY_MS);
    http.expectOne('http://api/api/things').flush(['ok']);
    expect(result).toEqual(['ok']);
  });

  it('passes a real refusal on at once', () => {
    let failure: HttpErrorResponse | undefined;
    TestBed.inject(ThingsApi).list().subscribe({ error: (error) => (failure = error) });
    http.expectOne('http://api/api/things').flush({ detail: 'no' }, { status: 403, statusText: 'Forbidden' });
    expect(failure?.status).toBe(403);
    http.verify();
  });

  it('never repeats a write', () => {
    let failure: HttpErrorResponse | undefined;
    TestBed.inject(ThingsApi).add().subscribe({ error: (error) => (failure = error) });
    http.expectOne('http://api/api/things').error(new ProgressEvent('error'), { status: 0 });
    vi.advanceTimersByTime(RETRY_DELAY_MS * 5);
    expect(failure?.status).toBe(0);
    http.verify();
  });
});
