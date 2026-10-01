import '../../report-fetcher/test/helpers/isolated-runtime.mjs';
import { mkdtemp, mkdir, readFile, writeFile, rm, readdir, chmod, appendFile } from 'node:fs/promises';
import { existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';
import {
  selectComposerFrame, matchLabel, validateApproval, checkComposer, checkTextFile, isNavigationAllowed, detectDenial,
  detectTour, termsHash, nextQueueName, parseArgs, validateRunConfig, summarizeViewCase, assembleState, makeBrowser,
  executeCommand, processNext, allocateQueueEntry, loadUsageCounts, sendCommand, sha256, MAX_COMPOSER_CHARS, serveLoop, cancelQueued,
  composerSubmitCheck, attachmentCheck, resolveIdentity, recoverInterrupted, markInFlight, commandInFlight, isIsoTime, pageAgent, collapse,
} from '../seller-assistant.mjs';
// Exports added after the first review are read through the namespace so a
// missing export fails its own test instead of the whole file.
import * as SA from '../seller-assistant.mjs';

const SC = 'https://sellercentral.amazon.com';
const ASSISTANT = `${SC}/assistant?client=sellerSupport-meldFullPage`;
const P1 = 'ASIN B0TEST0001 shows an inbound shipment discrepancy. We checked the shipment events. Please connect me with a Seller Support associate.';
const P1_SHA = sha256(P1);
// Fake controller clock: approvals are dated shortly before it.
const T0 = Date.parse('2026-09-29T12:00:00Z');
const RUN_ID = 'sa-test', SELLER = 'A1TEST';

async function runDir() {
  const dir = await mkdtemp(join(tmpdir(), 'seller-assistant-test-'));
  for (const sub of ['queue', 'results', 'steps', 'transcripts', 'screenshots', 'viewcase']) await mkdir(join(dir, sub));
  return dir;
}
async function approvalFile(dir, overrides = {}, name = 'approval.json') {
  const path = join(dir, name);
  await writeFile(path, JSON.stringify({ schema_version: 1, plan_item: 'P1', sha256: P1_SHA, approved_at: '2026-09-29T10:15:00+02:00', approval_text: 'Approved, send P1 as drafted.', run_id: RUN_ID, seller_id: SELLER, label: 'routine', ...overrides }));
  return path;
}
function baseState(overrides = {}) {
  return {
    url: ASSISTANT, conversation_url: null,
    frames: [{ frame_id: 'main', url: ASSISTANT, origin: SC, same_origin: true, reachable: true, composer_count: 1 }],
    selection: { ok: true, frame_id: 'main' },
    composer: { frame_id: 'main', tag: 'TEXTAREA', label: 'Message Seller Assistant...', value: '', length: 0, sha256: sha256(''), disabled: false, counter_text: '0/2500', submit_controls: [{ disabled: false, in_region: true }] },
    controls: [{ frame_id: 'main', label: 'Submit', disabled: false }, { frame_id: 'main', label: 'Upload file', disabled: false }],
    status_texts: [], busy: false, tour: { visible: false, text: null }, denial: { detected: false, text: null },
    handoff: { approve_count: 0 }, attachments: { chips: [], uploading: false, file_input_count: 1, input_files: [] },
    message_count: 2, ...overrides,
  };
}
function fakeRuntime(dir, { state = baseState(), identity = null, newTargetOnClick = false, dispatchError = null, approveEffect = 'label', onDispatch = null, afterClick = null, prepareError = null } = {}) {
  let clock = T0, clicked = false;
  const sent = [];
  const events = [];
  const attemptsAtDispatch = [];
  const uploads = [];
  const current = structuredClone(state);
  const attempts = () => { const path = join(dir, 'approvals.jsonl'); return existsSync(path) ? readFileSync(path, 'utf8').split('\n').filter(l => l.includes('"phase":"attempt"')).length : 0; };
  const browser = {
    scan: async () => {
      if (clicked && afterClick?.scan) throw afterClick.scan;
      const copy = structuredClone(current);
      if (copy.composer) Object.assign(copy.composer, { sha256: sha256(copy.composer.value), length: copy.composer.value.length });
      return copy;
    },
    targets: async () => { if (clicked && afterClick?.targets) throw afterClick.targets; return newTargetOnClick && clicked ? ['target-1', 'target-2'] : ['target-1']; },
    prepareClick: async (_frame, label, opts = {}) => {
      events.push(`prepare:${label}${opts.tour ? ':tour' : ''}`);
      if (opts.composerSubmit) events.push('composer-scope');
      if (typeof opts.expectedComposerText === 'string') events.push(`composer-text:${sha256(opts.expectedComposerText)}`);
      if (typeof opts.expectedTermsText === 'string') events.push(`terms-text:${termsHash(opts.expectedTermsText)}`);
      if (prepareError) throw prepareError;
      return { x: 10, y: 10 };
    },
    dispatchClick: async () => {
      events.push('dispatch');
      attemptsAtDispatch.push(attempts());
      if (dispatchError) throw dispatchError;
      clicked = true;
      const label = events.filter(e => e.startsWith('prepare:')).at(-1).slice(8);
      if (label === 'Submit') { sent.push(current.composer.value); current.composer.value = ''; current.message_count += 1; }
      if (label === 'Approve') {
        current.message_count += 1;
        if (approveEffect === 'label') current.composer.label = 'Message associate...';
        if (approveEffect === 'remove') current.controls = current.controls.filter(c => c.label !== 'Approve');
      }
      if (onDispatch) await onDispatch(label);
    },
    insertText: async (_frame, text) => { events.push('insert'); current.composer.value = text; },
    occurrences: async (_frame, text) => { if (clicked && afterClick?.occurrences) throw afterClick.occurrences; const k = sent.filter(t => t === text).length; return { full: k, prefix: k, composer_value: current.composer.value, message_count: current.message_count }; },
    terms: async () => ({ text: current.handoff.terms_text, sha256: termsHash(current.handoff.terms_text) }),
    prepareFileInput: async () => ({ objectId: 'file-input' }),
    setFile: async (_input, path) => { events.push('set-file'); uploads.push({ path, bytes: readFileSync(path, 'utf8') }); attemptsAtDispatch.push(attempts()); clicked = true; current.attachments.chips.push(path.split('/').at(-1)); },
    conversation: async () => ({ text: 'Seller Assistant\nHello', message_count: current.message_count, messages: [], busy: false, status: [], message_detection: 'structural' }),
    navigate: async url => events.push(`navigate:${url}`),
    release: async () => {},
  };
  const rt = {
    runDir: dir, origin: SC, lockout: null, fatal: false, baseline: null, counts: new Map(), browser,
    config: { schema_version: 1, run_id: RUN_ID, account: { seller_id: SELLER, marketplace_id: 'ATVPDKIKX0DER' } },
    deps: {
      verifyIdentity: identity || (async () => { events.push('identity'); return { merchant_id: 'A1TEST', marketplace_id: 'ATVPDKIKX0DER', source: 'live' }; }),
      screenshot: async () => ({}), evaluateMain: async () => ({ status: 200, body: '{}' }), readFile,
      now: () => clock, sleep: async ms => { clock += ms; },
      clientCgroup: () => ATTENDED_CGROUP,
    },
  };
  return { rt, events, current, sent, attemptsAtDispatch, uploads };
}
// The send client's cgroup: an attended terminal, so serve runs its commands.
const ATTENDED_CGROUP = '0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-com.t3tools.T3Code-1.scope\n';
const command = (id, name, args = {}) => ({ schema_version: 1, id, command: name, args, expires_at: '2099-01-01T00:00:00Z', client_pid: 4242 });

test('frame selection: one composer frame, none, several, cross-origin chat frame', () => {
  const main = { frame_id: 'm', url: ASSISTANT, origin: SC, same_origin: true, reachable: true };
  assert.deepEqual(selectComposerFrame([{ ...main, composer_count: 1 }]), { ok: true, frame_id: 'm' });
  assert.equal(selectComposerFrame([{ ...main, composer_count: 0 }]).reason, 'no_composer');
  assert.equal(selectComposerFrame([{ ...main, composer_count: 2 }]).reason, 'multiple_composers');
  const child = { frame_id: 'c', url: `${SC}/assistant/embed`, origin: SC, same_origin: true, reachable: true, composer_count: 1 };
  assert.equal(selectComposerFrame([{ ...main, composer_count: 1 }, child]).reason, 'multiple_composer_frames');
  assert.deepEqual(selectComposerFrame([{ ...main, composer_count: 0 }, child]), { ok: true, frame_id: 'c' });
  const foreign = { frame_id: 'x', url: 'https://chat.example.net/cyrano/widget', origin: 'https://chat.example.net', same_origin: false, reachable: false, composer_count: 0 };
  assert.equal(selectComposerFrame([{ ...main, composer_count: 0 }, foreign]).reason, 'cross_origin_chat_frame');
  assert.equal(selectComposerFrame([{ ...main, composer_count: 1 }, foreign]).reason, 'cross_origin_chat_frame');
  const ad = { ...foreign, url: 'https://ads.example.net/pixel' };
  assert.deepEqual(selectComposerFrame([{ ...main, composer_count: 1 }, ad]), { ok: true, frame_id: 'm' });
});

test('exact label matching: unique, ambiguous, disabled, whitespace, no substrings', () => {
  const controls = [{ label: 'Submit', disabled: false }, { label: 'Upload  file', disabled: true }, { label: 'Show more', disabled: false }, { label: 'Show more', disabled: false }];
  assert.equal(matchLabel(controls, 'Submit').ok, true);
  assert.equal(matchLabel(controls, 'Submit').index, 0);
  assert.deepEqual(matchLabel(controls, 'Show more'), { ok: false, reason: 'ambiguous', count: 2 });
  assert.deepEqual(matchLabel(controls, 'Upload file'), { ok: false, reason: 'disabled', count: 1 });
  assert.equal(matchLabel(controls, 'Sub').reason, 'not_found');
  assert.equal(matchLabel([{ label: 'Submit case', disabled: false }], 'Submit').reason, 'not_found');
});

test('composer hash mismatch, empty and over-long text are refused', () => {
  assert.equal(checkComposer(P1, P1_SHA).ok, true);
  assert.equal(checkComposer(`${P1}\r\n`, P1_SHA).ok, true);
  assert.equal(checkComposer(`${P1} `, P1_SHA).reason, 'composer_sha_mismatch');
  assert.equal(checkComposer('', P1_SHA).reason, 'composer_empty');
  const long = 'x'.repeat(MAX_COMPOSER_CHARS + 1);
  assert.equal(checkComposer(long, sha256(long)).reason, 'composer_too_long');
  const exact = 'y'.repeat(MAX_COMPOSER_CHARS);
  assert.equal(checkComposer(exact, sha256(exact)).ok, true);
});

test('text files must match their hash, be normalized and stay within 2500 characters', () => {
  const buffer = Buffer.from(P1);
  assert.equal(checkTextFile(buffer, P1_SHA).ok, true);
  assert.equal(checkTextFile(buffer, 'f'.repeat(64)).reason, 'text_sha_mismatch');
  const trailing = Buffer.from(`${P1}\n`);
  assert.equal(checkTextFile(trailing, sha256(trailing)).reason, 'text_file_not_normalized');
  const crlf = Buffer.from('line one\r\nline two');
  assert.equal(checkTextFile(crlf, sha256(crlf)).reason, 'text_file_not_normalized');
  const long = Buffer.from('z'.repeat(MAX_COMPOSER_CHARS + 1));
  assert.equal(checkTextFile(long, sha256(long)).reason, 'text_too_long');
});

test('type refuses over-long text and a non-empty composer without inserting', async () => {
  const dir = await runDir();
  try {
    const longPath = join(dir, 'long.txt'), text = 'a'.repeat(MAX_COMPOSER_CHARS + 1);
    await writeFile(longPath, text);
    const { rt, events } = fakeRuntime(dir);
    const tooLong = await executeCommand(rt, command('001', 'type', { 'text-file': longPath, sha256: sha256(text) }));
    assert.equal(tooLong.status, 'refused'); assert.equal(tooLong.reason, 'text_too_long');
    const p1Path = join(dir, 'p1.txt'); await writeFile(p1Path, P1);
    const busy = fakeRuntime(dir, { state: baseState({ composer: { ...baseState().composer, value: 'draft by someone' } }) });
    const notEmpty = await executeCommand(busy.rt, command('002', 'type', { 'text-file': p1Path, sha256: P1_SHA }));
    assert.equal(notEmpty.reason, 'composer_not_empty');
    assert.ok(!events.includes('insert') && !busy.events.includes('insert'));
    const ok = fakeRuntime(dir);
    const typed = await executeCommand(ok.rt, command('003', 'type', { 'text-file': p1Path, sha256: P1_SHA }));
    assert.equal(typed.status, 'ok'); assert.equal(typed.composer.sha256, P1_SHA);
    assert.ok(!ok.events.includes('dispatch'), 'type never clicks');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('navigation allowlist refuses unlisted labels and tour labels without a visible tour', async () => {
  assert.deepEqual(isNavigationAllowed('Get help with a new issue', {}), { ok: true, kind: 'navigation' });
  assert.equal(isNavigationAllowed('Submit', {}).reason, 'label_not_allowed');
  assert.equal(isNavigationAllowed('Open the tool', {}).reason, 'label_not_allowed');
  assert.equal(isNavigationAllowed('Skip', { tour: { visible: false } }).reason, 'tour_not_visible');
  assert.equal(isNavigationAllowed('Skip', { tour: { visible: true } }).kind, 'tour');
  assert.equal(isNavigationAllowed('Request changes', {}).reason, 'summary_not_visible');
  assert.equal(isNavigationAllowed('Request changes', { handoff: { approve_count: 0 } }).reason, 'summary_not_visible');
  assert.deepEqual(isNavigationAllowed('Request changes', { handoff: { approve_count: 2 } }), { ok: true, kind: 'summary' });
  assert.deepEqual(isNavigationAllowed('Request changes', { handoff: { approve_count: 1 } }), { ok: true, kind: 'summary' });
  assert.equal(isNavigationAllowed('Approve', { handoff: { approve_count: 1 } }).reason, 'label_not_allowed');
  const dir = await runDir();
  try {
    const { rt, events } = fakeRuntime(dir, { state: baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Open the tool', disabled: false }, { frame_id: 'main', label: 'Got it', disabled: false }] }) });
    const unlisted = await executeCommand(rt, command('001', 'navigate', { label: 'Open the tool' }));
    assert.equal(unlisted.status, 'refused'); assert.equal(unlisted.reason, 'label_not_allowed');
    const tour = await executeCommand(rt, command('002', 'navigate', { label: 'Got it' }));
    assert.equal(tour.reason, 'tour_not_visible');
    assert.ok(!events.some(e => e.startsWith('prepare:')) && !events.includes('dispatch'));
    const withTour = fakeRuntime(dir, { state: baseState({ tour: { visible: true, text: 'Step 1/3', frame_id: 'main' }, controls: [{ frame_id: 'main', label: 'Got it', disabled: false, in_tour: true }] }) });
    assert.equal((await executeCommand(withTour.rt, command('003', 'navigate', { label: 'Got it' }))).status, 'ok');
    assert.ok(withTour.events.includes('prepare:Got it:tour') && withTour.events.includes('dispatch'));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('approval files: missing, malformed, wrong hash, wrong item or bad timestamp are refused', async () => {
  const good = { schema_version: 1, plan_item: 'P1', sha256: P1_SHA, approved_at: '2026-09-29T08:15:00Z', approval_text: 'Go.', run_id: RUN_ID, seller_id: SELLER, label: 'routine' };
  const ctx = { runId: RUN_ID, sellerId: SELLER, now: T0 };
  assert.equal(validateApproval(good, P1_SHA, undefined, ctx).ok, true);
  assert.equal(validateApproval({ ...good, sha256: 'a'.repeat(64) }, P1_SHA, undefined, ctx).reason, 'approval_sha_mismatch');
  assert.equal(validateApproval({ ...good, approved_at: '2026-09-29T08:15:00' }, P1_SHA, undefined, ctx).reason, 'approval_time_invalid');
  assert.equal(validateApproval({ ...good, approval_text: ' ' }, P1_SHA, undefined, ctx).reason, 'approval_text_missing');
  assert.equal(validateApproval({ ...good, plan_item: 'P9' }, P1_SHA, undefined, ctx).reason, 'approval_plan_item_invalid');
  assert.equal(validateApproval({ ...good, plan_item: 'approve' }, P1_SHA, ['P1', 'P2', 'P3', 'followup'], ctx).reason, 'approval_plan_item_not_for_command');
  const dir = await runDir();
  try {
    const { rt, events, current } = fakeRuntime(dir);
    current.composer.value = P1;
    const missing = await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': join(dir, 'absent.json') }));
    assert.equal(missing.reason, 'approval_missing');
    const broken = join(dir, 'broken.json'); await writeFile(broken, '{not json');
    assert.equal((await executeCommand(rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': broken }))).reason, 'approval_malformed');
    const other = await approvalFile(dir, { sha256: 'b'.repeat(64) }, 'other.json');
    assert.equal((await executeCommand(rt, command('003', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': other }))).reason, 'approval_sha_mismatch');
    assert.ok(!events.includes('dispatch'));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('submit never clicks when the composer differs from the approved text', async () => {
  const dir = await runDir();
  try {
    const { rt, events, current } = fakeRuntime(dir);
    current.composer.value = `${P1} Also please refund us.`;
    const approval = await approvalFile(dir);
    const result = await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(result.status, 'refused'); assert.equal(result.reason, 'composer_sha_mismatch');
    assert.ok(!events.includes('dispatch'));
    current.composer.value = P1;
    const chips = await executeCommand(rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval, 'expect-attachment': ['invoice.pdf'] }));
    assert.equal(chips.reason, 'expected_attachment_not_approved');
    assert.ok(!events.includes('dispatch'));
    await assert.rejects(readFile(join(dir, 'approvals.jsonl'), 'utf8'));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('submit verifies identity before the click, logs the approval and is never repeated', async () => {
  const dir = await runDir();
  try {
    const { rt, events, current } = fakeRuntime(dir);
    current.composer.value = P1;
    const approval = await approvalFile(dir);
    const result = await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(result.status, 'sent');
    const lastIdentity = events.lastIndexOf('identity'), click = events.indexOf('dispatch');
    assert.ok(events.slice(0, click).filter(e => e === 'identity').length >= 2, 'identity before command and again before the click');
    assert.ok(lastIdentity > click, 'identity after command');
    const log = (await readFile(join(dir, 'approvals.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse);
    assert.deepEqual(log.map(x => x.phase), ['attempt', 'result']);
    assert.equal(log[0].approval.approval_text, 'Approved, send P1 as drafted.');
    current.composer.value = P1;
    const again = await executeCommand(rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(again.reason, 'send_limit_reached');
    assert.equal((await loadUsageCounts(dir)).get(`submit:${P1_SHA}`), 1);
    const step = JSON.parse(await readFile(join(dir, 'steps', '01-submit.json'), 'utf8'));
    assert.equal(step.result.status, 'sent'); assert.ok(step.composer && step.controls);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('P2 may be sent twice and no more', async () => {
  const dir = await runDir();
  try {
    const p2 = 'Please connect me with a Seller Support associate.', sha = sha256(p2);
    const approval = await approvalFile(dir, { plan_item: 'P2', sha256: sha });
    const { rt, current } = fakeRuntime(dir);
    const statuses = [];
    for (const id of ['001', '002', '003']) { current.composer.value = p2; statuses.push((await executeCommand(rt, command(id, 'submit', { 'expect-sha256': sha, 'approval-file': approval }))).status); }
    assert.deepEqual(statuses, ['sent', 'sent', 'refused']);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('identity mismatch blocks and locks out outbound commands until restart', async () => {
  const dir = await runDir();
  try {
    let good = true;
    const { rt, events, current } = fakeRuntime(dir, { identity: async () => { if (!good) throw Object.assign(new Error('seller changed'), { code: 'identity_mismatch' }); return { merchant_id: 'A1TEST', marketplace_id: 'ATVPDKIKX0DER', source: 'live' }; } });
    good = false;
    const state = await executeCommand(rt, command('001', 'state'));
    assert.equal(state.status, 'blocked'); assert.equal(state.reason, 'identity_mismatch');
    good = true;
    current.composer.value = P1;
    const approval = await approvalFile(dir);
    for (const [id, name, args] of [['002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }], ['003', 'navigate', { label: 'Show more' }], ['004', 'open', {}]]) {
      const result = await executeCommand(rt, command(id, name, args));
      assert.equal(result.status, 'blocked'); assert.equal(result.reason, 'locked_out:identity_mismatch');
    }
    assert.ok(!events.includes('dispatch') && !events.some(e => e.startsWith('navigate:')));
    assert.equal((await executeCommand(rt, command('005', 'state'))).status, 'ok', 'read-only commands still run and re-check identity');
    const stop = await executeCommand(rt, command('006', 'stop'));
    assert.equal(stop.stopping, true);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('an identity change right before the Submit click prevents the click', async () => {
  const dir = await runDir();
  try {
    let calls = 0;
    const { rt, events, current } = fakeRuntime(dir, { identity: async () => { calls++; if (calls === 2) throw new Error('header shows another seller'); return { merchant_id: 'A1TEST', marketplace_id: 'M', source: 'live' }; } });
    current.composer.value = P1;
    const result = await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(result.status, 'blocked'); assert.equal(result.reason, 'identity_mismatch');
    assert.ok(!events.includes('dispatch'));
    assert.equal(rt.lockout.reason, 'identity_mismatch');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('denial and tour text are detected', () => {
  const denial = detectDenial('Working on it\nYou don’t currently have permission to create support cases on this account.\nChoose New chat');
  assert.equal(denial.detected, true);
  assert.match(denial.text, /permission to create support cases/);
  assert.equal(detectDenial("You don't currently have permission to create support cases on this account.").detected, true);
  assert.equal(detectDenial('You do not currently have permission to view this page.').detected, true);
  // Wording observed live on 2026-09-30 (Blissta US).
  const variant = detectDenial('Here\'s what I found\nIt looks like you don’t currently have permission to create a support case on this account. The primary account holder may be able to grant you this permission via User Permissions in Seller Central.');
  assert.equal(variant.detected, true);
  assert.match(variant.text, /create a support case on this account/);
  assert.equal(detectDenial("Here's what I found").detected, false);
  assert.equal(detectTour('Welcome Step 2/4 Next').visible, true);
  assert.equal(detectTour('Steps to take').visible, false);
});

test('approve refuses when the live terms differ from the approved terms', async () => {
  const dir = await runDir();
  try {
    const approved = 'Connect with an associate\nA Seller Support associate will join this chat.\nApprove';
    const state = baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Approve', disabled: false }], handoff: { approve_count: 1, terms_text: `${approved}\nWe may call you back at +1 555 0100.` } });
    const { rt, events } = fakeRuntime(dir, { state });
    const approval = await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(approved) }, 'approve.json');
    const result = await executeCommand(rt, command('001', 'approve', { 'expect-terms-sha256': termsHash(approved), 'approval-file': approval }));
    assert.equal(result.status, 'refused'); assert.equal(result.reason, 'terms_sha_mismatch');
    assert.ok(!events.includes('dispatch'));
    assert.equal(termsHash('A  b\r\n\r\nc '), termsHash('A b\nc'));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('attach refuses a file whose bytes differ from the approved hash', async () => {
  const dir = await runDir();
  try {
    const file = join(dir, 'invoice.pdf'); await writeFile(file, 'pdf bytes');
    const approvedSha = sha256('other bytes');
    const approval = await approvalFile(dir, { plan_item: 'attachment', sha256: approvedSha }, 'attach.json');
    const { rt, events } = fakeRuntime(dir);
    const result = await executeCommand(rt, command('001', 'attach', { file, sha256: approvedSha, 'approval-file': approval }));
    assert.equal(result.status, 'refused'); assert.equal(result.reason, 'file_sha_mismatch');
    assert.ok(!events.includes('set-file'));
    const wrongItem = await approvalFile(dir, { plan_item: 'P3', sha256: sha256('pdf bytes') }, 'wrong.json');
    assert.equal((await executeCommand(rt, command('002', 'attach', { file, sha256: sha256('pdf bytes'), 'approval-file': wrongItem }))).reason, 'approval_plan_item_not_for_command');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('queue names allocate in order and never collide', async () => {
  assert.equal(nextQueueName([]), '001');
  assert.equal(nextQueueName(['001.json', '002.claim', 'notes.txt', '010.json.tmp-1']), '003');
  assert.equal(nextQueueName(['999.json']), '1000');
  const dir = await runDir();
  try {
    const names = await Promise.all(Array.from({ length: 12 }, () => allocateQueueEntry(dir)));
    assert.equal(new Set(names).size, 12);
    assert.deepEqual([...names].sort(), Array.from({ length: 12 }, (_, i) => String(i + 1).padStart(3, '0')));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('the controller processes queued commands in order, refuses expired ones and stops on stop', async () => {
  const dir = await runDir();
  try {
    const { rt } = fakeRuntime(dir);
    await writeFile(join(dir, 'queue', '002.json'), JSON.stringify({ ...command('002', 'state'), expires_at: '2000-01-01T00:00:00Z' }));
    await writeFile(join(dir, 'queue', '001.json'), JSON.stringify(command('001', 'state')));
    await writeFile(join(dir, 'queue', '005.json'), JSON.stringify({ schema_version: 1, id: '005', command: 'state', args: {} }));
    await writeFile(join(dir, 'queue', '003.json'), JSON.stringify({ schema_version: 1, id: '003', command: 'click', args: { label: 'Submit' } }));
    await writeFile(join(dir, 'queue', '004.json'), JSON.stringify(command('004', 'stop')));
    assert.equal((await processNext(rt)).id, '001');
    rt.deps.now = () => Date.parse('2026-09-29T00:00:00Z');
    assert.equal((await processNext(rt)).status, 'expired');
    assert.equal((await processNext(rt)).reason, 'command_malformed');
    await processNext(rt);
    assert.equal(rt.stopRequested.id, '004');
    assert.deepEqual((await readdir(join(dir, 'results'))).sort(), ['001.json', '002.json', '003.json', '004.running'], 'stop result is written by serve after release');
    const again = await processNext(rt);
    assert.equal(again.id, '004'); assert.equal(again.reason, 'interrupted', 'a started command is never run twice');
    await writeFile(join(dir, 'results', '004.json'), '{}');
    const noExpiry = await processNext(rt);
    assert.equal(noExpiry.id, '005'); assert.equal(noExpiry.reason, 'command_malformed', 'a command without expires_at never runs');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('argument parsing and run configuration are strict', () => {
  const parsed = parseArgs(['send', '--run', 'runs/x', 'submit', '--expect-sha256', P1_SHA, '--approval-file', 'a.json', '--expect-attachment', 'one.pdf', '--expect-attachment', 'two.png']);
  assert.equal(parsed.command, 'submit'); assert.ok(parsed.args['approval-file'].startsWith('/'));
  assert.deepEqual(parsed.args['expect-attachment'], ['one.pdf', 'two.png']);
  assert.deepEqual(parseArgs(['serve', '--run', 'r']), { mode: 'serve', run: 'r', maxMinutes: 90, idleMinutes: 20 });
  assert.equal(parseArgs(['serve', '--run', 'r', '--max-minutes', '30', '--idle-minutes', '5']).maxMinutes, 30);
  assert.throws(() => parseArgs(['send', '--run', 'r', 'click', '--label', 'Submit']), /Unknown command/);
  assert.throws(() => parseArgs(['send', '--run', 'r', 'navigate', '--label', 'x', '--force']), /Unknown flag/);
  assert.throws(() => parseArgs(['send', '--run', 'r', 'submit', '--expect-sha256', 'abc', '--approval-file', 'a']), /invalid_flag/);
  assert.equal(parseArgs(['send', '--run', 'r', 'open', '--via-lobby']).args['via-lobby'], true);
  assert.equal(parseArgs(['send', '--run', 'r', 'transcript', '--wait-new', '1', '--timeout', '240']).args.timeout, 240);
  const account = { profile_key: 'acme-us', client_slug: 'acme', marketplace: 'US', seller_id: 'A1TEST', marketplace_id: 'ATVPDKIKX0DER', seller_central_name: 'Acme', marketplace_label: 'United States', parent_account_name: 'Acme Group' };
  assert.equal(validateRunConfig({ schema_version: 1, run_id: 'sa-2026-09-29-acme', account }).run_id, 'sa-2026-09-29-acme');
  assert.throws(() => validateRunConfig({ schema_version: 1, run_id: 'bad id', account }), /run_id/);
  assert.throws(() => validateRunConfig({ schema_version: 1, run_id: 'ok', account: { ...account, seller_id: '' } }), /seller_id/);
});

test('ViewCase summary leaves out emails, senders and message text', () => {
  const summary = summarizeViewCase({ totalNumberOfContacts: 2, viewCaseMetaData: { caseTitle: 'Inbound discrepancy', caseStatus: 'Open', canEditCase: true, primaryEmail: 'ops@example.invalid' },
    contactList: [{ outbound: false, channelType: 'CHAT', sender: 'ops@example.invalid', message: 'Hello from ops@example.invalid', attachments: [{ fileName: 'invoice.pdf' }] }, { outbound: true, channelType: 'CHAT', sender: 'Amazon', message: 'Hi' }] });
  assert.equal(summary.contact_count, 2);
  assert.deepEqual(summary.contacts[0], { outbound: false, channel_type: 'CHAT', message_length: 30, attachment_names: ['invoice.pdf'] });
  assert.doesNotMatch(JSON.stringify(summary), /@/);
});

test('state assembly: composer hash, denial, tour, unreachable cross-origin frames', () => {
  const frames = [{ frame_id: 'm', url: `${SC}/assistant/amzn1.cyrano.conversation.cid.v2.123?client=sellerSupport-meldFullPage`, origin: SC, same_origin: true },
    { frame_id: 'x', url: 'https://metrics.example.net/pixel', origin: 'https://metrics.example.net', same_origin: false }];
  const state = assembleState(frames, { m: { title: 'Seller Assistant', text: "Step 1/3\nYou don't currently have permission to create support cases on this account.",
    tour: { visible: true, text: 'Step 1/3', reason: null, container: { tag: 'DIV', role: 'dialog', testid: null } },
    composers: [{ tag: 'TEXTAREA', label: 'Message Seller Assistant...', value: 'hi', disabled: false }],
    controls: [{ label: 'Submit', disabled: false }, { label: 'Upload file', disabled: true }], counters: ['2/2500'], status: ['Working on it'], busy: true,
    region: { chips: [], counters: ['2/2500'], uploading: false }, file_inputs: { count: 1, names: [] }, conversation: { message_count: 3, message_detection: 'structural' } } });
  assert.equal(state.selection.frame_id, 'm');
  assert.equal(state.composer.sha256, sha256('hi')); assert.equal(state.composer.counter_text, '2/2500');
  assert.equal(state.denial.detected, true); assert.equal(state.tour.visible, true); assert.equal(state.tour.frame_id, 'm');
  const chatText = assembleState(frames.slice(0, 1), { m: { text: 'Agent: see Step 2/4 in the guide', tour: { visible: false, text: 'Step 2/4', reason: 'no_tour_container' }, composers: [], controls: [] } });
  assert.equal(chatText.tour.visible, false, 'Step text without a tour container is not a tour'); assert.equal(chatText.tour.reason, 'no_tour_container');
  assert.equal(state.attachments.upload_enabled, false); assert.equal(state.attachments.submit_enabled, true);
  assert.match(state.conversation_url, /amzn1\.cyrano\.conversation/);
  assert.equal(state.frames[1].reachable, false);
});

test('the frame driver evaluates same-origin frames only, each in its own isolated world', async () => {
  const calls = [];
  const send = async (method, params) => {
    calls.push([method, params]);
    if (method === 'Page.getFrameTree') return { frameTree: { frame: { id: 'm', url: ASSISTANT, securityOrigin: SC }, childFrames: [{ frame: { id: 'x', url: 'https://widget.example.net/', securityOrigin: 'https://widget.example.net' } }] } };
    if (method === 'Page.createIsolatedWorld') return { executionContextId: params.frameId === 'm' ? 11 : 99 };
    if (method === 'Runtime.evaluate') return { result: { value: { title: 't', text: '', composers: [{ tag: 'TEXTAREA', label: 'Message Seller Assistant...', value: '', disabled: false }], controls: [], counters: [], status: [], busy: false, region: { chips: [], counters: [], uploading: false }, file_inputs: { count: 0, names: [] }, conversation: { message_count: 0 } } } };
    throw new Error(`unexpected ${method}`);
  };
  const state = await makeBrowser({ send }, SC).scan();
  assert.deepEqual(calls.filter(([m]) => m === 'Page.createIsolatedWorld').map(([, p]) => p.frameId), ['m']);
  assert.deepEqual(calls.filter(([m]) => m === 'Runtime.evaluate').map(([, p]) => p.contextId), [11]);
  assert.match(calls.find(([m]) => m === 'Runtime.evaluate')[1].expression, /^\/\*ew-sa:scan\*\//);
  assert.equal(state.selection.ok, true);
});

test('a covered control is never clicked', async () => {
  const methods = [];
  const send = async (method) => {
    methods.push(method);
    if (method === 'Page.createIsolatedWorld') return { executionContextId: 5 };
    if (method === 'Runtime.evaluate') return { result: { objectId: 'button-1' } };
    if (method === 'DOM.getContentQuads') return { quads: [[0, 0, 20, 0, 20, 10, 0, 10]] };
    if (method === 'DOM.getNodeForLocation') return { backendNodeId: 7 };
    if (method === 'DOM.resolveNode') return { object: { objectId: 'overlay-1' } };
    if (method === 'Runtime.callFunctionOn') return { result: { value: false } };
    return {};
  };
  await assert.rejects(makeBrowser({ send }, SC).prepareClick('m', 'Submit'), /another element covers/);
  assert.ok(!methods.includes('Input.dispatchMouseEvent'));
});

test('send queues one command and returns the controller result', async () => {
  const dir = await runDir();
  try {
    const account = { profile_key: 'acme-us', client_slug: 'acme', marketplace: 'US', seller_id: 'A1TEST', marketplace_id: 'ATVPDKIKX0DER', seller_central_name: 'Acme', marketplace_label: 'United States', parent_account_name: 'Acme Group' };
    await writeFile(join(dir, 'run.json'), JSON.stringify({ schema_version: 1, run_id: 'sa-test', account }));
    await writeFile(join(dir, 'serve.pid'), JSON.stringify({ pid: process.pid }));
    const { rt } = fakeRuntime(dir);
    rt.deps.now = Date.now;
    const printed = [];
    const client = sendCommand({ run: dir, command: 'state', args: {} }, { pollMs: 20, out: line => printed.push(line) });
    let result = null;
    for (let i = 0; i < 100 && !result; i++) { result = await processNext(rt); if (!result) await new Promise(r => setTimeout(r, 10)); }
    assert.equal(await client, 0);
    assert.equal(JSON.parse(printed[0]).status, 'ok');
    assert.deepEqual((await readdir(join(dir, 'queue'))).sort(), ['001.claim', '001.json']);
    await rm(join(dir, 'serve.pid'));
    assert.equal(await sendCommand({ run: dir, command: 'state', args: {} }, { out: line => printed.push(line) }), 2);
    assert.equal(JSON.parse(printed.at(-1)).reason, 'serve_not_running');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('tour labels click only inside the tour container', async () => {
  const dir = await runDir();
  try {
    const outside = fakeRuntime(dir, { state: baseState({ tour: { visible: true, text: 'Step 1/3', frame_id: 'main' }, controls: [...baseState().controls, { frame_id: 'main', label: 'Close', disabled: false, in_tour: false }] }) });
    const refused = await executeCommand(outside.rt, command('001', 'navigate', { label: 'Close' }));
    assert.equal(refused.status, 'blocked'); assert.equal(refused.reason, 'control_not_found_in_tour');
    assert.ok(!outside.events.includes('dispatch'), 'a chat Close outside the tour is never clicked');
    const both = fakeRuntime(dir, { state: baseState({ tour: { visible: true, text: 'Step 1/3', frame_id: 'main' },
      controls: [{ frame_id: 'main', label: 'Close', disabled: false, in_tour: false }, { frame_id: 'main', label: 'Close', disabled: false, in_tour: true }] }) });
    assert.equal((await executeCommand(both.rt, command('002', 'navigate', { label: 'Close' }))).status, 'ok');
    assert.ok(both.events.includes('prepare:Close:tour'), 'the page re-checks the tour container');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('type refuses multi-line text for a rich-text composer and allows it in a textarea', async () => {
  const dir = await runDir();
  try {
    const text = 'Hello,\nplease see the shipment below.\nBest regards,\nOps', path = join(dir, 'p3.txt');
    await writeFile(path, text);
    const rich = fakeRuntime(dir, { state: baseState({ composer: { ...baseState().composer, tag: 'DIV' } }) });
    const refused = await executeCommand(rich.rt, command('001', 'type', { 'text-file': path, sha256: sha256(text) }));
    assert.equal(refused.reason, 'multiline_needs_textarea'); assert.ok(!rich.events.includes('insert'));
    const plain = fakeRuntime(dir);
    assert.equal((await executeCommand(plain.rt, command('002', 'type', { 'text-file': path, sha256: sha256(text) }))).status, 'ok');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('approve logs the attempt before the click and reports approved', async () => {
  const dir = await runDir();
  try {
    const terms = 'Connect with an associate\nA Seller Support associate will join this chat.\nApprove';
    const state = baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Approve', disabled: false }], handoff: { approve_count: 1, terms_text: terms } });
    const { rt, attemptsAtDispatch } = fakeRuntime(dir, { state });
    const approval = await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(terms) }, 'approve.json');
    const result = await executeCommand(rt, command('001', 'approve', { 'expect-terms-sha256': termsHash(terms), 'approval-file': approval }));
    assert.equal(result.status, 'approved');
    assert.deepEqual(attemptsAtDispatch, [1], 'attempt written before the click');
    const again = await executeCommand(rt, command('002', 'approve', { 'expect-terms-sha256': termsHash(terms), 'approval-file': approval }));
    assert.equal(again.reason, 'send_limit_reached');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('attach logs the attempt before setting the file and waits for the chip', async () => {
  const dir = await runDir();
  try {
    const file = join(dir, 'invoice.pdf'); await writeFile(file, 'pdf bytes');
    const approval = await approvalFile(dir, { plan_item: 'attachment', sha256: sha256('pdf bytes') }, 'attach.json');
    const { rt, events, attemptsAtDispatch } = fakeRuntime(dir);
    const result = await executeCommand(rt, command('001', 'attach', { file, sha256: sha256('pdf bytes'), 'approval-file': approval }));
    assert.equal(result.status, 'attached'); assert.deepEqual(result.chips, ['invoice.pdf']);
    assert.ok(events.includes('set-file')); assert.deepEqual(attemptsAtDispatch, [1]);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a failed Submit dispatch is uncertain and never retried', async () => {
  const dir = await runDir();
  try {
    const { rt, current } = fakeRuntime(dir, { dispatchError: new Error('socket closed') });
    current.composer.value = P1;
    const approval = await approvalFile(dir);
    const first = await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(first.status, 'uncertain'); assert.equal(first.clicked, true);
    const retry = await executeCommand(rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(retry.reason, 'send_limit_reached');
    const log = (await readFile(join(dir, 'approvals.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse);
    assert.deepEqual(log.map(x => [x.phase, x.status ?? null]), [['attempt', null], ['result', 'uncertain']]);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a restarted controller rebuilds send counts from approvals.jsonl', async () => {
  const dir = await runDir();
  try {
    await writeFile(join(dir, 'approvals.jsonl'), JSON.stringify({ phase: 'attempt', command: 'submit', sha256: P1_SHA }) + '\n{"phase":"att');
    const { rt, events, current } = fakeRuntime(dir);
    rt.counts = await loadUsageCounts(dir);
    current.composer.value = P1;
    const result = await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(result.reason, 'send_limit_reached'); assert.ok(!events.includes('dispatch'));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a click that opens a new page target halts the controller', async () => {
  const dir = await runDir();
  try {
    const { rt } = fakeRuntime(dir, { newTargetOnClick: true, state: baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Show more', disabled: false }] }) });
    await writeFile(join(dir, 'queue', '001.json'), JSON.stringify(command('001', 'navigate', { label: 'Show more' })));
    await writeFile(join(dir, 'queue', '002.json'), JSON.stringify(command('002', 'state')));
    const loop = await serveLoop(rt, { started: T0, maxMs: 60000, idleMs: 60000 });
    assert.deepEqual(loop, { exitReason: 'halted_new_target', outcome: 'error' });
    const first = JSON.parse(await readFile(join(dir, 'results', '001.json'), 'utf8'));
    assert.equal(first.reason, 'new_target');
    assert.ok(!existsSync(join(dir, 'results', '002.json')), 'nothing runs after the halt');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('an identity mismatch halts the controller; stop releases as success', async () => {
  const dir = await runDir();
  try {
    const bad = fakeRuntime(dir, { identity: async () => { throw new Error('seller changed'); } });
    await writeFile(join(dir, 'queue', '001.json'), JSON.stringify(command('001', 'state')));
    assert.deepEqual(await serveLoop(bad.rt, { started: T0, maxMs: 60000, idleMs: 60000 }), { exitReason: 'halted_identity_mismatch', outcome: 'error' });
    const dir2 = await runDir();
    try {
      const good = fakeRuntime(dir2);
      await writeFile(join(dir2, 'queue', '001.json'), JSON.stringify(command('001', 'stop')));
      assert.deepEqual(await serveLoop(good.rt, { started: T0, maxMs: 60000, idleMs: 60000 }), { exitReason: 'stop', outcome: 'success' });
      const idle = fakeRuntime(dir2);
      idle.rt.stopRequested = null;
      await writeFile(join(dir2, 'results', '001.json'), '{}');
      assert.equal((await serveLoop(idle.rt, { started: T0, maxMs: 10 * 60000, idleMs: 5000 })).exitReason, 'idle_minutes');
    } finally { await rm(dir2, { recursive: true, force: true }); }
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a sent message stays visible as sent when the identity check after it fails', async () => {
  const dir = await runDir();
  try {
    let calls = 0;
    const { rt, current } = fakeRuntime(dir, { identity: async () => { calls++; if (calls === 3) throw new Error('header not painted'); return { merchant_id: 'A1TEST', marketplace_id: 'M', source: 'live' }; } });
    current.composer.value = P1;
    const result = await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(result.status, 'sent_identity_unverified'); assert.equal(result.action_status, 'sent'); assert.equal(result.delivery, 'sent');
    assert.equal(rt.lockout.reason, 'identity_mismatch');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('submit waits out a busy assistant and re-checks chips after the identity read', async () => {
  const dir = await runDir();
  try {
    const busy = fakeRuntime(dir, { state: baseState({ busy: true }) });
    busy.current.composer.value = P1;
    const blocked = await executeCommand(busy.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(blocked.reason, 'assistant_busy'); assert.ok(!busy.events.includes('dispatch'));
    let calls = 0;
    const chip = fakeRuntime(dir, { identity: async () => { calls++; if (calls === 2) chip.current.attachments.chips.push('late.pdf'); return { merchant_id: 'A1TEST', marketplace_id: 'M', source: 'live' }; } });
    chip.current.composer.value = P1;
    const late = await executeCommand(chip.rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(late.reason, 'attachment_not_approved'); assert.equal(late.stage, 'pre_click'); assert.ok(!chip.events.includes('dispatch'));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('transcript saves the whole frame text and finds a denial there', async () => {
  const dir = await runDir();
  try {
    const { rt } = fakeRuntime(dir);
    rt.browser.conversation = async () => ({ text: 'I need to open a new case', message_count: 1, messages: [], busy: false, status: [], message_detection: 'text_blocks',
      page_text: 'I need to open a new case\nSeller Assistant\nIt looks like you don\u2019t currently have permission to create a support case on this account.' });
    const result = await executeCommand(rt, command('001', 'transcript', {}));
    assert.equal(result.status, 'ok');
    assert.equal(result.denial.detected, true);
    assert.match(await readFile(result.page_text_path, 'utf8'), /Seller Assistant/);
    rt.browser.deepText = async frameId => ({ text: `Issue summary\nSubject\nFrame ${frameId}` });
    const deep = await executeCommand(rt, command('002', 'transcript', {}));
    assert.match(deep.deep_text, /Issue summary\nSubject/);
    assert.match(await readFile(deep.deep_text_path, 'utf8'), /Issue summary/);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('open accepts only a Seller Assistant conversation path', () => {
  const good = '/assistant/amzn1.cyrano.conversation.cid.v2.10021790765749518386464?client=sellerSupport-meldFullPage';
  assert.equal(SA.validateCommandArgs('open', { conversation: good }).ok, true);
  for (const bad of ['https://evil.example/assistant/amzn1.cyrano.conversation.cid.v2.1002179076574951?client=sellerSupport-meldFullPage',
    '/assistant?client=sellerSupport-meldFullPage', '/assistant/amzn1.cyrano.conversation.cid.v2.123/../../x?client=sellerSupport-meldFullPage',
    '//evil.example/assistant/amzn1.cyrano.conversation.cid.v2.10021790765749518386464?client=sellerSupport-meldFullPage']) {
    assert.equal(SA.validateCommandArgs('open', { conversation: bad }).ok, false, bad);
  }
  assert.deepEqual(parseArgs(['send', '--run', '/tmp/x', 'open', '--conversation', good]).args, { conversation: good });
});

test('transcript waits are capped by the serve deadline', async () => {
  const dir = await runDir();
  try {
    const { rt } = fakeRuntime(dir);
    rt.deadline = T0 + 5000;
    const result = await executeCommand(rt, command('001', 'transcript', { 'wait-new': 5, timeout: 1800 }));
    assert.equal(result.status, 'timeout');
    assert.ok(rt.deps.now() < T0 + 10000, 'stopped near the deadline, not after 1800 s');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a client that gives up leaves a cancelled marker that serve skips', async () => {
  const dir = await runDir();
  try {
    const account = { profile_key: 'acme-us', client_slug: 'acme', marketplace: 'US', seller_id: 'A1TEST', marketplace_id: 'ATVPDKIKX0DER', seller_central_name: 'Acme', marketplace_label: 'United States', parent_account_name: 'Acme Group' };
    await writeFile(join(dir, 'run.json'), JSON.stringify({ schema_version: 1, run_id: 'sa-test', account }));
    const { spawn } = await import('node:child_process');
    const fakeServe = spawn(process.execPath, ['-e', 'setTimeout(() => {}, 60000)'], { stdio: 'ignore' });
    const exited = new Promise(r => fakeServe.once('exit', r));
    const printed = [];
    await writeFile(join(dir, 'serve.pid'), JSON.stringify({ pid: fakeServe.pid }));
    const pending = sendCommand({ run: dir, command: 'open', args: {} }, { pollMs: 10, out: line => printed.push(line) });
    await new Promise(r => setTimeout(r, 50));
    fakeServe.kill('SIGKILL'); await exited;
    assert.equal(await pending, 2);
    assert.equal(JSON.parse(printed.at(-1)).cancelled, true);
    const marker = JSON.parse(await readFile(join(dir, 'results', '001.json'), 'utf8'));
    assert.equal(marker.status, 'cancelled');
    const { rt, events } = fakeRuntime(dir);
    assert.equal(await processNext(rt), null, 'the cancelled open never runs');
    assert.ok(!events.some(e => e.startsWith('navigate:')));
    assert.equal(await cancelQueued(join(dir, 'results', '001.json'), '001', 'again'), false, 'an existing result is never overwritten');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('isolated worlds are reused per frame document and recreated when stale', async () => {
  const calls = [];
  let loader = 'L1', staleOnce = false;
  const send = async (method, params) => {
    calls.push(method);
    if (method === 'Page.getFrameTree') return { frameTree: { frame: { id: 'm', url: ASSISTANT, securityOrigin: SC, loaderId: loader } } };
    if (method === 'Page.createIsolatedWorld') return { executionContextId: calls.filter(m => m === method).length };
    if (method === 'Runtime.evaluate') {
      if (staleOnce) { staleOnce = false; throw new Error('Cannot find context with specified id'); }
      return { result: { value: { title: 't', text: '', composers: [], controls: [], counters: [], status: [], busy: false, region: { chips: [], counters: [], uploading: false }, file_inputs: { count: 0, names: [] }, conversation: { message_count: 0 } } } };
    }
    throw new Error(`unexpected ${method}`);
  };
  const browser = makeBrowser({ send }, SC);
  await browser.scan(); await browser.scan(); await browser.scan();
  assert.equal(calls.filter(m => m === 'Page.createIsolatedWorld').length, 1, 'one world for three scans');
  loader = 'L2';
  await browser.scan();
  assert.equal(calls.filter(m => m === 'Page.createIsolatedWorld').length, 2, 'a new document gets a new world');
  staleOnce = true;
  await browser.scan();
  assert.equal(calls.filter(m => m === 'Page.createIsolatedWorld').length, 3, 'a destroyed context is recreated once');
});

test('the hit test adds the main frame scroll offset to the click point', async () => {
  const hits = [];
  const send = async (method, params) => {
    if (method === 'Page.createIsolatedWorld') return { executionContextId: 5 };
    if (method === 'Runtime.evaluate') return { result: { objectId: 'button-1' } };
    if (method === 'DOM.getContentQuads') return { quads: [[0, 0, 20, 0, 20, 10, 0, 10]] };
    if (method === 'Page.getLayoutMetrics') return { cssLayoutViewport: { pageX: 0, pageY: 400 } };
    if (method === 'DOM.getNodeForLocation') { hits.push([params.x, params.y]); return { backendNodeId: 7 }; }
    if (method === 'DOM.resolveNode') return { object: { objectId: 'button-inner' } };
    if (method === 'Runtime.callFunctionOn') return { result: { value: true } };
    return {};
  };
  const point = await makeBrowser({ send }, SC).prepareClick('m', 'Submit');
  assert.deepEqual([point.x, point.y], [10, 5], 'the mouse still uses viewport coordinates');
  assert.deepEqual(hits, [[10, 405]]);
});

// ------------------------------------------------ second review regressions

// Minimal DOM for running pageAgent directly: tags, attributes, text, and the
// selector forms pageAgent uses (tag, [a="v"], [a*="v" i]).
class FakeEl {
  constructor(tag, attrs = {}, children = [], text = '') {
    Object.assign(this, { tagName: tag.toUpperCase(), attrs, children: [], parentNode: null, text, nodeType: 1, shadowRoot: null, value: attrs.value ?? '' });
    this.disabled = 'disabled' in attrs; this.readOnly = 'readonly' in attrs;
    for (const c of children) { c.parentNode = this; this.children.push(c); }
  }
  getAttribute(n) { return n in this.attrs ? String(this.attrs[n]) : null; }
  hasAttribute(n) { return n in this.attrs; }
  getBoundingClientRect() { return { width: 10, height: 10 }; }
  get textContent() { return this.text + this.children.map(c => c.textContent).join(''); }
  // The element's own text is one text node ahead of its children.
  get childNodes() {
    if (this.text && !this.textNode) this.textNode = { nodeType: 3, textContent: this.text, nodeValue: this.text, parentNode: this, parentElement: this };
    return [...(this.text ? [this.textNode] : []), ...this.children];
  }
  closest(selector) { for (let n = this; n && n.nodeType === 1; n = n.parentNode) if (n.matches(selector)) return n; return null; }
  get innerText() { return this.textContent; }
  querySelectorAll() { const out = []; const walk = n => { for (const c of n.children) { out.push(c); walk(c); } }; walk(this); return out; }
  matches(selector) {
    return selector.split(',').map(s => s.trim()).some(s => {
      if (/^[a-z-]+$/.test(s)) return this.tagName === s.toUpperCase();
      if (/^\.[\w-]+$/.test(s)) return String(this.attrs.class || '').split(/\s+/).includes(s.slice(1));
      let m = /^\[([\w-]+)="([^"]*)"\]$/.exec(s);
      if (m) return this.getAttribute(m[1]) === m[2];
      m = /^\[([\w-]+)\*="([^"]*)" i\]$/.exec(s);
      if (m) return (this.getAttribute(m[1]) || '').toLowerCase().includes(m[2].toLowerCase());
      return false;
    });
  }
}
const el = (tag, attrs, children = [], text = '') => new FakeEl(tag, attrs, children, text);
function runPage(body, op, arg) {
  // createTreeWalker yields the text nodes under a node in document order.
  const createTreeWalker = root => {
    const texts = [];
    const walk = n => { for (const c of n.childNodes || []) { if (c.nodeType === 3) texts.push(c); else walk(c); } };
    walk(root);
    let i = 0;
    return { nextNode: () => texts[i++] ?? null };
  };
  const doc = { body, nodeType: 9, readyState: 'complete', title: 't', querySelectorAll: () => [body, ...body.querySelectorAll()], createTreeWalker };
  body.parentNode = doc;
  const saved = { document: globalThis.document, location: globalThis.location, NodeFilter: globalThis.NodeFilter };
  Object.assign(globalThis, { document: doc, location: { href: ASSISTANT }, NodeFilter: { SHOW_TEXT: 4 } });
  try { return pageAgent(op, arg, { collapse, matchLabel, detectTour, composerSubmitCheck, submitLabels: SA.SUBMIT_LABELS, uploadLabels: SA.UPLOAD_LABELS, normalizeComposer: SA.normalizeComposer }); }
  finally { Object.assign(globalThis, saved); }
}
const pageCode = fn => { try { fn(); return 'ok'; } catch (error) { return /EW:([a-z_]+):/.exec(error.message)?.[1] ?? error.message; } };

test('page: Submit is clicked only as the composer\'s own enabled control', () => {
  const chat = ({ ownDisabled = false, composerDisabled = false, rating = false, ownSubmit = true, value = P1 } = {}) => {
    const own = el('button', ownDisabled ? { disabled: '' } : {}, [], 'Submit');
    const footer = el('div', {}, [el('textarea', composerDisabled ? { disabled: '', placeholder: 'Message Seller Assistant...', value } : { placeholder: 'Message Seller Assistant...', value }), ...(ownSubmit ? [own] : []), el('button', {}, [], 'Upload file')]);
    const survey = el('form', {}, [el('span', {}, [], 'Rate this chat'), el('button', {}, [], 'Submit')]);
    return { body: el('body', {}, [el('main', {}, [...(rating ? [survey] : []), footer])]), own };
  };
  const clean = chat();
  assert.equal(runPage(clean.body, 'control', { label: 'Submit', composerSubmit: true, expectedComposerText: P1 }), clean.own);
  assert.deepEqual(runPage(chat().body, 'scan').region.submit, [{ disabled: false, in_region: true }]);
  assert.equal(pageCode(() => runPage(chat({ ownDisabled: true, rating: true }).body, 'control', { label: 'Submit', composerSubmit: true })), 'submit_not_unique');
  assert.equal(pageCode(() => runPage(chat({ rating: true }).body, 'control', { label: 'Submit', composerSubmit: true })), 'submit_not_unique');
  assert.equal(pageCode(() => runPage(chat({ ownSubmit: false, rating: true }).body, 'control', { label: 'Submit', composerSubmit: true })), 'submit_outside_composer_region');
  assert.equal(pageCode(() => runPage(chat({ ownDisabled: true }).body, 'control', { label: 'Submit', composerSubmit: true })), 'submit_disabled');
  assert.equal(pageCode(() => runPage(chat({ composerDisabled: true }).body, 'control', { label: 'Submit', composerSubmit: true })), 'composer_disabled');
  assert.deepEqual(runPage(chat({ ownDisabled: true, rating: true }).body, 'scan').region.submit, [{ disabled: false, in_region: false }, { disabled: true, in_region: true }]);
});

test('submit refuses another Submit in the frame, a Submit outside the composer region and a disabled composer', async () => {
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir);
    const cases = [
      ['submit_not_unique', { controls: [{ frame_id: 'main', label: 'Submit', disabled: true }, { frame_id: 'main', label: 'Submit', disabled: false }], submit_controls: [{ disabled: true, in_region: true }, { disabled: false, in_region: false }] }],
      ['submit_outside_composer_region', { submit_controls: [{ disabled: false, in_region: false }] }],
      ['composer_disabled', { disabled: true }],
      ['submit_scope_unknown', { submit_controls: null }],
    ];
    for (const [i, [reason, change]] of cases.entries()) {
      const { controls, ...composer } = change;
      const state = baseState({ ...(controls ? { controls } : {}) });
      Object.assign(state.composer, composer, { value: P1 });
      const { rt, events } = fakeRuntime(dir, { state });
      const result = await executeCommand(rt, command(String(i + 1).padStart(3, '0'), 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
      assert.equal(result.reason, reason); assert.ok(!events.includes('dispatch'), `${reason}: no click`);
    }
    const ok = fakeRuntime(dir); ok.current.composer.value = P1;
    assert.equal((await executeCommand(ok.rt, command('009', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }))).status, 'sent');
    assert.ok(ok.events.includes('composer-scope'), 'the page lookup is told to scope Submit to the composer');
    assert.deepEqual(composerSubmitCheck({ disabled: false }, [{ disabled: false, in_region: true }]), { ok: true, index: 0 });
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('the Submit click expression carries the composer scope', async () => {
  const expressions = [];
  const send = async (method, params) => {
    if (method === 'Page.createIsolatedWorld') return { executionContextId: 5 };
    if (method === 'Runtime.evaluate') { expressions.push(params.expression); return { result: { objectId: 'button-1' } }; }
    if (method === 'DOM.getContentQuads') return { quads: [[0, 0, 20, 0, 20, 10, 0, 10]] };
    if (method === 'DOM.getNodeForLocation') return { backendNodeId: 7 };
    if (method === 'DOM.resolveNode') return { object: { objectId: 'button-inner' } };
    if (method === 'Runtime.callFunctionOn') return { result: { value: true } };
    return {};
  };
  await makeBrowser({ send }, SC).prepareClick('m', 'Submit', { composerSubmit: true });
  assert.match(expressions[0], /"composerSubmit":true/);
  assert.match(expressions[0], /const composerSubmitCheck = function composerSubmitCheck/);
});

test('submit binds attachments to attaches this run confirmed', async () => {
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir);
    const hidden = fakeRuntime(dir, { state: baseState({ attachments: { chips: [], uploading: false, file_input_count: 1, input_files: ['secret.pdf'] } }) });
    hidden.current.composer.value = P1;
    const r1 = await executeCommand(hidden.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(r1.reason, 'attachment_chips_undetected'); assert.ok(!hidden.events.includes('dispatch'));
    const chip = fakeRuntime(dir, { state: baseState({ attachments: { chips: ['restored.pdf'], uploading: false, file_input_count: 1, input_files: [] } }) });
    chip.current.composer.value = P1;
    const r2 = await executeCommand(chip.rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval, 'expect-attachment': ['restored.pdf'] }));
    assert.equal(r2.reason, 'attachment_not_approved'); assert.ok(!chip.events.includes('dispatch'));
    // Attach through the driver, then send with exactly that file.
    const file = join(dir, 'invoice.pdf'); await writeFile(file, 'pdf bytes');
    const attachApproval = await approvalFile(dir, { plan_item: 'attachment', sha256: sha256('pdf bytes') }, 'attach.json');
    const flow = fakeRuntime(dir);
    assert.equal((await executeCommand(flow.rt, command('003', 'attach', { file, sha256: sha256('pdf bytes'), 'approval-file': attachApproval }))).status, 'attached');
    flow.current.composer.value = P1;
    assert.equal((await executeCommand(flow.rt, command('004', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }))).reason, 'attachment_mismatch', 'an attached file must be expected');
    const sent = await executeCommand(flow.rt, command('005', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval, 'expect-attachment': ['invoice.pdf'] }));
    assert.equal(sent.status, 'sent');
    assert.equal(attachmentCheck({ chips: ['a.pdf'], input_files: ['a.pdf', 'b.pdf'] }, ['a.pdf'], ['a.pdf']).reason, 'attachment_not_approved');
    assert.equal(attachmentCheck({ chips: [], input_files: [] }, ['a.pdf'], []).reason, 'expected_attachment_not_approved');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('any failure after an outbound dispatch is uncertain with a result line', async () => {
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir);
    const phases = async () => (await readFile(join(dir, 'approvals.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse).map(x => [x.phase, x.status ?? null]);
    const frameGone = Object.assign(new Error('No frame for given id found'), {});
    const s1 = fakeRuntime(dir, { afterClick: { occurrences: frameGone } }); s1.current.composer.value = P1;
    const r1 = await executeCommand(s1.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(r1.status, 'uncertain'); assert.equal(r1.clicked, true);
    assert.deepEqual(await phases(), [['attempt', null], ['result', 'uncertain']]);
    await rm(join(dir, 'approvals.jsonl'));
    const s2 = fakeRuntime(dir, { afterClick: { targets: new Error('Target.getTargets failed') } }); s2.current.composer.value = P1;
    const r2 = await executeCommand(s2.rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(r2.status, 'uncertain'); assert.equal(r2.clicked, true);
    await rm(join(dir, 'approvals.jsonl'));
    const lost = Object.assign(new Error('TASK_TAB_CONTROL_LOST'), { code: 'TASK_TAB_CONTROL_LOST' });
    const s3 = fakeRuntime(dir, { afterClick: { occurrences: lost } }); s3.current.composer.value = P1;
    const r3 = await executeCommand(s3.rt, command('003', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(r3.status, 'uncertain'); assert.equal(r3.clicked, true); assert.equal(s3.rt.fatal, true);
    await rm(join(dir, 'approvals.jsonl'));
    // The result line cannot be written: still uncertain, never error.
    const s4 = fakeRuntime(dir, { onDispatch: () => chmod(join(dir, 'approvals.jsonl'), 0o444) }); s4.current.composer.value = P1;
    const r4 = await executeCommand(s4.rt, command('004', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    await chmod(join(dir, 'approvals.jsonl'), 0o644);
    assert.equal(r4.status, 'uncertain'); assert.equal(r4.clicked, true); assert.ok(r4.log_error);
    await rm(join(dir, 'approvals.jsonl'));
    const terms = 'Connect with an associate\nApprove';
    const approveState = baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Approve', disabled: false }], handoff: { approve_count: 1, terms_text: terms } });
    const a = fakeRuntime(dir, { state: approveState, afterClick: { scan: new Error('No frame for given id found') } });
    const ra = await executeCommand(a.rt, command('005', 'approve', { 'expect-terms-sha256': termsHash(terms), 'approval-file': await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(terms) }, 'ap.json') }));
    assert.equal(ra.status, 'uncertain'); assert.equal(ra.clicked, true);
    await rm(join(dir, 'approvals.jsonl'));
    const file = join(dir, 'invoice.pdf'); await writeFile(file, 'pdf bytes');
    const f = fakeRuntime(dir, { afterClick: { scan: new Error('No frame for given id found') } });
    const rf = await executeCommand(f.rt, command('006', 'attach', { file, sha256: sha256('pdf bytes'), 'approval-file': await approvalFile(dir, { plan_item: 'attachment', sha256: sha256('pdf bytes') }, 'at.json') }));
    assert.equal(rf.status, 'uncertain'); assert.equal(rf.attached, true);
    assert.deepEqual(await phases(), [['attempt', null], ['result', 'uncertain']]);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('serve marks a command running before it executes and never re-runs an interrupted one', async () => {
  const dir = await runDir();
  try {
    const seen = [];
    const { rt, events } = fakeRuntime(dir, { identity: async () => { seen.push(existsSync(join(dir, 'results', '001.running'))); return { merchant_id: SELLER, marketplace_id: 'M', source: 'live' }; } });
    await writeFile(join(dir, 'queue', '001.json'), JSON.stringify(command('001', 'state')));
    await processNext(rt);
    assert.equal(seen[0], true, 'marker present while the command runs');
    assert.ok(!existsSync(join(dir, 'results', '001.running')), 'marker removed with the result');
    // A previous serve died: 002 has a marker, 003 has an attempt without result,
    // 004 has a marker and a cancelled result written by a client that lost the race.
    const approval = await approvalFile(dir);
    for (const id of ['002', '003', '004', '005']) await writeFile(join(dir, 'queue', `${id}.json`), JSON.stringify(command(id, 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval })));
    await writeFile(join(dir, 'results', '002.running'), '{}');
    await writeFile(join(dir, 'approvals.jsonl'), JSON.stringify({ queue_id: '003', phase: 'attempt', command: 'submit', sha256: P1_SHA }) + '\n');
    await writeFile(join(dir, 'results', '004.running'), '{}');
    await writeFile(join(dir, 'results', '004.json'), JSON.stringify({ id: '004', status: 'cancelled' }));
    assert.deepEqual(await recoverInterrupted(dir, T0), ['002', '003', '004']);
    for (const id of ['002', '003', '004']) {
      const r = JSON.parse(await readFile(join(dir, 'results', `${id}.json`), 'utf8'));
      assert.equal(r.status, 'uncertain'); assert.equal(r.reason, 'interrupted');
      assert.ok(!existsSync(join(dir, 'results', `${id}.running`)));
    }
    const log = (await readFile(join(dir, 'approvals.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse);
    assert.deepEqual(log.map(x => [x.queue_id, x.phase, x.status ?? null]), [['003', 'attempt', null], ['003', 'result', 'uncertain']]);
    // A marker found by the loop itself is also never executed.
    await writeFile(join(dir, 'results', '005.running'), '{}');
    rt.current = null;
    const r5 = await processNext(rt);
    assert.equal(r5.id, '005'); assert.equal(r5.status, 'uncertain');
    assert.ok(!events.includes('dispatch'));
    assert.equal(await processNext(rt), null);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('the signal and crash path marks the command in flight uncertain', async () => {
  const dir = await runDir();
  try {
    const { rt } = fakeRuntime(dir);
    rt.current = command('007', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': '/x.json' });
    rt.dispatch = { command: 'submit', sha256: P1_SHA, kind: 'clicked', logged: false };
    await writeFile(join(dir, 'results', '007.running'), '{}');
    const r = await markInFlight(rt, 'SIGTERM');
    assert.equal(r.status, 'uncertain'); assert.equal(r.clicked, true);
    const saved = JSON.parse(await readFile(join(dir, 'results', '007.json'), 'utf8'));
    assert.equal(saved.status, 'uncertain'); assert.equal(saved.reason, 'interrupted');
    const log = (await readFile(join(dir, 'approvals.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse);
    assert.deepEqual(log.map(x => [x.queue_id, x.phase, x.status]), [['007', 'result', 'uncertain']]);
    rt.current = command('008', 'state'); rt.dispatch = null;
    assert.equal((await markInFlight(rt, 'uncaughtException')).status, 'error');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('send reports uncertain, not cancelled, when serve died while running its command', async () => {
  const dir = await runDir();
  try {
    const account = { profile_key: 'acme-us', client_slug: 'acme', marketplace: 'US', seller_id: SELLER, marketplace_id: 'ATVPDKIKX0DER', seller_central_name: 'Acme', marketplace_label: 'United States', parent_account_name: 'Acme Group' };
    await writeFile(join(dir, 'run.json'), JSON.stringify({ schema_version: 1, run_id: RUN_ID, account }));
    const { spawn } = await import('node:child_process');
    for (const [id, how] of [['001', 'attempt'], ['002', 'marker']]) {
      const fakeServe = spawn(process.execPath, ['-e', 'setTimeout(() => {}, 60000)'], { stdio: 'ignore' });
      const exited = new Promise(r => fakeServe.once('exit', r));
      await writeFile(join(dir, 'serve.pid'), JSON.stringify({ pid: fakeServe.pid }));
      const printed = [];
      const pending = sendCommand({ run: dir, command: 'submit', args: { 'expect-sha256': P1_SHA, 'approval-file': '/a.json' } }, { pollMs: 10, out: line => printed.push(line) });
      await new Promise(r => setTimeout(r, 50));
      if (how === 'attempt') await appendFile(join(dir, 'approvals.jsonl'), JSON.stringify({ queue_id: id, phase: 'attempt', command: 'submit', sha256: P1_SHA }) + '\n');
      else await writeFile(join(dir, 'results', `${id}.running`), '{}');
      fakeServe.kill('SIGKILL'); await exited;
      assert.equal(await pending, 2);
      const out = JSON.parse(printed.at(-1));
      assert.equal(out.status, 'uncertain', how); assert.ok(!out.cancelled);
      assert.equal(JSON.parse(await readFile(join(dir, 'results', `${id}.json`), 'utf8')).status, 'uncertain');
      assert.equal(await commandInFlight(dir, id), true, 'a later serve still sees it as interrupted');
    }
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('approvals are bound to the run, the seller and a real past time', async () => {
  const good = { schema_version: 1, plan_item: 'P1', sha256: P1_SHA, approved_at: '2026-09-29T11:59:00Z', approval_text: 'Go.', run_id: RUN_ID, seller_id: SELLER, label: 'routine' };
  const ctx = { runId: RUN_ID, sellerId: SELLER, now: T0 };
  assert.equal(validateApproval(good, P1_SHA, undefined, ctx).ok, true);
  assert.equal(validateApproval({ ...good, run_id: 'sa-old' }, P1_SHA, undefined, ctx).reason, 'approval_run_mismatch');
  assert.equal(validateApproval({ ...good, seller_id: 'A2OTHER' }, P1_SHA, undefined, ctx).reason, 'approval_seller_mismatch');
  assert.equal(validateApproval({ ...good, run_id: undefined }, P1_SHA, undefined, ctx).reason, 'approval_run_id_missing');
  assert.equal(validateApproval({ ...good, seller_id: undefined }, P1_SHA, undefined, ctx).reason, 'approval_seller_id_missing');
  assert.equal(validateApproval(good, P1_SHA).reason, 'approval_context_missing');
  assert.equal(validateApproval({ ...good, approved_at: '2026-09-29T12:06:00Z' }, P1_SHA, undefined, ctx).reason, 'approval_time_in_future');
  assert.equal(validateApproval({ ...good, approved_at: '2026-09-29T12:04:00Z' }, P1_SHA, undefined, ctx).ok, true, 'five minutes of clock skew');
  assert.equal(validateApproval({ ...good, approved_at: '2026-02-31T10:00:00Z' }, P1_SHA, undefined, ctx).reason, 'approval_time_invalid');
  assert.equal(isIsoTime('2026-09-29T10:00:00+02:00'), true); assert.equal(isIsoTime('2026-09-29T24:00:00Z'), false);
  const dir = await runDir();
  try {
    const { rt, events, current } = fakeRuntime(dir); current.composer.value = P1;
    const other = await approvalFile(dir, { run_id: 'sa-earlier-run' }, 'old.json');
    assert.equal((await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': other }))).reason, 'approval_run_mismatch');
    assert.ok(!events.includes('dispatch'));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('approve waits for an idle page and needs a visible effect of the click', async () => {
  const dir = await runDir();
  try {
    const terms = 'Connect with an associate\nA Seller Support associate will join this chat.\nApprove';
    const state = (extra = {}) => baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Approve', disabled: false }], handoff: { approve_count: 1, terms_text: terms }, ...extra });
    const approval = await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(terms) }, 'approve.json');
    const args = { 'expect-terms-sha256': termsHash(terms), 'approval-file': approval };
    const busy = fakeRuntime(dir, { state: state({ busy: true }) });
    const r1 = await executeCommand(busy.rt, command('001', 'approve', args));
    assert.equal(r1.reason, 'assistant_busy'); assert.ok(!busy.events.includes('dispatch'));
    const onlyMessage = fakeRuntime(dir, { state: state(), approveEffect: 'message_only' });
    const r2 = await executeCommand(onlyMessage.rt, command('002', 'approve', args));
    assert.equal(r2.status, 'uncertain'); assert.equal(r2.reason, 'no_visible_change');
    await rm(join(dir, 'approvals.jsonl'));
    const removed = fakeRuntime(dir, { state: state(), approveEffect: 'remove' });
    assert.equal((await executeCommand(removed.rt, command('003', 'approve', args))).status, 'approved');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a live ID that differs fails at once; home IDs fill only missing fields', () => {
  const account = { seller_id: 'S', marketplace_id: 'M' };
  assert.deepEqual(resolveIdentity({ merchantId: 'OTHER', marketplace: null }, { merchantId: 'S', marketplace: 'M' }, account), { ok: false, reason: 'live seller ID differs' });
  assert.equal(resolveIdentity({ merchantId: null, marketplace: { marketplaceId: 'X' } }, { merchantId: 'S', marketplace: 'M' }, account).reason, 'live marketplace ID differs');
  assert.deepEqual(resolveIdentity({ merchantId: 'S', marketplace: null }, { merchantId: 'S', marketplace: 'M' }, account), { ok: true, identity: { merchantId: 'S', marketplace: 'M' }, source: 'live+home' });
  assert.equal(resolveIdentity(null, { merchantId: 'S', marketplace: 'M' }, account).source, 'home+header');
  assert.equal(resolveIdentity({ merchantId: 'S', marketplace: 'M' }, null, account).source, 'live');
});

test('run.json keeps and validates the context binding', async () => {
  const account = { profile_key: 'acme-us', client_slug: 'acme', marketplace: 'US', seller_id: 'S', marketplace_id: 'M', seller_central_name: 'Acme', marketplace_label: 'United States', parent_account_name: 'Acme',
    context_binding: { seller_id: 'S', marketplace_id: 'M', unique_label_mapping: true } };
  const kept = validateRunConfig({ schema_version: 1, run_id: 'r1', account });
  assert.deepEqual(kept.account.context_binding, { seller_id: 'S', marketplace_id: 'M', unique_label_mapping: true });
  const { contextMatches } = await import('../browser-ui.mjs');
  const header = { url: `${SC}/assistant`, contextTokens: [['acme', 'united states']], contexts: [], identity: { merchantId: null, marketplace: null } };
  assert.equal(contextMatches(header, kept.account, 'sc'), true, 'header-only pages still verify through the binding');
  assert.throws(() => validateRunConfig({ schema_version: 1, run_id: 'r1', account: { ...account, context_binding: { ...account.context_binding, seller_id: 'OTHER' } } }), /context_binding IDs/);
  assert.throws(() => validateRunConfig({ schema_version: 1, run_id: 'r1', account: { ...account, context_binding: { ...account.context_binding, unique_label_mapping: false } } }), /unique_label_mapping/);
  assert.throws(() => validateRunConfig({ schema_version: 1, run_id: 'r1', account: { ...account, context_binding: 'yes' } }), /must be an object/);
});

test('attach uploads a private copy hashed after it was written', async () => {
  const dir = await runDir();
  try {
    const file = join(dir, 'invoice.pdf'); await writeFile(file, 'pdf bytes');
    const approval = await approvalFile(dir, { plan_item: 'attachment', sha256: sha256('pdf bytes') }, 'attach.json');
    // The source changes between the hash check and the upload.
    let calls = 0;
    const { rt, uploads } = fakeRuntime(dir, { identity: async () => { if (++calls === 2) await writeFile(file, 'swapped bytes'); return { merchant_id: SELLER, marketplace_id: 'M', source: 'live' }; } });
    const result = await executeCommand(rt, command('001', 'attach', { file, sha256: sha256('pdf bytes'), 'approval-file': approval }));
    assert.equal(result.status, 'attached');
    assert.equal(uploads.length, 1);
    assert.equal(uploads[0].path, join(dir, 'uploads', '01', 'invoice.pdf'));
    assert.equal(uploads[0].bytes, 'pdf bytes', 'Amazon receives the approved bytes');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('an interrupt stops every click, insert and upload that has not started', async () => {
  const dir = await runDir();
  try {
    assert.equal(typeof SA.abortHandler, 'function', 'abortHandler is exported');
    const interrupt = rt => {
      const ctl = { exiting: false, rt };
      // Not awaited: the handler must set the flag before its first await.
      SA.abortHandler(ctl, 'SIGTERM', async () => { await markInFlight(rt, 'SIGTERM'); })();
      assert.equal(rt.aborting, true, 'flag set synchronously');
    };
    const log = async () => existsSync(join(dir, 'approvals.jsonl')) ? (await readFile(join(dir, 'approvals.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse) : [];
    // Submit: the interrupt lands during the pre-click identity read.
    let calls = 0, s;
    s = fakeRuntime(dir, { identity: async () => { if (++calls === 2) interrupt(s.rt); return { merchant_id: SELLER, marketplace_id: 'M', source: 'live' }; } });
    s.current.composer.value = P1;
    const r1 = await executeCommand(s.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(r1.status, 'blocked'); assert.equal(r1.reason, 'aborting'); assert.equal(r1.clicked, false);
    assert.ok(!s.events.includes('dispatch')); assert.deepEqual(await log(), [], 'no attempt line');
    // Approve: same point.
    const terms = 'Connect with an associate\nApprove';
    const approveState = baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Approve', disabled: false }], handoff: { approve_count: 1, terms_text: terms } });
    calls = 0;
    const a = fakeRuntime(dir, { state: approveState, identity: async () => { if (++calls === 2) interrupt(a.rt); return { merchant_id: SELLER, marketplace_id: 'M', source: 'live' }; } });
    const r2 = await executeCommand(a.rt, command('002', 'approve', { 'expect-terms-sha256': termsHash(terms), 'approval-file': await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(terms) }, 'ap.json') }));
    assert.equal(r2.status, 'blocked'); assert.equal(r2.reason, 'aborting'); assert.ok(!a.events.includes('dispatch'));
    // Attach: the interrupt lands right before the upload.
    const file = join(dir, 'invoice.pdf'); await writeFile(file, 'pdf bytes');
    calls = 0;
    const f = fakeRuntime(dir, { identity: async () => { if (++calls === 2) interrupt(f.rt); return { merchant_id: SELLER, marketplace_id: 'M', source: 'live' }; } });
    const r3 = await executeCommand(f.rt, command('003', 'attach', { file, sha256: sha256('pdf bytes'), 'approval-file': await approvalFile(dir, { plan_item: 'attachment', sha256: sha256('pdf bytes') }, 'at.json') }));
    assert.equal(r3.status, 'blocked'); assert.equal(r3.reason, 'aborting'); assert.ok(!f.events.includes('set-file'));
    // Type: the interrupt lands during the identity read before the handler.
    const text = join(dir, 'p1.txt'); await writeFile(text, P1);
    const t = fakeRuntime(dir, { identity: async () => { interrupt(t.rt); return { merchant_id: SELLER, marketplace_id: 'M', source: 'live' }; } });
    const r4 = await executeCommand(t.rt, command('004', 'type', { 'text-file': text, sha256: P1_SHA }));
    assert.equal(r4.status, 'blocked'); assert.ok(!t.events.includes('insert'));
    assert.deepEqual(await log(), [], 'no attempt line from any stopped action');
    // No new command starts once aborting.
    const q = fakeRuntime(dir); q.rt.aborting = true;
    await writeFile(join(dir, 'queue', '005.json'), JSON.stringify(command('005', 'state')));
    assert.equal(await processNext(q.rt), null);
    assert.ok(!existsSync(join(dir, 'results', '005.running')) && !existsSync(join(dir, 'results', '005.json')));
    assert.deepEqual(await serveLoop(q.rt, { started: T0, maxMs: 60000, idleMs: 60000 }), { exitReason: 'aborting', outcome: 'error' });
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('approved needs the effect on two consecutive scans with the frame reachable', async () => {
  const dir = await runDir();
  try {
    const terms = 'Connect with an associate\nApprove';
    const state = baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Approve', disabled: false }], handoff: { approve_count: 1, terms_text: terms } });
    const args = async name => ({ 'expect-terms-sha256': termsHash(terms), 'approval-file': await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(terms) }, name) });
    // One empty scan during a re-render, then the unchanged page.
    const x = fakeRuntime(dir, { state, approveEffect: 'message_only' });
    const scan = x.rt.browser.scan;
    let dropped = false;
    x.rt.browser.scan = async () => {
      const s = await scan();
      if (x.events.includes('dispatch') && !dropped) { dropped = true; return { ...s, frames: [], controls: [], composer: null, selection: { ok: false, reason: 'no_composer_frame' } }; }
      return s;
    };
    const r1 = await executeCommand(x.rt, command('001', 'approve', await args('a1.json')));
    assert.ok(dropped); assert.equal(r1.status, 'uncertain'); assert.equal(r1.reason, 'no_visible_change');
    await rm(join(dir, 'approvals.jsonl'));
    // One scan with the effect and a valid selection, then Approve is back.
    const y = fakeRuntime(dir, { state, approveEffect: 'message_only' });
    const scanY = y.rt.browser.scan;
    let once = false;
    y.rt.browser.scan = async () => {
      const s = await scanY();
      if (y.events.includes('dispatch') && !once) { once = true; return { ...s, controls: s.controls.filter(c => c.label !== 'Approve') }; }
      return s;
    };
    assert.equal((await executeCommand(y.rt, command('002', 'approve', await args('a2.json')))).status, 'uncertain');
    await rm(join(dir, 'approvals.jsonl'));
    // A lasting effect is approved.
    const z = fakeRuntime(dir, { state, approveEffect: 'remove' });
    assert.equal((await executeCommand(z.rt, command('003', 'approve', await args('a3.json')))).status, 'approved');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a click that opens a new target reports its delivery and keeps the lockout', async () => {
  const dir = await runDir();
  try {
    const s = fakeRuntime(dir, { newTargetOnClick: true }); s.current.composer.value = P1;
    const r1 = await executeCommand(s.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(r1.status, 'sent'); assert.equal(r1.delivery, 'sent'); assert.equal(r1.reason, 'new_target');
    assert.equal(r1.lockout.reason, 'new_target'); assert.equal(s.rt.lockout.reason, 'new_target');
    // The identity check after the click fails: still reported as sent.
    let calls = 0;
    const u = fakeRuntime(dir, { newTargetOnClick: true, identity: async () => { if (++calls === 3) throw new Error('header gone'); return { merchant_id: SELLER, marketplace_id: 'M', source: 'live' }; } });
    u.current.composer.value = 'Please connect me with a Seller Support associate.';
    const p2 = sha256(u.current.composer.value);
    const r2 = await executeCommand(u.rt, command('002', 'submit', { 'expect-sha256': p2, 'approval-file': await approvalFile(dir, { plan_item: 'P2', sha256: p2 }, 'p2.json') }));
    assert.equal(r2.status, 'sent_identity_unverified'); assert.equal(r2.delivery, 'sent');
    const terms = 'Connect with an associate\nApprove';
    const a = fakeRuntime(dir, { newTargetOnClick: true, approveEffect: 'remove', state: baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Approve', disabled: false }], handoff: { approve_count: 1, terms_text: terms } }) });
    const r3 = await executeCommand(a.rt, command('003', 'approve', { 'expect-terms-sha256': termsHash(terms), 'approval-file': await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(terms) }, 'ap.json') }));
    assert.equal(r3.status, 'approved'); assert.equal(r3.reason, 'new_target'); assert.equal(r3.lockout.reason, 'new_target');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('an attached name is used up by the submit that carried it', async () => {
  const dir = await runDir();
  try {
    const attached = { phase: 'result', command: 'attach', status: 'attached', name: 'a.pdf' };
    assert.deepEqual(SA.approvedAttachmentNames([attached]), ['a.pdf']);
    assert.deepEqual(SA.approvedAttachmentNames([attached, { queue_id: '002', phase: 'attempt', command: 'submit', attachments: ['a.pdf'] }, { queue_id: '002', phase: 'result', command: 'submit', status: 'uncertain' }]), []);
    assert.deepEqual(SA.approvedAttachmentNames([attached, { queue_id: '002', phase: 'attempt', command: 'submit', attachments: ['a.pdf'] }, { queue_id: '002', phase: 'result', command: 'submit', status: 'blocked', reason: 'aborting' }]), ['a.pdf'], 'a submit stopped before the click uses nothing');
    assert.deepEqual(SA.approvedAttachmentNames([attached, { queue_id: '002', phase: 'attempt', command: 'submit', attachments: ['a.pdf'] }, { ...attached }]), ['a.pdf'], 'a new approved attach counts again');
    // Through the driver: attach, send with it, then the same chip is still there.
    const file = join(dir, 'invoice.pdf'); await writeFile(file, 'pdf bytes');
    const flow = fakeRuntime(dir);
    assert.equal((await executeCommand(flow.rt, command('001', 'attach', { file, sha256: sha256('pdf bytes'), 'approval-file': await approvalFile(dir, { plan_item: 'attachment', sha256: sha256('pdf bytes') }, 'attach.json') }))).status, 'attached');
    flow.current.composer.value = P1;
    assert.equal((await executeCommand(flow.rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir), 'expect-attachment': ['invoice.pdf'] }))).status, 'sent');
    const p2 = 'Please connect me with a Seller Support associate.';
    flow.current.composer.value = p2;
    const again = await executeCommand(flow.rt, command('003', 'submit', { 'expect-sha256': sha256(p2), 'approval-file': await approvalFile(dir, { plan_item: 'P2', sha256: sha256(p2) }, 'p2.json'), 'expect-attachment': ['invoice.pdf'] }));
    assert.equal(again.status, 'refused'); assert.equal(again.reason, 'attachment_not_approved');
    assert.equal(flow.sent.length, 1);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

// ------------------------------------------------ attended case replies (9222)

const CASE_ID = '22354454371';
const CASE_URL = `${SC}/cu/case-dashboard/view-case?caseID=${CASE_ID}`;
// Shape of the 2026-10-01 Evora chat window URL.
const CHAT_URL = `${SC}/hill/website/chat?formType=reply&originalHttpRequestId=RVB41GNAWCS48T6AZPXD&caseID=${CASE_ID}&contactRequestId=${CASE_ID}%3ACRQ%2Fabc`;
const P3 = 'Dear Amazon Support,\n\nPlease escalate the catalog issue for ASIN B0TEST0001.\n\nVictor Uhl\nEcom Wizards';
const P3_SHA = sha256(P3);
const ATTENDED = { kind: 'attended', requester_id: 'U01', source: { session_id: 'session-1', instruction: 'Approved, send P1 as drafted.' } };
// A reply run is bound to its registry row (open --case refuses otherwise).
const BOUND = { registry_id: 'b8b31850', baseline: { last_sent_at: '2026-09-30T14:02:11+00:00' }, authorization: ATTENDED };
const claimed = async () => ({ ok: true, status: 'claimed' });

function caseState(overrides = {}) {
  const state = baseState({ url: CASE_URL, frames: [{ frame_id: 'main', url: CASE_URL, origin: SC, same_origin: true, reachable: true, composer_count: 1 }],
    controls: [{ frame_id: 'main', label: 'Reply', disabled: false }, { frame_id: 'main', label: 'Cancel', disabled: false }, { frame_id: 'main', label: 'Chat now', disabled: false }],
    name_field: { count: 1, value: 'Thermoslim LLC', disabled: false }, ...overrides });
  Object.assign(state.composer, { label: '', submit_controls: [], submit_by_label: { Submit: [], Send: [], 'Chat now': [{ disabled: false, in_region: true }] } });
  return state;
}
/** A runtime on the case page plus the chat window Chat now opens. */
function chatRuntime(dir, { popups = null, adopt = null, claim = null, config = {} } = {}) {
  const chatState = baseState({ url: CHAT_URL, frames: [{ frame_id: 'main', url: CHAT_URL, origin: SC, same_origin: true, reachable: true, composer_count: 1 }],
    controls: [{ frame_id: 'main', label: 'Send', disabled: false }, { frame_id: 'main', label: 'Attach', disabled: false }, { frame_id: 'main', label: 'End chat', disabled: false }] });
  Object.assign(chatState.composer, { label: 'Write here and press Enter', submit_controls: [], submit_by_label: { Submit: [], Send: [{ disabled: false, in_region: true }], 'Chat now': [] } });
  let chat = null, opened = false;
  chat = fakeRuntime(dir, { state: chatState, onDispatch: label => {
    if (label === 'Send') { chat.sent.push(chat.current.composer.value); chat.current.composer.value = ''; chat.current.message_count += 1; }
  } });
  const counted = chat.rt.browser.occurrences;
  chat.rt.browser.occurrences = async (frame, text) => text === SA.CHAT_OPENING_LINE ? { full: 1, prefix: 1, composer_value: chat.current.composer.value, message_count: chat.current.message_count } : counted(frame, text);
  const main = fakeRuntime(dir, { state: caseState(), onDispatch: label => { if (label === 'Chat now') opened = true; } });
  const infos = () => [{ targetId: 'task', type: 'page', url: CASE_URL, openerId: null },
    ...(opened ? (popups ?? [{ targetId: 'chat-1', type: 'page', url: CHAT_URL, openerId: 'task' }]) : [])];
  Object.assign(main.rt.browser, {
    targets: async () => infos().map(t => t.targetId), targetInfos: async () => infos(),
    fillName: async (_frame, text) => { main.events.push('fill-name'); main.current.name_field.value = text; },
  });
  Object.assign(main.rt, { caseId: CASE_ID, taskTargetId: 'task', chat: null, config: { ...main.rt.config, ...BOUND, signature_name: 'Victor', ...config } });
  main.rt.deps.adoptChat = adopt || (async target => { main.events.push(`adopt:${target.targetId}`); return { targetId: target.targetId, browser: chat.rt.browser, release: async () => {} }; });
  main.rt.deps.claimAttended = claim || claimed;
  return { ...main, chat };
}
/** A runtime bound to a case registry row, on the case page state by default. */
function boundRuntime(dir, options = { state: caseState() }) {
  const run = fakeRuntime(dir, options);
  Object.assign(run.rt.config, BOUND);
  run.rt.deps.claimAttended = claimed;
  return run;
}
const readLog = async dir => existsSync(join(dir, 'approvals.jsonl')) ? (await readFile(join(dir, 'approvals.jsonl'), 'utf8')).trim().split('\n').map(JSON.parse) : [];

test('session: operator on 9222 for attended runs, never from Grimoire, Grimoire on 9223', () => {
  const human = '0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-com.t3tools.T3Code-1.scope\n';
  assert.deepEqual(SA.assertSession({}, human), { session: 'grimoire', port: 9223, lockPort: 9223 });
  assert.deepEqual(SA.assertSession({ CDP_PORT: '9223', AMAZON_BROWSER_SESSION: 'grimoire' }, human), { session: 'grimoire', port: 9223, lockPort: 9223 });
  assert.deepEqual(SA.assertSession({ CDP_PORT: '9222' }, human), { session: 'operator', port: 9222, lockPort: null });
  assert.deepEqual(SA.assertSession({ AMAZON_BROWSER_SESSION: 'operator' }, human), { session: 'operator', port: 9222, lockPort: null });
  const code = (env, cgroup = human) => { try { SA.assertSession(env, cgroup); return 'ok'; } catch (error) { return error.code; } };
  assert.equal(code({ AMAZON_BROWSER_SESSION: 'operator', CDP_PORT: '9223' }), 'session_invalid');
  assert.equal(code({ AMAZON_BROWSER_SESSION: 'grimoire', CDP_PORT: '9222' }), 'session_invalid');
  assert.equal(code({ AMAZON_BROWSER_SESSION: 'other' }), 'session_invalid');
  assert.equal(code({ CDP_PORT: '9555' }), 'session_invalid');
  assert.equal(code({ AMAZON_BROWSER_SESSION: 'operator', CDP_PORT: '9222', WIZARDS_AI_MODE: '1' }), 'attended_context_required');
  assert.equal(code({ CDP_PORT: '9222', WIZARDS_AI_MODE: '' }), 'attended_context_required', 'set but empty still counts');
  assert.equal(code({ CDP_PORT: '9222' }, '0::/user.slice/user-1000.slice/user@1000.service/app.slice/wizards-ai-case-daily.service\n'), 'attended_context_required');
  assert.equal(code({ CDP_PORT: '9222' }, '12:pids:/system.slice/wizards-ai-transport.service\n'), 'attended_context_required');
  assert.equal(code({ CDP_PORT: '9223', WIZARDS_AI_MODE: '1' }, '0::/system.slice/wizards-ai-case-daily.service\n'), 'ok', 'Grimoire keeps its own session');
  assert.equal(SA.unattendedContext({}, human), false);
  assert.equal(SA.unattendedContext({}, ''), false);
});

test('serve takes the session lock only when bound to 9223', () => {
  const calls = [];
  const lock = { acquireSessionLock: (port, owner) => { calls.push([port, owner]); return () => calls.push(['released', port]); } };
  const grimoire = SA.acquireServeLock({ session: 'grimoire', port: 9223, lockPort: 9223 }, lock);
  assert.deepEqual(calls, [[9223, 'seller-assistant']]);
  grimoire();
  assert.deepEqual(calls.at(-1), ['released', 9223]);
  calls.length = 0;
  const operator = SA.acquireServeLock({ session: 'operator', port: 9222, lockPort: null }, lock);
  assert.equal(typeof operator, 'function'); operator();
  assert.deepEqual(calls, [], 'no lock call at all on 9222');
});

test('open --case opens the case page; Reply is a navigation target only there', async () => {
  assert.deepEqual(parseArgs(['send', '--run', '/tmp/x', 'open', '--case', CASE_ID]).args, { case: CASE_ID });
  assert.equal(SA.validateCommandArgs('open', { case: '12ab5' }).ok, false);
  assert.equal(SA.validateCommandArgs('open', { case: '1234' }).ok, false);
  const dir = await runDir();
  try {
    const opened = boundRuntime(dir);
    const result = await executeCommand(opened.rt, command('001', 'open', { case: CASE_ID }));
    assert.equal(result.status, 'ok'); assert.equal(result.case_id, CASE_ID); assert.equal(result.reply_present, true);
    assert.deepEqual(opened.events.filter(e => e.startsWith('navigate:')), [`navigate:${CASE_URL}`], 'straight to the case, not the lobby');
    assert.equal(opened.rt.caseId, CASE_ID);
    assert.ok(!opened.events.includes('dispatch'));
    const both = boundRuntime(dir);
    assert.equal((await executeCommand(both.rt, command('002', 'open', { case: CASE_ID, 'via-lobby': true }))).reason, 'case_with_other_target');
    assert.ok(!both.events.some(e => e.startsWith('navigate:')));
    const elsewhere = boundRuntime(dir, {});
    const missed = await executeCommand(elsewhere.rt, command('003', 'open', { case: CASE_ID }));
    assert.equal(missed.status, 'blocked'); assert.equal(missed.reason, 'case_page_not_reached'); assert.equal(elsewhere.rt.caseId ?? null, null);
    // Reply: allowed on the opened case page only; it clicks Reply and sends nothing.
    assert.deepEqual(isNavigationAllowed('Reply', { url: CASE_URL }), { ok: true, kind: 'reply' });
    assert.equal(isNavigationAllowed('Reply', { url: ASSISTANT }).reason, 'reply_not_on_case_page');
    assert.equal(isNavigationAllowed('Reply', { url: CASE_URL }, { caseId: '99999999' }).reason, 'reply_not_on_case_page');
    assert.equal(isNavigationAllowed('Reply', { url: CASE_URL.replace(SC, 'https://sellercentral.amazon.de') }, { origin: SC }).reason, 'reply_not_on_case_page');
    const reply = await executeCommand(opened.rt, command('004', 'navigate', { label: 'Reply' }));
    assert.equal(reply.status, 'ok'); assert.equal(reply.kind, 'reply');
    assert.ok(opened.events.includes('prepare:Reply') && opened.events.includes('dispatch'));
    const onAssistant = fakeRuntime(dir, { state: baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Reply', disabled: false }] }) });
    assert.equal((await executeCommand(onAssistant.rt, command('005', 'navigate', { label: 'Reply' }))).reason, 'reply_not_on_case_page');
    const notOpened = fakeRuntime(dir, { state: caseState() });
    assert.equal((await executeCommand(notOpened.rt, command('006', 'navigate', { label: 'Reply' }))).reason, 'case_not_opened');
    assert.ok(!onAssistant.events.includes('dispatch') && !notOpened.events.includes('dispatch'));
    // A run that is not bound to the case's registry row never reaches the case page.
    const unbound = fakeRuntime(dir, { state: caseState() });
    assert.equal((await executeCommand(unbound.rt, command('007', 'open', { case: CASE_ID }))).reason, 'registry_binding_required');
    assert.ok(!unbound.events.some(e => e.startsWith('navigate:')));
    assert.ok(!existsSync(join(dir, 'approvals.jsonl')), 'opening a case and its reply form logs no send');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('submit --label takes Submit, Send or Chat now and clicks only that composer control', async () => {
  assert.equal(parseArgs(['send', '--run', 'r', 'submit', '--expect-sha256', P1_SHA, '--approval-file', 'a.json']).args.label, undefined, 'Submit by default');
  assert.equal(parseArgs(['send', '--run', 'r', 'submit', '--expect-sha256', P1_SHA, '--approval-file', 'a.json', '--label', 'Chat now']).args.label, 'Chat now');
  assert.throws(() => parseArgs(['send', '--run', 'r', 'submit', '--expect-sha256', P1_SHA, '--approval-file', 'a.json', '--label', 'Reply']), /invalid_flag:label/);
  assert.equal(SA.validateCommandArgs('submit', { 'expect-sha256': P1_SHA, 'approval-file': '/a.json', label: 'Send ' }).ok, false);
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir);
    const sendState = () => {
      const s = baseState({ controls: [{ frame_id: 'main', label: 'Send', disabled: false }, { frame_id: 'main', label: 'Attach', disabled: false }] });
      Object.assign(s.composer, { value: P1, submit_controls: [], submit_by_label: { Submit: [], Send: [{ disabled: false, in_region: true }], 'Chat now': [] } });
      return s;
    };
    const asSubmit = fakeRuntime(dir, { state: sendState() });
    assert.equal((await executeCommand(asSubmit.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }))).reason, 'control_not_found', 'the default label is Submit');
    const unscoped = sendState(); unscoped.composer.submit_by_label = null;
    const blind = fakeRuntime(dir, { state: unscoped });
    assert.equal((await executeCommand(blind.rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval, label: 'Send' }))).reason, 'submit_scope_unknown');
    assert.ok(!asSubmit.events.includes('dispatch') && !blind.events.includes('dispatch'));
    const send = fakeRuntime(dir, { state: sendState(), onDispatch: label => { if (label === 'Send') { send.sent.push(send.current.composer.value); send.current.composer.value = ''; } } });
    const sent = await executeCommand(send.rt, command('003', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval, label: 'Send' }));
    assert.equal(sent.status, 'sent'); assert.equal(sent.submit_label, 'Send');
    assert.ok(send.events.includes('prepare:Send') && send.events.includes('composer-scope'));
    const log = await readLog(dir);
    assert.deepEqual(log.map(x => [x.phase, x.command, x.submit_label ?? null]), [['attempt', 'submit', 'Send'], ['result', 'submit', null]]);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('page: Send and Chat now are scoped to the composer region; Attach anchors it', () => {
  const footer = el('div', {}, [el('textarea', { placeholder: 'Write here and press Enter', value: P3 }), el('button', {}, [], 'Attach'), el('button', {}, [], 'Send')]);
  const body = el('body', {}, [el('main', {}, [el('div', {}, [el('button', {}, [], 'End chat')]), footer])]);
  const scan = runPage(body, 'scan');
  assert.deepEqual(scan.region.submit_by_label.Send, [{ disabled: false, in_region: true }]);
  assert.deepEqual(scan.region.submit_by_label.Submit, []);
  assert.equal(runPage(body, 'control', { label: 'Send', composerSubmit: true, expectedComposerText: P3 }).text, 'Send');
  assert.equal(pageCode(() => runPage(body, 'control', { label: 'Reply', composerSubmit: true })), 'composer_submit_label');
  // The reply form: "Your name" input with its label, the message, Chat now.
  const form = (extraName = false) => el('body', {}, [el('div', { class: 'reply-form' }, [
    el('div', { 'data-test-tag': 'input-name' }, [el('label', { for: 'input-2' }, [], 'Your name'), el('input', { id: 'input-2', type: 'text', value: 'Thermoslim LLC' })]),
    ...(extraName ? [el('input', { type: 'text', 'aria-label': 'Your name', value: '' })] : []),
    el('textarea', {}), el('button', {}, [], 'Cancel'), el('button', {}, [], 'Chat now')])]);
  const reply = runPage(form(), 'scan');
  assert.deepEqual(reply.name_field, { count: 1, value: 'Thermoslim LLC', disabled: false });
  assert.deepEqual(reply.region.submit_by_label['Chat now'], [{ disabled: false, in_region: true }]);
  assert.equal(runPage(form(), 'name-input').getAttribute('id'), 'input-2');
  assert.equal(pageCode(() => runPage(form(true), 'name-input')), 'name_field_count', 'two name fields fail closed');
  const search = el('body', {}, [el('input', { type: 'search', 'aria-label': 'Search' }), el('input', { type: 'text', placeholder: 'Search for anything' })]);
  assert.equal(runPage(search, 'scan').name_field.count, 0, 'search inputs are not the name field');
});

test('Chat now fills the name and opening line, then adopts exactly the case chat window', async () => {
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir, { plan_item: 'P3', sha256: P3_SHA });
    const run = chatRuntime(dir);
    const result = await executeCommand(run.rt, command('001', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Chat now' }));
    assert.equal(result.status, 'sent'); assert.equal(result.submit_label, 'Chat now');
    assert.deepEqual(result.chat, { target_id: 'chat-1', url: CHAT_URL, slot: SA.CHAT_SLOT });
    assert.equal(run.rt.lockout, null, 'the expected window does not halt the run');
    assert.equal(run.rt.browser, run.chat.rt.browser, 'later commands drive the chat window');
    const order = ['fill-name', 'insert', 'prepare:Chat now', 'dispatch', 'adopt:chat-1'].map(e => run.events.indexOf(e));
    assert.ok(order.every((v, i) => v >= 0 && (i === 0 || v > order[i - 1])), `order: ${run.events.join(',')}`);
    assert.equal(run.current.name_field.value, 'Victor'); assert.equal(run.current.composer.value, SA.CHAT_OPENING_LINE);
    let log = await readLog(dir);
    assert.deepEqual(log.map(x => [x.phase, x.command, x.status ?? null]), [['attempt', 'chat_now', null], ['result', 'chat_now', 'sent']]);
    assert.equal(log[0].label, 'routine'); assert.equal(log[0].name, 'Victor'); assert.equal(log[0].opening_line_sha256, sha256(SA.CHAT_OPENING_LINE));
    // The approved message then goes out through the chat window's Send.
    run.chat.current.composer.value = P3;
    const sent = await executeCommand(run.rt, command('002', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Send' }));
    assert.equal(sent.status, 'sent');
    assert.deepEqual(run.chat.sent, [P3]);
    assert.ok(run.chat.events.includes('prepare:Send'));
    log = await readLog(dir);
    assert.deepEqual(log.filter(x => x.phase === 'attempt' && x.command === 'submit').map(x => x.sha256), [P3_SHA], 'the receipt sees one submit: the message');
    assert.equal((await executeCommand(run.rt, command('003', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Chat now' }))).reason, 'send_limit_reached');
    assert.equal((await executeCommand(run.rt, command('004', 'open', { case: CASE_ID }))).reason, 'case_chat_open');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('Chat now: any other new window still halts the run and nothing is adopted', async () => {
  const other = `${SC}/hill/website/chat?formType=reply&caseID=99999999`;
  const cases = [
    ['chat_case_mismatch', [{ targetId: 'chat-1', type: 'page', url: other, openerId: 'task' }]],
    ['chat_opener_mismatch', [{ targetId: 'chat-1', type: 'page', url: CHAT_URL, openerId: null }]],
    ['chat_form_type_mismatch', [{ targetId: 'chat-1', type: 'page', url: CHAT_URL.replace('formType=reply', 'formType=create'), openerId: 'task' }]],
    ['chat_origin_mismatch', [{ targetId: 'chat-1', type: 'page', url: CHAT_URL.replace(SC, 'https://evil.example'), openerId: 'task' }]],
    ['multiple_new_targets', [{ targetId: 'chat-1', type: 'page', url: CHAT_URL, openerId: 'task' }, { targetId: 'ad-1', type: 'page', url: 'https://ads.example/', openerId: 'task' }]],
  ];
  for (const [reason, popups] of cases) {
    const dir = await runDir();
    try {
      const approval = await approvalFile(dir, { plan_item: 'P3', sha256: P3_SHA });
      const run = chatRuntime(dir, { popups });
      const result = await executeCommand(run.rt, command('001', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Chat now' }));
      assert.equal(result.status, 'uncertain', reason); assert.equal(result.reason, reason);
      assert.equal(run.rt.lockout.reason, 'new_target'); assert.equal(result.lockout.check, reason);
      assert.ok(!run.events.some(e => e.startsWith('adopt:')), `${reason}: nothing adopted`);
      assert.notEqual(run.rt.browser, run.chat.rt.browser);
      const log = await readLog(dir);
      assert.deepEqual(log.map(x => [x.phase, x.status ?? null]), [['attempt', null], ['result', 'uncertain']]);
    } finally { await rm(dir, { recursive: true, force: true }); }
  }
  const dir = await runDir();
  try {
    const run = chatRuntime(dir, { popups: [] });
    const result = await executeCommand(run.rt, command('001', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': await approvalFile(dir, { plan_item: 'P3', sha256: P3_SHA }), label: 'Chat now' }));
    assert.equal(result.reason, 'chat_window_missing'); assert.equal(run.rt.lockout.reason, 'chat_window_missing');
    assert.deepEqual(SA.isCaseChatTarget({ type: 'page', url: CHAT_URL, openerId: 'task' }, { origin: SC, caseId: CASE_ID, openerId: 'task' }), { ok: true });
    assert.equal(SA.isCaseChatTarget({ type: 'page', url: `${SC}/assistant?caseID=${CASE_ID}&formType=reply`, openerId: 'task' }, { origin: SC, caseId: CASE_ID, openerId: 'task' }).reason, 'chat_path_mismatch');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('Chat now refuses before any click without a signature name, an opened case or a clean form', async () => {
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir, { plan_item: 'P3', sha256: P3_SHA });
    const args = { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Chat now' };
    const noName = chatRuntime(dir, { config: { signature_name: undefined } });
    assert.equal((await executeCommand(noName.rt, command('001', 'submit', args))).reason, 'signature_name_missing');
    const noCase = chatRuntime(dir); noCase.rt.caseId = null;
    assert.equal((await executeCommand(noCase.rt, command('002', 'submit', args))).reason, 'case_not_opened');
    const drafted = chatRuntime(dir); drafted.current.composer.value = 'Something else';
    assert.equal((await executeCommand(drafted.rt, command('003', 'submit', args))).reason, 'composer_not_empty');
    const twoNames = chatRuntime(dir); twoNames.current.name_field = { count: 2, value: null, disabled: null };
    assert.equal((await executeCommand(twoNames.rt, command('004', 'submit', args))).reason, 'name_field_count');
    const files = chatRuntime(dir);
    assert.equal((await executeCommand(files.rt, command('005', 'submit', { ...args, 'expect-attachment': ['a.pdf'] }))).reason, 'chat_now_takes_no_attachment');
    // Without registry_id neither Chat now nor a Send on the case page can skip the claim.
    const unbound = chatRuntime(dir, { config: { registry_id: undefined } });
    assert.equal((await executeCommand(unbound.rt, command('006', 'submit', args))).reason, 'registry_binding_required');
    unbound.current.composer.value = P3;
    assert.equal((await executeCommand(unbound.rt, command('007', 'submit', { ...args, label: 'Send' }))).reason, 'registry_binding_required');
    for (const r of [noName, noCase, drafted, twoNames, files, unbound]) assert.ok(!r.events.includes('dispatch'));
    assert.deepEqual(await readLog(dir), []);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('every text approval needs a label, and the label is logged with the attempt', async () => {
  const good = { schema_version: 1, plan_item: 'P3', sha256: P3_SHA, approved_at: '2026-09-29T11:59:00Z', approval_text: 'Go.', run_id: RUN_ID, seller_id: SELLER, label: 'appeal' };
  const ctx = { runId: RUN_ID, sellerId: SELLER, now: T0 };
  assert.equal(validateApproval(good, P3_SHA, undefined, ctx).ok, true);
  const { label, ...unlabelled } = good;
  for (const item of ['P1', 'P2', 'P3', 'followup']) assert.equal(validateApproval({ ...unlabelled, plan_item: item }, P3_SHA, undefined, ctx).reason, 'approval_label_missing', item);
  assert.equal(validateApproval({ ...good, label: 'urgent' }, P3_SHA, undefined, ctx).reason, 'approval_label_invalid');
  assert.equal(validateApproval({ ...good, label: 'Routine' }, P3_SHA, undefined, ctx).reason, 'approval_label_invalid');
  for (const value of SA.APPROVAL_LABELS) assert.equal(validateApproval({ ...good, label: value }, P3_SHA, undefined, ctx).ok, true, value);
  assert.equal(validateApproval({ ...unlabelled, plan_item: 'approve' }, P3_SHA, undefined, ctx).ok, true, 'terms and file approvals carry no label');
  assert.equal(validateApproval({ ...unlabelled, plan_item: 'attachment' }, P3_SHA, undefined, ctx).ok, true);
  const dir = await runDir();
  try {
    const { rt, events, current } = fakeRuntime(dir); current.composer.value = P1;
    const missing = await approvalFile(dir, { label: undefined }, 'unlabelled.json');
    assert.equal((await executeCommand(rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': missing }))).reason, 'approval_label_missing');
    assert.ok(!events.includes('dispatch')); assert.deepEqual(await readLog(dir), []);
    const appeal = await approvalFile(dir, { label: 'appeal' }, 'appeal.json');
    assert.equal((await executeCommand(rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': appeal }))).status, 'sent');
    const log = await readLog(dir);
    assert.equal(log[0].label, 'appeal'); assert.equal(log[0].approval.label, 'appeal');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a registered case: claim-attended runs before each outbound action and a refusal stops it with no attempt line', async () => {
  const config = { schema_version: 1, run_id: RUN_ID, account: { seller_id: SELLER, marketplace_id: 'ATVPDKIKX0DER' }, registry_id: 'b8b31850', baseline: { last_sent_at: '2026-09-30T14:02:11+00:00' }, authorization: ATTENDED };
  const dir = await runDir();
  try {
    const requests = [];
    const refuse = async request => { requests.push(request); return { ok: false, reason: 'daily_sent', message: 'Grimoire already sent on this case today' }; };
    const s = fakeRuntime(dir); s.current.composer.value = P1; Object.assign(s.rt, { config }); s.rt.deps.claimAttended = refuse;
    const refused = await executeCommand(s.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(refused.status, 'refused'); assert.equal(refused.reason, 'claim_refused'); assert.equal(refused.claim_reason, 'daily_sent'); assert.equal(refused.stage, 'pre_click');
    assert.ok(!s.events.includes('dispatch'));
    assert.deepEqual(requests[0], { registry_id: 'b8b31850', run_id: RUN_ID, account: { seller_id: SELLER, marketplace_id: 'ATVPDKIKX0DER' }, case_id: null, baseline: { last_sent_at: '2026-09-30T14:02:11+00:00' }, authorization: ATTENDED });
    // Approve and attach stop the same way.
    const terms = 'Connect with an associate\nApprove';
    const a = fakeRuntime(dir, { state: baseState({ controls: [...baseState().controls, { frame_id: 'main', label: 'Approve', disabled: false }], handoff: { approve_count: 1, terms_text: terms } }) });
    Object.assign(a.rt, { config }); a.rt.deps.claimAttended = refuse;
    assert.equal((await executeCommand(a.rt, command('002', 'approve', { 'expect-terms-sha256': termsHash(terms), 'approval-file': await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(terms) }, 'ap.json') }))).reason, 'claim_refused');
    const file = join(dir, 'invoice.pdf'); await writeFile(file, 'pdf bytes');
    const f = fakeRuntime(dir); Object.assign(f.rt, { config }); f.rt.deps.claimAttended = refuse;
    assert.equal((await executeCommand(f.rt, command('003', 'attach', { file, sha256: sha256('pdf bytes'), 'approval-file': await approvalFile(dir, { plan_item: 'attachment', sha256: sha256('pdf bytes') }, 'at.json') }))).reason, 'claim_refused');
    assert.ok(!a.events.includes('dispatch') && !f.events.includes('set-file'));
    // Chat now as well, before its click.
    const chat = chatRuntime(dir, { claim: refuse, config });
    assert.equal((await executeCommand(chat.rt, command('004', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': await approvalFile(dir, { plan_item: 'P3', sha256: P3_SHA }, 'p3.json'), label: 'Chat now' }))).reason, 'claim_refused');
    assert.ok(!chat.events.includes('dispatch'));
    assert.deepEqual(await readLog(dir), [], 'no attempt line from any refused claim');
    // A thrown claim is a refusal too.
    const t = fakeRuntime(dir); t.current.composer.value = P1; Object.assign(t.rt, { config }); t.rt.deps.claimAttended = async () => { throw new Error('python3 missing'); };
    const thrown = await executeCommand(t.rt, command('005', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }));
    assert.equal(thrown.claim_reason, 'claim_unavailable'); assert.ok(!t.events.includes('dispatch'));
    // The approval sentence must be the authorization's, or the send could not be recorded.
    const other = fakeRuntime(dir); other.current.composer.value = P1; Object.assign(other.rt, { config }); other.rt.deps.claimAttended = async () => ({ ok: true });
    assert.equal((await executeCommand(other.rt, command('006', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir, { approval_text: 'yes' }, 'yes.json') }))).reason, 'approval_instruction_mismatch');
    // A claim that passes lets the click go ahead, once per outbound action.
    let claims = 0;
    const ok = fakeRuntime(dir); ok.current.composer.value = P1; Object.assign(ok.rt, { config }); ok.rt.deps.claimAttended = async () => { claims++; ok.events.push('claim'); return { ok: true, status: 'claimed' }; };
    assert.equal((await executeCommand(ok.rt, command('007', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': await approvalFile(dir) }))).status, 'sent');
    assert.equal(claims, 1); assert.ok(ok.events.indexOf('claim') < ok.events.indexOf('dispatch'));
    assert.deepEqual((await readLog(dir)).map(x => x.phase), ['attempt', 'result']);
    // Without registry_id (a case not registered yet) no claim is made.
    const fresh = fakeRuntime(dir); fresh.current.composer.value = 'Please connect me with a Seller Support associate.';
    fresh.rt.deps.claimAttended = async () => { throw new Error('must not be called'); };
    const p2 = sha256(fresh.current.composer.value);
    assert.equal((await executeCommand(fresh.rt, command('008', 'submit', { 'expect-sha256': p2, 'approval-file': await approvalFile(dir, { plan_item: 'P2', sha256: p2 }, 'p2.json') }))).status, 'sent');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a text approved later in the chat carries its own authorization, and the claim before its click uses it', async () => {
  const later = { kind: 'attended', requester_id: 'U01', source: { session_id: 'session-1', request_id: 'followup-1', instruction: 'Yes, send the order ID' } };
  const ctx = { runId: RUN_ID, sellerId: SELLER, now: T0, instruction: ATTENDED.source.instruction };
  const good = { schema_version: 1, plan_item: 'followup', sha256: P1_SHA, approved_at: '2026-09-29T11:59:00Z', approval_text: later.source.instruction, run_id: RUN_ID, seller_id: SELLER, label: 'admission' };
  assert.equal(validateApproval(good, P1_SHA, undefined, ctx).reason, 'approval_instruction_mismatch');
  assert.equal(validateApproval({ ...good, authorization: later }, P1_SHA, undefined, ctx).ok, true);
  assert.equal(validateApproval({ ...good, authorization: { ...later, kind: 'slack' } }, P1_SHA, undefined, ctx).reason, 'approval_authorization_invalid');
  assert.equal(validateApproval({ ...good, authorization: { ...later, source: { ...later.source, instruction: 'Send it' } } }, P1_SHA, undefined, ctx).reason, 'approval_authorization_invalid');
  assert.equal(validateApproval({ ...good, authorization: { ...later, source: { instruction: later.source.instruction } } }, P1_SHA, undefined, ctx).reason, 'approval_authorization_invalid', 'the session is required');
  const dir = await runDir();
  try {
    const requests = [];
    const run = fakeRuntime(dir); run.current.composer.value = P1;
    Object.assign(run.rt.config, BOUND);
    run.rt.deps.claimAttended = async request => { requests.push(request); return { ok: true, status: 'claimed' }; };
    const file = await approvalFile(dir, { plan_item: 'followup', approval_text: later.source.instruction, label: 'admission', authorization: later }, 'followup.json');
    assert.equal((await executeCommand(run.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': file }))).status, 'sent');
    assert.deepEqual(requests.map(r => r.authorization), [later]);
    assert.deepEqual((await readLog(dir))[0].approval.authorization, later, 'the receipt finds it with the attempt');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('the claim before Chat now names the opened case and the chat name for the service to check', async () => {
  const dir = await runDir();
  try {
    const requests = [];
    const run = chatRuntime(dir, { claim: async request => { requests.push(request); return { ok: true, status: 'claimed' }; } });
    const result = await executeCommand(run.rt, command('001', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': await approvalFile(dir, { plan_item: 'P3', sha256: P3_SHA }), label: 'Chat now' }));
    assert.equal(result.status, 'sent');
    assert.deepEqual([requests[0].case_id, requests[0].signature_name, requests[0].authorization], [CASE_ID, 'Victor', ATTENDED]);
    assert.equal('signature_name' in SA.claimRequest({ run_id: 'r', registry_id: 'x', account: { seller_id: 'S', marketplace_id: 'M' }, baseline: {}, authorization: ATTENDED }), false, 'no name without the chat form');
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('claim-attended runs the case service and only exit 0 with claimed passes', async () => {
  const calls = [];
  const exec = answer => (cmd, args, options, done) => { calls.push([cmd, args, options.timeout]); answer(done); };
  const ok = await SA.runClaimAttended('/tmp/run/claim-attended.json', exec(done => done(null, '{"authorization_revision":7,"operation_id":"attended-3f1c","status":"claimed"}\n')));
  assert.equal(ok.ok, true); assert.equal(ok.operation_id, 'attended-3f1c');
  assert.equal(calls[0][0], 'python3');
  assert.match(calls[0][1][0], /tools\/amazon-operations\/case_service\.py$/);
  assert.deepEqual(calls[0][1].slice(1), ['claim-attended', '--request', '/tmp/run/claim-attended.json']);
  assert.equal(calls[0][2], 30000);
  const blocked = await SA.runClaimAttended('/x.json', exec(done => done(Object.assign(new Error('exit 2'), { code: 2 }), '{"message":"A message was sent after this draft","reason":"baseline_changed","status":"blocked"}\n')));
  assert.deepEqual([blocked.ok, blocked.reason], [false, 'baseline_changed']);
  const missing = await SA.runClaimAttended('/x.json', exec(done => done(Object.assign(new Error('spawn python3 ENOENT'), { code: 'ENOENT' }), '')));
  assert.deepEqual([missing.ok, missing.reason], [false, 'claim_unavailable']);
  const odd = await SA.runClaimAttended('/x.json', exec(done => done(null, '{"status":"blocked","reason":"run_recorded"}')));
  assert.deepEqual([odd.ok, odd.reason], [false, 'run_recorded'], 'exit 0 without claimed is still a refusal');
});

test('run.json keeps the case binding and the signature name, strictly', () => {
  const account = { profile_key: 'acme-us', client_slug: 'acme', marketplace: 'US', seller_id: 'S', marketplace_id: 'M', seller_central_name: 'Acme', marketplace_label: 'United States', parent_account_name: 'Acme' };
  const base = { schema_version: 1, run_id: 'r1', account };
  const bound = validateRunConfig({ ...base, registry_id: 'b8b3', baseline: { last_sent_at: null }, authorization: ATTENDED, signature_name: 'Victor Uhl' });
  assert.deepEqual([bound.registry_id, bound.baseline, bound.authorization, bound.signature_name], ['b8b3', { last_sent_at: null }, ATTENDED, 'Victor Uhl']);
  assert.equal(validateRunConfig({ ...base, registry_id: 'b8b3', baseline: { last_sent_at: '2026-10-01T14:40:22.371000+00:00' }, authorization: ATTENDED }).baseline.last_sent_at, '2026-10-01T14:40:22.371000+00:00');
  assert.equal(validateRunConfig(base).registry_id, undefined);
  assert.throws(() => validateRunConfig({ ...base, registry_id: 'b8b3', authorization: ATTENDED }), /baseline/);
  assert.throws(() => validateRunConfig({ ...base, registry_id: 'b8b3', baseline: { last_sent_at: 'yesterday' }, authorization: ATTENDED }), /baseline/);
  assert.throws(() => validateRunConfig({ ...base, registry_id: 'b8b3', baseline: { last_sent_at: null } }), /authorization/);
  assert.throws(() => validateRunConfig({ ...base, registry_id: 'b8b3', baseline: { last_sent_at: null }, authorization: { ...ATTENDED, kind: 'slack' } }), /authorization/);
  assert.throws(() => validateRunConfig({ ...base, registry_id: '' }), /registry_id/);
  assert.throws(() => validateRunConfig({ ...base, signature_name: 'Victor\nUhl' }), /signature_name/);
  assert.throws(() => validateRunConfig({ ...base, signature_name: 'x'.repeat(101) }), /signature_name/);
});

test('the chat window is bound as a named slot of the run task and released by outcome', async () => {
  const calls = [];
  let guard = null, closed = false;
  const registry = {
    reserveTaskTab: async spec => { calls.push(['reserve', spec.taskId, spec.slot, spec.workflow]); return { kind: 'create', controlToken: 'ctl', reservationToken: 'res' }; },
    bindReservedTaskTab: async spec => { calls.push(['bind', spec.slot, spec.targetId, spec.reservationToken, spec.controlToken]); },
    assertTaskTabControl: async spec => { calls.push(['assert', spec.slot, spec.targetId, spec.controlToken]); return {}; },
    touchTaskTabControl: async () => ({}),
    releaseTaskTabControl: async spec => { calls.push(['release', spec.slot, spec.outcome]); return {}; },
    abandonTaskTabReservation: async spec => { calls.push(['abandon', spec.slot]); },
  };
  const session = { setTaskControlGuard: (fn, options) => { guard = fn; calls.push(['guard', options.initialUrl]); }, assertTaskControl: async () => guard(), close: () => { closed = true; }, invalidateTaskControl: () => {} };
  const cdp = { listPages: async () => [{ id: 'chat-1', url: CHAT_URL, webSocketDebuggerUrl: 'ws://127.0.0.1:9222/devtools/page/chat-1' }], Session: { open: async url => { calls.push(['open', url]); return session; } } };
  const policy = { cleanup: { heartbeat_interval_ms: 60000 } };
  const spec = { registry, cdp, policy, port: 9222, taskId: 'amazon-communications:abc', owner: 'seller-assistant:1', origin: SC, target: { targetId: 'chat-1', url: CHAT_URL } };
  const chat = await SA.adoptChatTarget(spec);
  assert.deepEqual(calls.slice(0, 5), [['reserve', 'amazon-communications:abc', 'case-chat', 'amazon-communications'], ['bind', 'case-chat', 'chat-1', 'res', 'ctl'],
    ['open', 'ws://127.0.0.1:9222/devtools/page/chat-1'], ['guard', CHAT_URL], ['assert', 'case-chat', 'chat-1', 'ctl']]);
  assert.equal(chat.session, session); assert.equal(chat.slot, 'case-chat');
  await chat.release('handoff'); await chat.release('error');
  assert.deepEqual(calls.filter(c => c[0] === 'release'), [['release', 'case-chat', 'handoff']], 'released once');
  assert.equal(closed, true);
  calls.length = 0;
  const busy = { ...registry, reserveTaskTab: async () => ({ kind: 'busy', reason: 'task-tab-reservation-busy', controlToken: null }) };
  await assert.rejects(SA.adoptChatTarget({ ...spec, registry: busy }), error => error.code === 'chat_slot_unavailable');
  const gone = { ...cdp, listPages: async () => [] };
  await assert.rejects(SA.adoptChatTarget({ ...spec, cdp: gone }), error => error.code === 'chat_target_unavailable');
  assert.deepEqual(calls.filter(c => c[0] === 'release'), [['release', 'case-chat', 'error']], 'a bound slot that cannot be driven is released as error');
});

// ------------------------------------------------- third review regressions

test('page: Submit is not returned once the composer text differs from the approved text', () => {
  const chat = value => {
    const own = el('button', {}, [], 'Submit');
    const footer = el('div', {}, [el('textarea', { placeholder: 'Message Seller Assistant...', value }), own, el('button', {}, [], 'Upload file')]);
    return { body: el('body', {}, [el('main', {}, [footer])]), own };
  };
  const lookup = (value, extra = { expectedComposerText: P1 }) => runPage(chat(value).body, 'control', { label: 'Submit', composerSubmit: true, ...extra });
  assert.equal(pageCode(() => lookup(`${P1} Also please refund us.`)), 'composer_changed');
  assert.equal(pageCode(() => lookup('')), 'composer_changed');
  assert.equal(pageCode(() => lookup(P1, {})), 'composer_changed', 'no expected text fails closed');
  // Same normalization as the hash check: CRLF, outer newlines and no-break spaces.
  const ok = chat(`\r\n${P1.replace('ASIN B0TEST0001', 'ASIN B0TEST0001')}\r\n`);
  assert.equal(runPage(ok.body, 'control', { label: 'Submit', composerSubmit: true, expectedComposerText: P1 }), ok.own);
});

test('submit binds the Submit lookup to the approved text and clicks nothing when the page says it changed', async () => {
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir);
    const ok = fakeRuntime(dir); ok.current.composer.value = P1;
    assert.equal((await executeCommand(ok.rt, command('001', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }))).status, 'sent');
    assert.ok(ok.events.includes(`composer-text:${P1_SHA}`), 'the page lookup gets the approved text');
    await rm(join(dir, 'approvals.jsonl'));
    const changed = fakeRuntime(dir, { prepareError: Object.assign(new Error('composer_changed'), { code: 'composer_changed' }) });
    changed.current.composer.value = P1;
    const result = await executeCommand(changed.rt, command('002', 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }));
    assert.equal(result.status, 'blocked'); assert.equal(result.reason, 'composer_changed'); assert.equal(result.clicked, false);
    assert.ok(!changed.events.includes('dispatch'));
    assert.ok(!existsSync(join(dir, 'approvals.jsonl')) || !readFileSync(join(dir, 'approvals.jsonl'), 'utf8').includes('"phase":"attempt"'), 'no attempt line');
    assert.equal(changed.rt.counts.get(`submit:${P1_SHA}`) ?? 0, 0);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('the Submit click expression carries the approved text and the composer normalization', async () => {
  const expressions = [];
  const send = async (method, params) => {
    if (method === 'Page.createIsolatedWorld') return { executionContextId: 5 };
    if (method === 'Runtime.evaluate') { expressions.push(params.expression); return { result: { objectId: 'button-1' } }; }
    if (method === 'DOM.getContentQuads') return { quads: [[0, 0, 20, 0, 20, 10, 0, 10]] };
    if (method === 'DOM.getNodeForLocation') return { backendNodeId: 7 };
    if (method === 'DOM.resolveNode') return { object: { objectId: 'button-inner' } };
    if (method === 'Runtime.callFunctionOn') return { result: { value: true } };
    return {};
  };
  await makeBrowser({ send }, SC).prepareClick('m', 'Submit', { composerSubmit: true, expectedComposerText: P1 });
  assert.ok(expressions[0].includes(JSON.stringify(P1)));
  assert.match(expressions[0], /const normalizeComposer = /);
});

test('a P2 approval of any other text is sent once', async () => {
  const dir = await runDir();
  try {
    assert.equal(SA.P2_TEXT, 'Please connect me with a Seller Support associate.');
    const approval = await approvalFile(dir, { plan_item: 'P2', sha256: P1_SHA });
    const { rt, current } = fakeRuntime(dir);
    const statuses = [];
    for (const id of ['001', '002']) { current.composer.value = P1; statuses.push(await executeCommand(rt, command(id, 'submit', { 'expect-sha256': P1_SHA, 'approval-file': approval }))); }
    assert.deepEqual(statuses.map(r => r.status), ['sent', 'refused']);
    assert.equal(statuses[1].reason, 'send_limit_reached'); assert.equal(statuses[1].limit, 1);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

// Two email Issue summaries: the assistant re-issued the summary after Request
// changes. Each card holds its fields, then an inner action card with Approve.
function twoSummaries({ secondChanges = true } = {}) {
  const card = (subject, changes) => {
    const approve = el('button', {}, [], 'Approve');
    const change = changes ? el('button', {}, [], 'Request changes') : null;
    const node = el('div', { class: 'summary-card' }, [
      el('h3', {}, [], 'Issue summary'), el('p', {}, [], `Subject: ${subject}`), el('p', {}, [], 'Attachments'), el('p', {}, [], 'None'),
      el('div', { class: 'actions-card' }, [el('span', {}, [], 'Option valid for 1 hour'), approve, ...(change ? [change] : [])]),
    ]);
    return { node, approve, change };
  };
  const first = card('First wording', true), second = card('Exact subject', secondChanges);
  const footer = el('div', {}, [el('textarea', { placeholder: 'Select an option above to proceed.' }), el('button', {}, [], 'Upload file')]);
  return { body: el('body', {}, [el('main', {}, [first.node, second.node, footer])]), first, second };
}

test('page: with two Issue summaries the terms and both controls come from the last one', () => {
  const page = twoSummaries();
  const terms = runPage(page.body, 'terms');
  assert.equal(terms.basis, 'card');
  assert.match(terms.text, /Subject: Exact subject/); assert.doesNotMatch(terms.text, /First wording/);
  assert.match(terms.text, /Issue summary/); assert.match(terms.text, /Attachments/);
  assert.equal(runPage(page.body, 'control', { label: 'Approve', expectedTermsText: terms.text }), page.second.approve);
  assert.equal(runPage(page.body, 'control', { label: 'Request changes', expectedTermsText: terms.text }), page.second.change);
  const firstText = terms.text.replace('Exact subject', 'First wording');
  assert.equal(pageCode(() => runPage(page.body, 'control', { label: 'Approve', expectedTermsText: firstText })), 'terms_changed');
  assert.equal(pageCode(() => runPage(page.body, 'control', { label: 'Request changes', expectedTermsText: firstText })), 'terms_changed');
  const uneven = twoSummaries({ secondChanges: false });
  const unevenTerms = runPage(uneven.body, 'terms').text;
  assert.equal(pageCode(() => runPage(uneven.body, 'control', { label: 'Request changes', expectedTermsText: unevenTerms })), 'request_changes_count');
  // Without the summary fields no card qualifies once there are two Approves.
  const bare = el('body', {}, [el('main', {}, [
    el('div', { class: 'actions-card' }, [el('span', {}, [], 'Pick one'), el('button', {}, [], 'Approve')]),
    el('div', { class: 'actions-card' }, [el('span', {}, [], 'Pick one'), el('button', {}, [], 'Approve')]),
    el('div', {}, [el('textarea', {}), el('button', {}, [], 'Upload file')]),
  ])]);
  assert.equal(pageCode(() => runPage(bare, 'terms')), 'terms_container_not_found');
});

test('page: staged upload cards count as chips until an upload refusal empties the list', () => {
  const page = ({ placeholder = 'Click send to upload', refused = false, regionChip = null, regionError = false } = {}) => {
    const staged = el('div', { class: 'upload-card' }, [el('span', { class: 'file-name' }, [], 'invoice.pdf'), ...(refused ? [el('span', {}, [], 'Unsupported file was attached')] : [])]);
    const footer = el('div', {}, [
      ...(regionChip ? [el('span', {}, [], regionChip)] : []), ...(regionError ? [el('span', {}, [], 'Upload failed')] : []),
      el('textarea', { placeholder }), el('button', {}, [], 'Submit'), el('button', {}, [], 'Upload file'),
    ]);
    return el('body', {}, [el('main', {}, [staged, footer])]);
  };
  assert.deepEqual(runPage(page(), 'scan').region.chips, ['invoice.pdf']);
  assert.deepEqual(runPage(page({ placeholder: 'Message Seller Assistant...' }), 'scan').region.chips, [], 'staged cards count only while the composer says click send to upload');
  assert.deepEqual(runPage(page({ refused: true }), 'scan').region.chips, [], 'a refused staged card is not a chip');
  assert.deepEqual(runPage(page({ placeholder: 'Message Seller Assistant...', regionChip: 'report.csv' }), 'scan').region.chips, ['report.csv']);
  assert.deepEqual(runPage(page({ regionChip: 'report.csv', regionError: true }), 'scan').region.chips, [], 'an upload error empties every chip');
});

test('approve and Request changes with two summaries are bound to the last summary\'s terms', async () => {
  const dir = await runDir();
  try {
    const first = 'Issue summary Subject: First wording Attachments None Approve Request changes';
    const second = 'Issue summary Subject: Exact subject Attachments None Approve Request changes';
    const state = (handoff = {}) => baseState({
      controls: [...baseState().controls, ...['Approve', 'Request changes', 'Approve', 'Request changes'].map(label => ({ frame_id: 'main', label, disabled: false }))],
      handoff: { approve_count: 2, frame_id: 'main', terms_text: second, terms_sha256: termsHash(second), ...handoff },
    });
    const stale = fakeRuntime(dir, { state: state() });
    const staleApproval = await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(first) }, 'first.json');
    const r1 = await executeCommand(stale.rt, command('001', 'approve', { 'expect-terms-sha256': termsHash(first), 'approval-file': staleApproval }));
    assert.equal(r1.status, 'blocked'); assert.equal(r1.reason, 'control_summary_not_verified');
    assert.ok(!stale.events.includes('dispatch') && !stale.events.some(e => e.startsWith('prepare:')));
    const ok = fakeRuntime(dir, { state: state() });
    const approval = await approvalFile(dir, { plan_item: 'approve', sha256: termsHash(second) }, 'second.json');
    const r2 = await executeCommand(ok.rt, command('002', 'approve', { 'expect-terms-sha256': termsHash(second), 'approval-file': approval }));
    assert.equal(r2.status, 'approved');
    assert.ok(ok.events.includes(`terms-text:${termsHash(second)}`), 'the page lookup re-reads the approved terms');
    const nav = fakeRuntime(dir, { state: state() });
    assert.equal((await executeCommand(nav.rt, command('003', 'navigate', { label: 'Request changes' }))).status, 'ok');
    assert.ok(nav.events.includes('prepare:Request changes') && nav.events.includes(`terms-text:${termsHash(second)}`));
    const unread = fakeRuntime(dir, { state: state({ terms_text: null, terms_sha256: null, terms_error: 'terms_container_not_found' }) });
    const r4 = await executeCommand(unread.rt, command('004', 'navigate', { label: 'Request changes' }));
    assert.equal(r4.status, 'blocked'); assert.equal(r4.reason, 'control_summary_not_verified');
    assert.ok(!unread.events.includes('dispatch'));
  } finally { await rm(dir, { recursive: true, force: true }); }
});

// ------------------------------- merge of the PR #76 fixes into attended replies

// PR #76 review finding F1 on PR 1's labels: Send and Chat now are looked up
// with the same click-time composer re-check as Submit.
test('page: the Send and Chat now lookups re-check the composer text like Submit', () => {
  const window = value => {
    const send = el('button', {}, [], 'Send');
    const footer = el('div', {}, [el('textarea', { placeholder: 'Write here and press Enter', value }), el('button', {}, [], 'Attach'), send]);
    return { body: el('body', {}, [el('main', {}, [el('div', {}, [el('button', {}, [], 'End chat')]), footer])]), send };
  };
  const chat = window(`${P3}\r\n`);
  assert.equal(runPage(chat.body, 'control', { label: 'Send', composerSubmit: true, expectedComposerText: P3 }), chat.send);
  assert.equal(pageCode(() => runPage(window(`${P3} Also please refund us.`).body, 'control', { label: 'Send', composerSubmit: true, expectedComposerText: P3 })), 'composer_changed');
  assert.equal(pageCode(() => runPage(chat.body, 'control', { label: 'Send', composerSubmit: true })), 'composer_changed', 'no expected text fails closed');
  const form = value => {
    const chatNow = el('button', {}, [], 'Chat now');
    const body = el('body', {}, [el('div', { class: 'reply-form' }, [
      el('div', { 'data-test-tag': 'input-name' }, [el('label', { for: 'input-2' }, [], 'Your name'), el('input', { id: 'input-2', type: 'text', value: 'Victor' })]),
      el('textarea', { value }), el('button', {}, [], 'Cancel'), chatNow])]);
    return { body, chatNow };
  };
  const reply = form(SA.CHAT_OPENING_LINE);
  assert.equal(runPage(reply.body, 'control', { label: 'Chat now', composerSubmit: true, expectedComposerText: SA.CHAT_OPENING_LINE }), reply.chatNow);
  assert.equal(pageCode(() => runPage(form(`${SA.CHAT_OPENING_LINE} Please refund us.`).body, 'control', { label: 'Chat now', composerSubmit: true, expectedComposerText: SA.CHAT_OPENING_LINE })), 'composer_changed');
});

const composerChanged = () => Object.assign(new Error('EW:composer_changed:'), { code: 'composer_changed' });

test('Chat now binds its lookup to the opening line and clicks nothing when the page says it changed', async () => {
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir, { plan_item: 'P3', sha256: P3_SHA });
    const args = { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Chat now' };
    const ok = chatRuntime(dir);
    assert.equal((await executeCommand(ok.rt, command('001', 'submit', args))).status, 'sent');
    assert.ok(ok.events.includes(`composer-text:${sha256(SA.CHAT_OPENING_LINE)}`), 'the case page lookup gets the opening line');
    await rm(join(dir, 'approvals.jsonl'));
    const changed = chatRuntime(dir);
    const prepare = changed.rt.browser.prepareClick;
    changed.rt.browser.prepareClick = async (...a) => { await prepare(...a); throw composerChanged(); };
    const result = await executeCommand(changed.rt, command('002', 'submit', args));
    assert.equal(result.status, 'blocked'); assert.equal(result.reason, 'composer_changed'); assert.equal(result.clicked, false);
    assert.ok(!changed.events.includes('dispatch') && !changed.events.some(e => e.startsWith('adopt:')), 'nothing clicked, no window adopted');
    assert.deepEqual(await readLog(dir), [], 'no attempt line');
    assert.equal(changed.rt.counts.get(`chat_now:${P3_SHA}`) ?? 0, 0);
    assert.equal(changed.rt.chat, null);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

test('a Send in the adopted chat window binds its lookup to the approved text in that window', async () => {
  const dir = await runDir();
  try {
    const approval = await approvalFile(dir, { plan_item: 'P3', sha256: P3_SHA });
    const run = chatRuntime(dir);
    assert.equal((await executeCommand(run.rt, command('001', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Chat now' }))).status, 'sent');
    assert.equal(run.rt.browser, run.chat.rt.browser);
    run.chat.current.composer.value = P3;
    const prepare = run.chat.rt.browser.prepareClick;
    let changeNext = true;
    run.chat.rt.browser.prepareClick = async (...a) => { const point = await prepare(...a); if (changeNext) { changeNext = false; throw composerChanged(); } return point; };
    const blocked = await executeCommand(run.rt, command('002', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Send' }));
    assert.equal(blocked.status, 'blocked'); assert.equal(blocked.reason, 'composer_changed'); assert.equal(blocked.clicked, false);
    assert.ok(run.chat.events.includes('prepare:Send') && run.chat.events.includes(`composer-text:${P3_SHA}`), 'the chat window lookup gets the approved text');
    assert.ok(!run.chat.events.includes('dispatch')); assert.deepEqual(run.chat.sent, []);
    assert.deepEqual((await readLog(dir)).filter(x => x.command === 'submit'), [], 'no submit attempt line');
    assert.equal(run.rt.counts.get(`submit:${P3_SHA}`) ?? 0, 0);
    const sent = await executeCommand(run.rt, command('003', 'submit', { 'expect-sha256': P3_SHA, 'approval-file': approval, label: 'Send' }));
    assert.equal(sent.status, 'sent'); assert.deepEqual(run.chat.sent, [P3]);
  } finally { await rm(dir, { recursive: true, force: true }); }
});

// PR #76 review finding F3: Grimoire never drives this route, so serve refuses
// WIZARDS_AI_MODE and wizards-ai-* units on either session, before it reads the
// run directory or loads a browser module. cases.mjs keeps Grimoire on 9223.
test('F3: serve refuses under WIZARDS_AI_MODE or in a wizards-ai unit, on 9222 and on 9223', async () => {
  const human = '0::/user.slice/user-1000.slice/user@1000.service/app.slice/app-com.t3tools.T3Code-1.scope\n';
  const code = (env, cgroup = human) => { try { SA.assertAttended(env, cgroup); return 'ok'; } catch (error) { return error.code; } };
  assert.equal(code({ AMAZON_BROWSER_SESSION: 'grimoire', CDP_PORT: '9223', WIZARDS_AI_MODE: '1' }), 'attended_context_required');
  assert.equal(code({ WIZARDS_AI_MODE: '1' }), 'attended_context_required', 'the default session is Grimoire');
  assert.equal(code({ AMAZON_BROWSER_SESSION: 'operator', CDP_PORT: '9222', WIZARDS_AI_MODE: '1' }), 'attended_context_required');
  assert.equal(code({ WIZARDS_AI_MODE: '' }), 'attended_context_required', 'set but empty still counts');
  assert.equal(code({ CDP_PORT: '9223' }, '0::/system.slice/wizards-ai-case-daily.service\n'), 'attended_context_required');
  assert.equal(code({ CDP_PORT: '9223' }), 'ok', 'an attended run may still use the Grimoire session');
  assert.equal(code({ CDP_PORT: '9222' }), 'ok');
  // serve itself: the refusal comes first, so a missing run directory is never read.
  const saved = process.env.WIZARDS_AI_MODE;
  process.env.WIZARDS_AI_MODE = '1';
  try {
    const missing = join(tmpdir(), `seller-assistant-f3-${process.pid}-absent`);
    await assert.rejects(SA.serve({ run: missing }), error => error.code === 'attended_context_required');
    assert.equal(existsSync(missing), false, 'no run directory was created');
  } finally { if (saved === undefined) delete process.env.WIZARDS_AI_MODE; else process.env.WIZARDS_AI_MODE = saved; }
});

// Review F2: `send` drives the attended browser through a running serve, so
// Grimoire may not queue a command either. The client refuses itself, and serve
// refuses a command whose client is gone or sits in a wizards-ai unit.
test('F2: send refuses under WIZARDS_AI_MODE and serve runs only commands from a live attended client', { timeout: 20000 }, async () => {
  const dir = await runDir();
  const saved = process.env.WIZARDS_AI_MODE;
  try {
    const account = { profile_key: 'acme-us', client_slug: 'acme', marketplace: 'US', seller_id: 'A1TEST', marketplace_id: 'ATVPDKIKX0DER', seller_central_name: 'Acme', marketplace_label: 'United States', parent_account_name: 'Acme Group' };
    await writeFile(join(dir, 'run.json'), JSON.stringify({ schema_version: 1, run_id: 'sa-test', account }));
    await writeFile(join(dir, 'serve.pid'), JSON.stringify({ pid: process.pid }));
    process.env.WIZARDS_AI_MODE = '1';
    await assert.rejects(sendCommand({ run: dir, command: 'state', args: {} }, { pollMs: 10, out: () => {} }), error => error.code === 'attended_context_required');
    assert.deepEqual(await readdir(join(dir, 'queue')), [], 'nothing was queued');
    if (saved === undefined) delete process.env.WIZARDS_AI_MODE; else process.env.WIZARDS_AI_MODE = saved;

    const { rt, events } = fakeRuntime(dir);
    const grimoire = '0::/user.slice/user-1000.slice/user@1000.service/app.slice/wizards-ai-slack.service\n';
    const cases = [['001', () => grimoire, 'attended_context_required'], ['002', () => null, 'client_gone']];
    for (const [id, cgroup, reason] of cases) {
      rt.deps.clientCgroup = cgroup;
      await writeFile(join(dir, 'queue', `${id}.json`), JSON.stringify(command(id, 'state')));
      const result = await processNext(rt);
      assert.deepEqual([result.id, result.status, result.reason], [id, 'refused', reason]);
    }
    const { client_pid: _pid, ...unstamped } = command('003', 'state');
    await writeFile(join(dir, 'queue', '003.json'), JSON.stringify(unstamped));
    assert.equal((await processNext(rt)).reason, 'command_malformed', 'a command without its client pid never runs');
    assert.deepEqual(events, [], 'no refused command reached the browser or the identity check');
    rt.deps.clientCgroup = () => ATTENDED_CGROUP;
    await writeFile(join(dir, 'queue', '004.json'), JSON.stringify(command('004', 'state')));
    assert.equal((await processNext(rt)).status, 'ok');
    // The default reader: a live process has a readable cgroup, a finished one has none.
    assert.equal(typeof SA.readClientCgroup(process.pid), 'string');
    if (existsSync('/proc/self/cgroup')) assert.equal(SA.readClientCgroup(2 ** 30), null);
  } finally {
    if (saved === undefined) delete process.env.WIZARDS_AI_MODE; else process.env.WIZARDS_AI_MODE = saved;
    await rm(dir, { recursive: true, force: true });
  }
});
