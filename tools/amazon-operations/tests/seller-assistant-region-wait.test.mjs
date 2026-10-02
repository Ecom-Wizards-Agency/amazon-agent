import '../../report-fetcher/test/helpers/isolated-runtime.mjs';
import { spawn } from 'node:child_process';
import { mkdtemp, mkdir, readFile, writeFile, rm, readdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { setTimeout as delay } from 'node:timers/promises';
import test from 'node:test';
import assert from 'node:assert/strict';
import * as scopes from '../../browserctl/context-scopes.mjs';
import * as SA from '../seller-assistant.mjs';

// The Seller Assistant controller on 9222 waits for its Seller Central region
// while another attended session holds it, for a bounded time and visibly.

const HERE = dirname(fileURLToPath(import.meta.url));
const SCRIPT = join(HERE, '..', 'seller-assistant.mjs');
const HOOKS = join(HERE, 'fixtures', 'fake-cdp-hooks.mjs');
const REGISTRY = join(process.env.AMAZON_BROWSER_RUNTIME_DIR, 'leases.json');
const SC = 'https://sellercentral.amazon.com';
const ACCOUNT = { profile_key: 'acme-us', client_slug: 'acme', marketplace: 'US', seller_id: 'A1TEST', marketplace_id: 'ATVPDKIKX0DER', seller_central_name: 'Acme', marketplace_label: 'United States', parent_account_name: 'Acme Group' };
const HOLDER_TASK = 'seller-central-region:0123456789abcdef0123';
const HOLDER_KEY = `9222:${encodeURIComponent(HOLDER_TASK)}:primary`;
const HOLDER_TOKEN = '00000000-0000-4000-8000-00000000c0de';
const HOLDER_OWNER = 'region-step.mjs:4242';
const OPERATOR = { CDP_PORT: '9222', AMAZON_BROWSER_SESSION: 'operator' };
const GRIMOIRE = { CDP_PORT: '9223', AMAZON_BROWSER_SESSION: 'grimoire' };

async function runDir() {
  const dir = await mkdtemp(join(tmpdir(), 'seller-assistant-region-'));
  await writeFile(join(dir, 'run.json'), JSON.stringify({ schema_version: 1, run_id: 'sa-region-test', account: ACCOUNT }));
  return dir;
}
const readJson = async path => { try { return JSON.parse(await readFile(path, 'utf8')); } catch { return null; } };
async function until(check, timeoutMs = 15000) {
  const end = Date.now() + timeoutMs;
  for (;;) {
    const value = await check();
    if (value) return value;
    if (Date.now() > end) throw new Error('condition not reached in time');
    await delay(25);
  }
}
async function withEnv(vars, fn) {
  const saved = Object.fromEntries(Object.keys(vars).map(key => [key, process.env[key]]));
  Object.assign(process.env, vars);
  try { return await fn(); } finally {
    for (const [key, value] of Object.entries(saved)) { if (value === undefined) delete process.env[key]; else process.env[key] = value; }
  }
}
async function captureLog(lines, fn) {
  const original = console.log;
  console.log = (...args) => lines.push(args.join(' '));
  try { return await fn(); } finally { console.log = original; }
}

/** The task record of the session holding the US region, as listTaskTabs returns it. */
function holderRecord(now) {
  return { key: HOLDER_KEY, port: 9222, taskId: HOLDER_TASK, slot: 'primary', workflow: 'seller-central-region', exclusiveContext: true,
    contextScope: 'sc:na', regionScope: 'sc:na', state: 'bound', targetId: 'HOLDER-TARGET', bindingGeneration: 1,
    controller: { token: HOLDER_TOKEN, owner: HOLDER_OWNER, heartbeatAt: now - 4000, expiresAt: now + 600000 } };
}
/** What task-tabs throws when reserveTaskTab answers browser-context-busy. */
function busyError() {
  return Object.assign(new Error('TASK_TAB_BUSY: browser-context-busy: sc:na on port 9222'),
    { code: 'TASK_TAB_BUSY', retryAt: Date.now() + 60000, blockingScope: 'sc:na', blockingTask: HOLDER_KEY });
}

/** Browser modules for serve: the region is busy while busy() is true.
 * `atSwitch` records whether serve.json existed when the account switch began. */
function fakeBrowser(busy, dir = null) {
  const calls = [], atSwitch = [];
  const session = { assertTaskControl: async () => {}, send: async () => ({}) };
  const page = { port: 9222, targetId: 'SA-TARGET', session };
  const B = {
    tabs: {
      taskIdFor: (workflow, key) => `${workflow}:${key}`,
      acquireTaskPage: async spec => { calls.push(['acquire', spec.taskId]); if (busy()) throw busyError(); return page; },
      releaseTaskPage: async (_handle, { outcome }) => { calls.push(['release', outcome]); return {}; },
    },
    sc: {
      switchAccount: async () => { calls.push(['switch']); if (dir) atSwitch.push(existsSync(join(dir, 'serve.json'))); },
      readIdentity: async () => ({ merchantId: ACCOUNT.seller_id, marketplace: ACCOUNT.marketplace_id }),
    },
    ui: { origins: { US: SC }, snapshot: async () => ({ url: `${SC}/home` }), contextMatches: () => true },
    cases: { caseBrowserAccount: account => ({ ...account }) },
    registry: { listTaskTabs: async () => [holderRecord(Date.now())] },
    policy: { loadBrowserPolicy: () => ({ cleanup: { heartbeat_interval_ms: 30000 } }) },
    lock: { acquireSessionLock: (port, owner) => { calls.push(['lock', port, owner]); return () => calls.push(['unlock', port]); } },
    cdp: { listPages: async () => [], evaluate: async () => null },
    scopes,
  };
  return { B, calls, atSwitch };
}

test('serve accepts --region-wait-minutes from 0 to 240 and defaults to 3', () => {
  assert.equal(SA.parseArgs(['serve', '--run', 'r']).regionWaitMinutes, 3);
  assert.equal(SA.parseArgs(['serve', '--run', 'r', '--region-wait-minutes', '0']).regionWaitMinutes, 0);
  assert.equal(SA.parseArgs(['serve', '--run', 'r', '--region-wait-minutes', '0.5']).regionWaitMinutes, 0.5);
  assert.equal(SA.parseArgs(['serve', '--run', 'r', '--region-wait-minutes', '240']).regionWaitMinutes, 240);
  for (const bad of ['-1', 'abc', '241', '1e3', '']) {
    assert.throws(() => SA.parseArgs(['serve', '--run', 'r', '--region-wait-minutes', bad]), error => error.code === 'usage', bad);
  }
});

test('on 9222 a held region makes serve wait visibly, refuse sends with waiting_for_region, and serve once the region is free', async () => {
  const dir = await runDir();
  let free = false;
  const { B, calls, atSwitch } = fakeBrowser(() => !free, dir);
  const lines = [];
  try {
    await withEnv(OPERATOR, () => captureLog(lines, async () => {
      const served = SA.serve({ run: dir, maxMinutes: 5, idleMinutes: 0, regionWaitMinutes: 1 }, { loadDeps: async () => B, regionPollMs: 20 });
      const waiting = await until(async () => { const status = await readJson(join(dir, 'serve.json')); return status?.status === 'waiting_for_region' && status; });
      assert.equal(waiting.pid, process.pid);
      assert.equal(waiting.session, 'operator');
      assert.equal(waiting.port, 9222);
      assert.equal(waiting.region_scope, 'sc:na');
      assert.equal(waiting.task_id, 'amazon-communications:seller-assistant:sa-region-test');
      assert.equal(waiting.holder.blocking_scope, 'sc:na');
      assert.equal(waiting.holder.owner, HOLDER_OWNER);
      assert.equal(waiting.holder.workflow, 'seller-central-region');
      assert.equal(waiting.holder.task_id, HOLDER_TASK);
      assert.ok(waiting.holder.heartbeat_age_s >= 4 && waiting.holder.heartbeat_age_s < 60, 'heartbeat age in seconds');
      assert.equal(Date.parse(waiting.wait_until) - Date.parse(waiting.waiting_since), 60000);
      assert.ok(!JSON.stringify(waiting).includes(HOLDER_TOKEN), 'the holder control token is never written');
      // The file is refreshed while the wait lasts.
      await until(async () => (await readJson(join(dir, 'serve.json')))?.updated_at > waiting.updated_at);
      assert.equal(existsSync(join(dir, 'serve.pid')), true);

      const answers = [];
      const code = await SA.sendCommand({ run: dir, command: 'state', args: {} }, { pollMs: 10, out: line => answers.push(JSON.parse(line)) });
      assert.equal(code, 2);
      assert.equal(answers.length, 1);
      assert.equal(answers[0].status, 'error');
      assert.equal(answers[0].reason, 'waiting_for_region', 'a send during the wait names the wait');
      assert.equal(answers[0].holder.owner, HOLDER_OWNER);
      assert.equal(answers[0].wait_until, waiting.wait_until);
      assert.deepEqual(await readdir(join(dir, 'queue')), [], 'nothing was queued');

      free = true;
      assert.equal(await served, 0, 'the idle budget ends the run with exit 0');
    }));
    assert.deepEqual(lines.map(line => JSON.parse(line).status), ['waiting_for_region', 'serving'], 'one line when the wait starts, then serving');
    const acquires = calls.filter(([name]) => name === 'acquire').length;
    assert.ok(acquires >= 3, `the controller retried (${acquires} attempts)`);
    assert.deepEqual(calls.filter(([name]) => name !== 'acquire'), [['switch'], ['release', 'error']], 'no session lock on 9222; one release');
    assert.deepEqual(atSwitch, [false], 'the waiting status is gone once the page is acquired');
    const final = await readJson(join(dir, 'serve.json'));
    assert.deepEqual([final.status, final.reason], ['stopped', 'idle_minutes']);
    assert.equal(existsSync(join(dir, 'serve.pid')), false);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('on 9222 a region held past the wait ends with region_busy, exit 1 and nothing acquired', async () => {
  const dir = await runDir();
  const { B, calls } = fakeBrowser(() => true);
  const lines = [];
  try {
    const code = await withEnv(OPERATOR, () => captureLog(lines, () =>
      SA.serve({ run: dir, regionWaitMinutes: 0.002 }, { loadDeps: async () => B, regionPollMs: 20 })));
    assert.equal(code, 1);
    const status = await readJson(join(dir, 'serve.json'));
    assert.equal(status.status, 'error');
    assert.equal(status.reason, 'region_busy');
    assert.equal(status.port, 9222);
    assert.equal(status.region_scope, 'sc:na');
    assert.deepEqual([status.holder.owner, status.holder.workflow, status.holder.task_id, status.holder.blocking_scope], [HOLDER_OWNER, 'seller-central-region', HOLDER_TASK, 'sc:na']);
    assert.equal(typeof status.holder.heartbeat_age_s, 'number');
    assert.ok(status.waited_s >= 0);
    assert.ok(!JSON.stringify(status).includes(HOLDER_TOKEN));
    assert.deepEqual(lines.map(line => JSON.parse(line).status), ['waiting_for_region', 'error']);
    assert.equal(JSON.parse(lines[1]).reason, 'region_busy');
    assert.ok(calls.filter(([name]) => name === 'acquire').length >= 2, 'it retried before giving up');
    assert.deepEqual(calls.filter(([name]) => name !== 'acquire'), [], 'no page, no switch, no release, no lock');
    assert.equal(existsSync(join(dir, 'serve.pid')), false);
    // Zero minutes: the first busy answer ends the run, without a waiting line.
    lines.length = 0;
    assert.equal(await withEnv(OPERATOR, () => captureLog(lines, () =>
      SA.serve({ run: dir, regionWaitMinutes: 0 }, { loadDeps: async () => B, regionPollMs: 20 }))), 1);
    assert.deepEqual(lines.map(line => JSON.parse(line).reason), ['region_busy']);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a command queued just before the wait began is cancelled with waiting_for_region, never run later', async () => {
  const dir = await runDir();
  try {
    for (const sub of ['queue', 'results']) await mkdir(join(dir, sub));
    await writeFile(join(dir, 'serve.pid'), JSON.stringify({ pid: process.pid }));
    const answers = [];
    const sent = SA.sendCommand({ run: dir, command: 'state', args: {} }, { pollMs: 10, out: line => answers.push(JSON.parse(line)) });
    await until(() => existsSync(join(dir, 'queue', '001.json')));
    await writeFile(join(dir, 'serve.json'), JSON.stringify({ status: 'waiting_for_region', pid: process.pid, port: 9222, region_scope: 'sc:na' }));
    assert.equal(await sent, 2);
    assert.deepEqual([answers[0].status, answers[0].reason, answers[0].id], ['cancelled', 'waiting_for_region', '001']);
    const result = await readJson(join(dir, 'results', '001.json'));
    assert.deepEqual([result.status, result.reason], ['cancelled', 'waiting_for_region'], 'serve skips it once it serves');
    // A waiting status of another process is not this controller's.
    await writeFile(join(dir, 'serve.json'), JSON.stringify({ status: 'waiting_for_region', pid: process.pid + 1 }));
    await writeFile(join(dir, 'results', '002.json'), JSON.stringify({ schema_version: 1, id: '002', status: 'ok' }));
    answers.length = 0;
    assert.equal(await SA.sendCommand({ run: dir, command: 'state', args: {} }, { pollMs: 10, out: line => answers.push(JSON.parse(line)) }), 0);
    assert.equal(answers[0].status, 'ok');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('on 9223 nothing changes: a busy region fails at once under the session lock', async () => {
  const dir = await runDir();
  const { B, calls } = fakeBrowser(() => true);
  const lines = [];
  try {
    const code = await withEnv(GRIMOIRE, () => captureLog(lines, () =>
      SA.serve({ run: dir, regionWaitMinutes: 1 }, { loadDeps: async () => B, regionPollMs: 20 })));
    assert.equal(code, 1);
    assert.deepEqual(calls, [['lock', 9223, 'seller-assistant'], ['acquire', 'amazon-communications:seller-assistant:sa-region-test'], ['unlock', 9223]]);
    assert.deepEqual(lines.map(line => [JSON.parse(line).status, JSON.parse(line).reason]), [['error', 'TASK_TAB_BUSY']]);
    const status = await readJson(join(dir, 'serve.json'));
    assert.deepEqual([status.status, status.reason], ['stopped', 'TASK_TAB_BUSY']);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

// The entry point itself, in a child process, against the real lease registry
// of the isolated runtime with the US region held by another controller.
// fake-cdp-hooks.mjs replaces cdp.mjs, so nothing reaches a browser.

async function holdRegion() {
  const now = Date.now(), record = holderRecord(now);
  const state = {
    schema_version: 1, revision: 1, leases: {}, auth_attempts: {}, download_claims: {},
    task_tabs: { [HOLDER_KEY]: record },
    context_claims: { 9222: { kind: 'regional-context-guard', version: 1, port: 9222, taskSlotKey: '@regional-guard:9222', controlToken: '@regional-guard:9222',
      owner: 'regional-context-controller', heartbeatAt: record.controller.heartbeatAt, expiresAt: record.controller.expiresAt } },
    regional_context_claims: { '9222:sc:na': { taskSlotKey: HOLDER_KEY, controlToken: HOLDER_TOKEN, owner: HOLDER_OWNER,
      heartbeatAt: record.controller.heartbeatAt, expiresAt: record.controller.expiresAt, scope: 'sc:na', port: 9222 } },
  };
  await writeFile(REGISTRY, JSON.stringify(state, null, 2));
  return state;
}
function startServe(dir, waitMinutes) {
  const env = { ...process.env, ...OPERATOR, CDP_HOST: 'cdp.invalid', CDP_AUTOSTART: '0', CDP_LAUNCHER: join(dir, 'no-launcher') };
  for (const key of ['WIZARDS_AI_MODE', 'AMAZON_BROWSER_LOCK_TOKEN', 'AMAZON_BROWSER_LOCK_CHAIN', 'AMAZON_BROWSER_LAUNCHER_CONTROL', 'AMAZON_BROWSER_LAUNCHER_PID']) delete env[key];
  const child = spawn(process.execPath, ['--import', HOOKS, SCRIPT, 'serve', '--run', dir, '--region-wait-minutes', String(waitMinutes)], { env, stdio: ['ignore', 'pipe', 'pipe'] });
  let stdout = '', stderr = '';
  child.stdout.on('data', chunk => { stdout += chunk; });
  child.stderr.on('data', chunk => { stderr += chunk; });
  const exited = new Promise(resolve => child.on('exit', (code, signal) => resolve({ code, signal })));
  const finished = async limitMs => {
    const result = await Promise.race([exited, delay(limitMs, null, { ref: false })]);
    if (result) return { ...result, stdout, stderr };
    child.kill('SIGKILL');
    await exited;
    return { code: 'hung', signal: null, stdout, stderr };
  };
  return { child, finished };
}
async function assertNothingHeld(before) {
  const after = JSON.parse(await readFile(REGISTRY, 'utf8'));
  assert.deepEqual(Object.keys(after.task_tabs), [HOLDER_KEY], 'no task record or reservation for the controller');
  assert.deepEqual(after.regional_context_claims, before.regional_context_claims, 'the holder keeps its claim; no claim was added');
  assert.deepEqual(after.context_claims, before.context_claims);
  assert.deepEqual(after.leases, {}, 'no tab lease');
}

test('entry point: a region held past the bound exits 1 with region_busy, neither exit 13 nor a hang', { timeout: 60000 }, async () => {
  const dir = await runDir();
  try {
    const before = await holdRegion();
    // 0.05 minutes = 3 s: the process must stay alive through real waits.
    const run = await startServe(dir, 0.05).finished(30000);
    assert.notEqual(run.code, 13, `the event loop emptied during an await: ${run.stderr}`);
    assert.equal(run.code, 1, `exit ${run.code}: ${run.stderr}`);
    const lines = run.stdout.trim().split('\n').map(line => JSON.parse(line));
    assert.deepEqual(lines.map(line => line.status), ['waiting_for_region', 'error']);
    assert.equal(lines[0].holder.owner, HOLDER_OWNER);
    assert.equal(lines[1].reason, 'region_busy');
    const status = await readJson(join(dir, 'serve.json'));
    assert.deepEqual([status.status, status.reason, status.port, status.region_scope], ['error', 'region_busy', 9222, 'sc:na']);
    assert.deepEqual([status.holder.owner, status.holder.workflow, status.holder.task_id], [HOLDER_OWNER, 'seller-central-region', HOLDER_TASK]);
    assert.ok(status.waited_s >= 3);
    assert.ok(!run.stdout.includes(HOLDER_TOKEN) && !JSON.stringify(status).includes(HOLDER_TOKEN));
    assert.equal(existsSync(join(dir, 'serve.pid')), false);
    await assertNothingHeld(before);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('entry point: a send during the wait names it, and SIGTERM ends the wait cleanly', { timeout: 60000 }, async () => {
  const dir = await runDir();
  try {
    const before = await holdRegion();
    const serve = startServe(dir, 1);
    const waiting = await until(async () => { const status = await readJson(join(dir, 'serve.json')); return status?.status === 'waiting_for_region' && status; });
    assert.equal(waiting.pid, serve.child.pid);
    assert.equal(waiting.holder.owner, HOLDER_OWNER);
    const answers = [];
    assert.equal(await SA.sendCommand({ run: dir, command: 'state', args: {} }, { pollMs: 10, out: line => answers.push(JSON.parse(line)) }), 2);
    assert.deepEqual([answers[0].status, answers[0].reason], ['error', 'waiting_for_region']);
    assert.deepEqual(await readdir(join(dir, 'queue')), []);
    serve.child.kill('SIGTERM');
    const run = await serve.finished(20000);
    assert.equal(run.code, 143, `exit ${run.code}: ${run.stderr}`);
    assert.equal(existsSync(join(dir, 'serve.pid')), false, 'serve.pid is removed');
    const status = await readJson(join(dir, 'serve.json'));
    assert.deepEqual([status.status, status.reason], ['stopped', 'SIGTERM']);
    await assertNothingHeld(before);
  } finally { await rm(dir, { recursive: true, force: true }); }
});
