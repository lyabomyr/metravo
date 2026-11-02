// Uptime watcher — a Cloudflare Worker run by a cron trigger every 5 minutes.
//
// A server that is down cannot report itself, so this lives outside it. It
// checks the API and the website; after two failed checks in a row it tells
// the admins in Telegram, and tells them again when the service is back.
// Admin chats are looked up in the control database (users in ADMIN_EMAILS
// who linked Telegram), so there is nothing extra to configure.
//
// Deployed by OpenTofu (infra/terraform/monitoring.tf). State between runs
// lives in the KV namespace bound as STATE, written only when it changes.

const FAILURES_BEFORE_ALERT = 2;
const TIMEOUT_MS = 20000;

export default {
  async scheduled(_event, env, ctx) {
    ctx.waitUntil(checkAll(env));
  },

  // GET the worker's URL to see the last known state.
  async fetch(_request, env) {
    const states = {};
    for (const target of targets(env)) states[target.key] = await readState(env, target.key);
    return Response.json(states);
  },
};

function targets(env) {
  return [
    { key: 'api', name: 'API', url: `${env.API_URL}/api/health` },
    { key: 'site', name: 'Website', url: env.SITE_URL },
  ];
}

async function checkAll(env) {
  for (const target of targets(env)) {
    const problem = await probe(target.url);
    const before = await readState(env, target.key);
    const after = nextState(before, problem);
    if (after.down && !before.down) await alert(env, `🔴 ${target.name} is down: ${problem} (${target.url})`);
    if (!after.down && before.down) await alert(env, `🟢 ${target.name} is back up`);
    if (JSON.stringify(after) !== JSON.stringify(before)) await env.STATE.put(target.key, JSON.stringify(after));
  }
}

async function probe(url) {
  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(TIMEOUT_MS), headers: { 'user-agent': 'metravo-uptime' } });
    return response.ok ? null : `HTTP ${response.status}`;
  } catch (error) {
    return error.name === 'TimeoutError' ? `no answer in ${TIMEOUT_MS / 1000} s` : String(error.message || error);
  }
}

export function nextState(state, problem) {
  if (!problem) return { failures: 0, down: false };
  const failures = state.failures + 1;
  return { failures, down: state.down || failures >= FAILURES_BEFORE_ALERT, last_problem: problem };
}

async function readState(env, key) {
  return JSON.parse((await env.STATE.get(key)) || '{"failures":0,"down":false}');
}

async function alert(env, text) {
  const chats = await adminChats(env).catch((error) => {
    console.error('cannot read admin chats', error);
    return [];
  });
  for (const chatId of chats) {
    await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/sendMessage`, {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ chat_id: chatId, text: `🚨 Metravo: ${text}` }),
    });
  }
  console.log('alert', text, 'to', chats.length, 'chat(s)');
}

// Turso's HTTP API: https://docs.turso.tech/sdk/http/reference
async function adminChats(env) {
  const emails = env.ADMIN_EMAILS.split(',').map((email) => email.trim().toLowerCase()).filter(Boolean);
  if (!emails.length) return [];
  const sql = `SELECT t.chat_id FROM telegram_chats t JOIN users u ON u.id = t.user_id WHERE u.email IN (${emails.map(() => '?').join(',')})`;
  const response = await fetch(`${env.CONTROL_DB_URL.replace(/^libsql:/, 'https:')}/v2/pipeline`, {
    method: 'POST',
    headers: { authorization: `Bearer ${env.CONTROL_DB_TOKEN}`, 'content-type': 'application/json' },
    body: JSON.stringify({
      requests: [
        { type: 'execute', stmt: { sql, args: emails.map((value) => ({ type: 'text', value })) } },
        { type: 'close' },
      ],
    }),
  });
  const body = await response.json();
  return body.results[0].response.result.rows.map((row) => row[0].value);
}
