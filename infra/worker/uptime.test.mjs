// node --test infra/worker
import assert from 'node:assert/strict';
import { test } from 'node:test';

import { nextState } from './uptime.js';

const up = { failures: 0, down: false };

test('one failed check is not an outage yet', () => {
  assert.deepEqual(nextState(up, 'HTTP 502'), { failures: 1, down: false, last_problem: 'HTTP 502' });
});

test('the second failure in a row marks it down', () => {
  assert.equal(nextState(nextState(up, 'HTTP 502'), 'HTTP 502').down, true);
});

test('a good check resets everything', () => {
  assert.deepEqual(nextState({ failures: 5, down: true }, null), up);
});
