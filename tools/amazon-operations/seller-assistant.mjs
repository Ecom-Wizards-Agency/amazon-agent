#!/usr/bin/env node
/** Seller Assistant step driver for attended Seller Support chats and case replies.
 *
 * `serve` is the only process that touches the browser. It holds one managed task
 * tab for the whole chat, in the operator session on 9222 (attended runs) or the
 * Grimoire session on 9223, and executes queued commands one at a time. `send`
 * writes one command into the run directory and waits for its result; it never
 * imports a browser module.
 *
 * Safety model: outbound actions (Submit, Send, Chat now, Approve, file attach)
 * run only when the live composer text, handoff terms or file hash equals an
 * operator-approved SHA-256 recorded in an approval file. Navigation clicks use a
 * fixed allowlist. Enter is never pressed. Identity (seller and marketplace) is
 * verified on the task tab before and after every command and again immediately
 * before each outbound click. A run bound to a case registry row also asks the
 * case service (claim-attended) before each outbound action.
 *
 * Attended use only. Grimoire never runs this driver; the operator session is
 * refused under WIZARDS_AI_MODE or inside a wizards-ai-* unit.
 */
import { mkdir, readFile, readdir, rename, writeFile, open, appendFile, unlink, copyFile } from 'node:fs/promises';
import { unlinkSync, existsSync, readFileSync, constants as fsConstants } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { basename, dirname, isAbsolute, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

export const MAX_COMPOSER_CHARS = 2500;
export const NAVIGATION_LABELS = Object.freeze(['Get help with a new issue', 'Show more', 'Show less']);
// Reply opens the reply form of a case and sends nothing. It is allowed only on
// the case view page.
export const REPLY_LABEL = 'Reply';
export const SUBMIT_LABELS = Object.freeze(['Submit', 'Send', 'Chat now']);
export const UPLOAD_LABELS = Object.freeze(['Upload file', 'Attach']);
// The case reply form's Chat now button opens Amazon's case chat in a new window.
// Its opening line and the "Your name" value (the case owner's signature_name
// from run.json) are code constants shown in the operator's draft, so they are
// covered by the approval of the message the chat delivers.
export const CHAT_OPENING_LINE = 'Hello.';
export const CHAT_SLOT = 'case-chat';
export const CASE_VIEW_PATH = '/cu/case-dashboard/view-case';
export const CASE_CHAT_PATH = '/hill/website/chat';
// Labels an attended text approval must carry (case_service.py LABELS).
export const APPROVAL_LABELS = Object.freeze(['routine', 'appeal', 'dispute', 'refund_request', 'commitment', 'admission']);
const TEXT_ITEMS = new Set(['P1', 'P2', 'P3', 'followup']);
const SESSION_PORTS = Object.freeze({ grimoire: 9223, operator: 9222 });
const CASE_SERVICE = join(dirname(fileURLToPath(import.meta.url)), 'case_service.py');
export const TOUR_LABELS = Object.freeze(['Skip', 'Skip tour', 'Got it', 'Done', 'Next', 'Finish', 'Close', 'Dismiss']);
// Request changes reopens an email-case Issue summary for editing and sends
// nothing. It is allowed only while exactly one Approve control is visible.
export const SUMMARY_LABELS = Object.freeze(['Request changes']);
export const PLAN_ITEMS = Object.freeze(['P1', 'P2', 'P3', 'approve', 'attachment', 'followup']);
const COMMAND_PLAN_ITEMS = { submit: ['P1', 'P2', 'P3', 'followup'], approve: ['approve'], attach: ['attachment'] };
// P2 ("Please connect me with a Seller Support associate.") may be sent twice.
// Every other approved hash is sent at most once per run; an uncertain send is
// never retried automatically.
const SEND_LIMITS = { P2: 2 };
const ASSISTANT_PATH = '/assistant?client=sellerSupport-meldFullPage';
// An existing Seller Assistant conversation, reopened after a controller restart.
export const CONVERSATION_PATH = /^\/assistant\/amzn1\.cyrano\.conversation\.cid\.v2\.\d{10,40}\?client=sellerSupport-meldFullPage$/;
const LOBBY_PATH = '/cu/case-lobby';
const RUN_ID = /^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$/;
const SHA = /^[a-f0-9]{64}$/;
const ISO_TZ = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?(?:Z|[+-]\d{2}:\d{2})$/;
export const ACCOUNT_KEYS = Object.freeze(['profile_key', 'client_slug', 'marketplace', 'seller_id', 'marketplace_id',
  'seller_central_name', 'marketplace_label', 'parent_account_name']);
const OUTBOUND = new Set(['open', 'navigate', 'type', 'submit', 'approve', 'attach']);
const SUCCESS = new Set(['ok', 'sent', 'approved', 'attached']);
const ACTION_DONE = new Set(['sent', 'approved', 'attached']);
const CHAT_FRAME_URL = /assistant|cyrano|meld|chat|seller-?support/i;
const RUN_SUBDIRS = ['queue', 'results', 'steps', 'transcripts', 'screenshots', 'viewcase', 'uploads'];
// An approval may be stamped up to five minutes ahead of the controller clock.
const APPROVAL_CLOCK_SKEW_MS = 5 * 60000;

export const sha256 = value => createHash('sha256').update(value).digest('hex');
export const collapse = v => String(v ?? '').replace(/\s+/g, ' ').trim();
// Same rule as cases.mjs bodyText: CR and CRLF become LF; leading and trailing
// newlines are dropped. Approved texts are hashed in this form.
export const normalizeText = value => String(value ?? '').replace(/\r\n?/g, '\n').replace(/^\n+|\n+$/g, '');
// A contenteditable composer reports runs of spaces as no-break spaces.
export const normalizeComposer = value => normalizeText(String(value ?? '').replace(/ /g, ' '));
// Terms are hashed per visible line: spacing collapsed, blank lines dropped. The
// `state` command reports the same text and hash that `approve` checks.
export const normalizeTerms = value => String(value ?? '').replace(/\r\n?/g, '\n').split('\n')
  .map(line => line.replace(/[ \t ]+/g, ' ').trim()).filter(Boolean).join('\n');
export const termsHash = text => sha256(normalizeTerms(text));

function codeError(code, message = code, extra = {}) {
  return Object.assign(new Error(message), { code }, extra);
}
const isFatal = error => /^(?:TASK_|BROWSER_SESSION)/.test(String(error?.code || '')) ||
  /TASK_TAB_CONTROL_LOST|BROWSER_SESSION_LOCK_LOST/.test(String(error?.message || ''));

// ------------------------------------------------------------------- session

const readCgroup = () => { try { return readFileSync('/proc/self/cgroup', 'utf8'); } catch { return ''; } };

/** Grimoire sets WIZARDS_AI_MODE and runs in wizards-ai-* units; either one marks
 * an unattended process. Same rule as case_service.py unattended_context. */
export function unattendedContext(env = process.env, cgroup = readCgroup()) {
  if (env.WIZARDS_AI_MODE !== undefined) return true;
  return String(cgroup ?? '').split('\n').some(line => {
    const fields = line.split(':');
    return (fields.length > 2 ? fields.slice(2).join(':') : fields.at(-1)).split('/').some(part => part.startsWith('wizards-ai-'));
  });
}

/** The browser session a case or Seller Assistant run may use: the operator
 * session on 9222 (never from Grimoire's environment) or Grimoire on 9223. The
 * same resolution as browserctl session.mjs: a named session fixes its port, else
 * CDP_PORT 9222 means operator. Only 9223 carries the port-wide session lock. */
export function assertSession(env = process.env, cgroup = undefined) {
  const port = env.CDP_PORT ? Number(env.CDP_PORT) : null;
  const session = env.AMAZON_BROWSER_SESSION || (port === 9222 ? 'operator' : 'grimoire');
  const expected = SESSION_PORTS[session];
  if (!expected || (port !== null && port !== expected)) {
    throw codeError('session_invalid', 'Seller Support runs need the operator session on 9222 or the Grimoire session on 9223');
  }
  if (session === 'operator' && unattendedContext(env, cgroup === undefined ? readCgroup() : cgroup)) {
    throw codeError('attended_context_required', 'The operator session is refused under WIZARDS_AI_MODE or inside a wizards-ai unit');
  }
  return { session, port: expected, lockPort: expected === 9223 ? 9223 : null };
}

/** Grimoire's 9223 lock is held for the whole chat. The operator browser has no
 * port lock; its Seller Central work serializes on the task tab's region claim. */
export function acquireServeLock(binding, lock) {
  return binding?.lockPort === 9223 ? lock.acquireSessionLock(9223, 'seller-assistant') : () => {};
}

// ---------------------------------------------------------------- pure checks

export function validateRunConfig(config) {
  if (!config || typeof config !== 'object' || Array.isArray(config)) throw codeError('run_config_invalid', 'run.json must be an object');
  if (config.schema_version !== 1) throw codeError('run_config_invalid', 'run.json schema_version must be 1');
  if (typeof config.run_id !== 'string' || !RUN_ID.test(config.run_id)) throw codeError('run_config_invalid', 'run.json run_id must match [A-Za-z0-9][A-Za-z0-9_.-]{0,63}');
  const account = config.account;
  if (!account || typeof account !== 'object') throw codeError('run_config_invalid', 'run.json account is required');
  for (const key of ACCOUNT_KEYS) {
    if (typeof account[key] !== 'string' || !account[key].trim()) throw codeError('run_config_invalid', `run.json account.${key} must be a non-empty string`);
  }
  const kept = Object.fromEntries(ACCOUNT_KEYS.map(key => [key, account[key]]));
  // The policy's label binding lets the identity check trust the exact header
  // when a page exposes no live IDs (browser-ui contextMatches). It must name
  // this account's own IDs.
  if (account.context_binding !== undefined) {
    const b = account.context_binding;
    if (!b || typeof b !== 'object' || Array.isArray(b)) throw codeError('run_config_invalid', 'run.json account.context_binding must be an object');
    if (b.seller_id !== account.seller_id || b.marketplace_id !== account.marketplace_id) throw codeError('run_config_invalid', 'run.json account.context_binding IDs must equal the account seller_id and marketplace_id');
    if (b.unique_label_mapping !== true) throw codeError('run_config_invalid', 'run.json account.context_binding.unique_label_mapping must be true');
    kept.context_binding = { seller_id: b.seller_id, marketplace_id: b.marketplace_id, unique_label_mapping: true };
  }
  const run = { schema_version: 1, run_id: config.run_id, account: kept };
  // A run bound to a case registry row passes the draft baseline (from
  // case_service.py sign) and the attended authorization to claim-attended before
  // every outbound action. Without registry_id the case is not registered yet.
  if (config.registry_id !== undefined) {
    if (typeof config.registry_id !== 'string' || !config.registry_id.trim()) throw codeError('run_config_invalid', 'run.json registry_id must be a non-empty string');
    const baseline = config.baseline;
    if (!baseline || typeof baseline !== 'object' || Array.isArray(baseline) || !('last_sent_at' in baseline) || !(baseline.last_sent_at === null || isIsoTime(baseline.last_sent_at))) {
      throw codeError('run_config_invalid', 'run.json baseline.last_sent_at must be the sign result: a timestamp or null');
    }
    const auth = config.authorization;
    if (!auth || typeof auth !== 'object' || Array.isArray(auth) || auth.kind !== 'attended' || typeof auth.source?.instruction !== 'string' || !auth.source.instruction.trim()) {
      throw codeError('run_config_invalid', 'run.json authorization must be an attended authorization with source.instruction');
    }
    Object.assign(run, { registry_id: config.registry_id, baseline: { last_sent_at: baseline.last_sent_at }, authorization: auth });
  }
  // The case chat's "Your name" field (maxlength 100 on the 2026-10-01 form).
  if (config.signature_name !== undefined) {
    if (typeof config.signature_name !== 'string' || !config.signature_name.trim() || config.signature_name.length > 100 || /[\r\n]/.test(config.signature_name)) {
      throw codeError('run_config_invalid', 'run.json signature_name must be one line of at most 100 characters');
    }
    run.signature_name = config.signature_name;
  }
  return run;
}

/** The claim-attended request for this run (case_service.py README contract). */
export function claimRequest(config) {
  return { registry_id: config.registry_id, run_id: config.run_id, account: { seller_id: config.account.seller_id, marketplace_id: config.account.marketplace_id },
    baseline: config.baseline, authorization: config.authorization };
}

/** Ask the case service whether this attended run may click. Anything but exit 0
 * with status `claimed` is a refusal. */
export function runClaimAttended(requestPath, exec = execFile) {
  return new Promise(done => {
    exec('python3', [CASE_SERVICE, 'claim-attended', '--request', requestPath], { encoding: 'utf8', timeout: 30000 }, (error, stdout) => {
      let answer = null;
      try { answer = JSON.parse(String(stdout || '').trim().split('\n').at(-1)); } catch { /* reported below */ }
      if (!error && answer?.status === 'claimed') return done({ ok: true, ...answer });
      done({ ok: false, reason: answer?.reason || (typeof error?.code === 'string' ? 'claim_unavailable' : 'claim_unreadable'),
        message: String(answer?.message || error?.message || 'claim-attended gave no answer').slice(0, 300) });
    });
  });
}

/** Case page and case chat window checks, by URL. */
export function isCaseViewPage(url, caseId = null) {
  let parsed;
  try { parsed = new URL(url); } catch { return false; }
  return parsed.pathname === CASE_VIEW_PATH && (caseId === null || parsed.searchParams.get('caseID') === caseId);
}

/** The Chat now window Amazon opens for a case reply: same origin, the chat
 * path, this case and reply form type (observed 2026-10-01:
 * /hill/website/chat?formType=reply&...&caseID=<id>&contactRequestId=...), opened
 * by the task tab. Anything else is an unexpected tab. */
export function isCaseChatTarget(info, { origin, caseId, openerId }) {
  if (!info || info.type !== 'page') return { ok: false, reason: 'chat_target_not_page' };
  let url;
  try { url = new URL(info.url); } catch { return { ok: false, reason: 'chat_url_invalid' }; }
  if (url.origin !== origin) return { ok: false, reason: 'chat_origin_mismatch' };
  if (url.pathname !== CASE_CHAT_PATH) return { ok: false, reason: 'chat_path_mismatch' };
  if (!caseId || url.searchParams.get('caseID') !== caseId) return { ok: false, reason: 'chat_case_mismatch' };
  if (url.searchParams.get('formType') !== 'reply') return { ok: false, reason: 'chat_form_type_mismatch' };
  if (!openerId || info.openerId !== openerId) return { ok: false, reason: 'chat_opener_mismatch' };
  return { ok: true };
}

/** A timestamp with a timezone whose calendar fields are real (no 31 February). */
export function isIsoTime(value) {
  if (typeof value !== 'string') return false;
  const m = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})(?::(\d{2})(?:\.\d{1,9})?)?(Z|([+-])(\d{2}):(\d{2}))$/.exec(value);
  if (!m) return false;
  const [year, month, day, hour, minute, second] = [m[1], m[2], m[3], m[4], m[5], m[6] ?? '0'].map(Number);
  const days = new Date(Date.UTC(year, month, 0)).getUTCDate();
  if (month < 1 || month > 12 || day < 1 || day > days || hour > 23 || minute > 59 || second > 59) return false;
  if (m[7] !== 'Z' && (Number(m[9]) > 23 || Number(m[10]) > 59)) return false;
  return !Number.isNaN(Date.parse(value));
}

/** Identity for one check. A live ID that is present and differs fails at once;
 * the IDs read on /home at startup fill only fields the live read lacks. */
export function resolveIdentity(live, home, account) {
  const marketOf = x => (typeof x?.marketplace === 'string' ? x.marketplace : x?.marketplace?.marketplaceId) || null;
  const liveSeller = live?.merchantId || null, liveMarket = marketOf(live);
  if (liveSeller && liveSeller !== account.seller_id) return { ok: false, reason: 'live seller ID differs' };
  if (liveMarket && liveMarket !== account.marketplace_id) return { ok: false, reason: 'live marketplace ID differs' };
  const identity = { merchantId: liveSeller || home?.merchantId || null, marketplace: liveMarket || marketOf(home) };
  const source = liveSeller && liveMarket ? 'live' : (liveSeller || liveMarket) ? 'live+home' : 'home+header';
  return { ok: true, identity, source };
}

/** The Submit to click must be the only visible Submit in the composer's frame,
 * sit in the composer's region, and be enabled, and the composer must be
 * enabled. Also injected into the page (see pageAgent). */
export function composerSubmitCheck(composer, submits) {
  if (!composer) return { ok: false, reason: 'composer_missing' };
  if (composer.disabled) return { ok: false, reason: 'composer_disabled' };
  if (!Array.isArray(submits)) return { ok: false, reason: 'submit_scope_unknown' };
  if (submits.length !== 1) return { ok: false, reason: submits.length ? 'submit_not_unique' : 'submit_not_found', count: submits.length };
  if (submits[0].in_region !== true) return { ok: false, reason: 'submit_outside_composer_region', count: 1 };
  if (submits[0].disabled) return { ok: false, reason: 'submit_disabled', count: 1 };
  return { ok: true, index: 0 };
}

/** Attachments before Submit. Every observed file (chips and file input) and
 * every expected name must be an attach this run logged as attached, and the
 * expected set must equal the observed set. A file in the input without a
 * detected chip fails closed. */
export function attachmentCheck(attachments, expected, approvedNames) {
  const chips = attachments?.chips || [], inputs = attachments?.input_files || [];
  const approved = new Set(approvedNames || []);
  if (inputs.length && !chips.length) return { ok: false, reason: 'attachment_chips_undetected', input_files: inputs };
  const observed = [...new Set([...chips, ...inputs])];
  const unapproved = observed.filter(n => !approved.has(n));
  if (unapproved.length) return { ok: false, reason: 'attachment_not_approved', names: unapproved };
  const unbound = (expected || []).filter(n => !approved.has(n));
  if (unbound.length) return { ok: false, reason: 'expected_attachment_not_approved', names: unbound };
  if (!sameSet(expected || [], observed)) return { ok: false, reason: 'attachment_mismatch', observed, expected: expected || [] };
  return { ok: true, observed };
}

/** Exact whitespace-collapsed label match over visible controls. Exactly one
 * enabled match is required. Also injected into the page (see pageAgent). */
export function matchLabel(controls, label) {
  const want = collapse(label);
  const list = controls || [];
  const same = list.filter(c => c && c.visible !== false && collapse(c.label) === want);
  const enabled = same.filter(c => !c.disabled);
  if (enabled.length === 1) return { ok: true, index: list.indexOf(enabled[0]), control: enabled[0] };
  if (enabled.length > 1) return { ok: false, reason: 'ambiguous', count: enabled.length };
  if (same.length) return { ok: false, reason: 'disabled', count: same.length };
  return { ok: false, reason: 'not_found', count: 0 };
}

/** Pick the unique same-origin frame (main frame included) holding exactly one
 * visible composer. Cross-origin frames are never evaluated. */
export function selectComposerFrame(frames) {
  const brief = f => ({ frame_id: f.frame_id, url: f.url, origin: f.origin, composer_count: f.composer_count ?? 0 });
  const same = frames.filter(f => f.same_origin && f.reachable);
  const multiple = same.filter(f => f.composer_count > 1);
  const hits = same.filter(f => f.composer_count === 1);
  const chatLike = frames.filter(f => !f.same_origin && CHAT_FRAME_URL.test(f.url || ''));
  const unreachable = frames.filter(f => f.same_origin && !f.reachable);
  if (chatLike.length) return { ok: false, reason: 'cross_origin_chat_frame', details: { frames: chatLike.map(brief) } };
  if (multiple.length) return { ok: false, reason: 'multiple_composers', details: { frames: multiple.map(brief) } };
  if (hits.length > 1) return { ok: false, reason: 'multiple_composer_frames', details: { frames: hits.map(brief) } };
  if (hits.length === 1) return { ok: true, frame_id: hits[0].frame_id };
  if (unreachable.length) return { ok: false, reason: 'frame_unreachable', details: { frames: unreachable.map(brief) } };
  return { ok: false, reason: 'no_composer', details: { frames: frames.map(brief) } };
}

export function isNavigationAllowed(label, state = {}, { origin = null, caseId = null } = {}) {
  const wanted = collapse(label);
  if (NAVIGATION_LABELS.includes(wanted)) return { ok: true, kind: 'navigation' };
  if (wanted === REPLY_LABEL) {
    const onCase = isCaseViewPage(state?.url, caseId) && (!origin || originOf(state.url) === origin);
    return onCase ? { ok: true, kind: 'reply' } : { ok: false, reason: 'reply_not_on_case_page' };
  }
  if (TOUR_LABELS.includes(wanted)) {
    return state?.tour?.visible === true ? { ok: true, kind: 'tour' } : { ok: false, reason: 'tour_not_visible' };
  }
  if (SUMMARY_LABELS.includes(wanted)) {
    return state?.handoff?.approve_count >= 1 ? { ok: true, kind: 'summary' } : { ok: false, reason: 'summary_not_visible' };
  }
  return { ok: false, reason: 'label_not_allowed' };
}

const DENIALS = [/(?:don['’]t|do not) currently have permission to create (?:a )?support cases?[^.\n]*\.?/i,
  /do not currently have permission[^.\n]*\.?/i];
export function detectDenial(text) {
  const value = String(text ?? '');
  for (const pattern of DENIALS) {
    const match = pattern.exec(value);
    if (match) {
      const start = value.lastIndexOf('\n', match.index) + 1;
      const end = value.indexOf('\n', match.index + match[0].length);
      return { detected: true, text: collapse(value.slice(start, end < 0 ? undefined : end)).slice(0, 400) };
    }
  }
  return { detected: false, text: null };
}

export function detectTour(text) {
  const match = /\bStep\s*\d+\s*\/\s*\d+\b/.exec(String(text ?? ''));
  return match ? { visible: true, text: match[0] } : { visible: false, text: null };
}

/** Text files must already be in normalized form so `sha256sum <file>` equals the
 * approved text hash: UTF-8, no BOM, LF line endings, no leading or trailing newline. */
export function checkTextFile(buffer, expectedSha) {
  if (!SHA.test(expectedSha || '')) return { ok: false, reason: 'expected_sha_invalid' };
  if (sha256(buffer) !== expectedSha) return { ok: false, reason: 'text_sha_mismatch' };
  let text;
  try { text = new TextDecoder('utf-8', { fatal: true }).decode(buffer); } catch { return { ok: false, reason: 'text_not_utf8' }; }
  if (text.startsWith('﻿') || text !== normalizeText(text) || text.includes(' ')) return { ok: false, reason: 'text_file_not_normalized' };
  if (!text.trim()) return { ok: false, reason: 'text_empty' };
  // The page counter is assumed to count like a textarea maxlength: JavaScript
  // string length (UTF-16 code units) after CRLF to LF normalization.
  if (text.length > MAX_COMPOSER_CHARS) return { ok: false, reason: 'text_too_long', length: text.length };
  return { ok: true, text, length: text.length };
}

export function checkComposer(value, expectedSha) {
  const text = normalizeComposer(value);
  const facts = { length: text.length, sha256: sha256(text) };
  if (!SHA.test(expectedSha || '')) return { ...facts, ok: false, reason: 'expected_sha_invalid' };
  if (!text) return { ...facts, ok: false, reason: 'composer_empty' };
  if (text.length > MAX_COMPOSER_CHARS) return { ...facts, ok: false, reason: 'composer_too_long' };
  if (facts.sha256 !== expectedSha) return { ...facts, ok: false, reason: 'composer_sha_mismatch' };
  return { ...facts, ok: true, text };
}

/** `context` binds the approval to this run: { runId, sellerId, now }, plus
 * `instruction` (the attended authorization's approval sentence) on a run bound to
 * a case registry row, whose receipt requires the same sentence on every text. */
export function validateApproval(approval, expectedSha, allowedItems = PLAN_ITEMS, context = {}) {
  const fail = reason => ({ ok: false, reason });
  if (!approval || typeof approval !== 'object' || Array.isArray(approval)) return fail('approval_malformed');
  if (approval.schema_version !== 1) return fail('approval_schema_invalid');
  if (!PLAN_ITEMS.includes(approval.plan_item)) return fail('approval_plan_item_invalid');
  if (!allowedItems.includes(approval.plan_item)) return fail('approval_plan_item_not_for_command');
  if (!SHA.test(approval.sha256 || '')) return fail('approval_sha_invalid');
  if (!SHA.test(expectedSha || '')) return fail('expected_sha_invalid');
  if (approval.sha256 !== expectedSha) return fail('approval_sha_mismatch');
  if (!isIsoTime(approval.approved_at)) return fail('approval_time_invalid');
  if (typeof approval.approval_text !== 'string' || !approval.approval_text.trim()) return fail('approval_text_missing');
  // Every text approval names what the operator approved: routine, or one of the
  // sensitive types the draft was labelled with.
  if (TEXT_ITEMS.has(approval.plan_item)) {
    if (approval.label === undefined || approval.label === null || approval.label === '') return fail('approval_label_missing');
    if (!APPROVAL_LABELS.includes(approval.label)) return fail('approval_label_invalid');
  }
  if (typeof approval.run_id !== 'string' || !approval.run_id) return fail('approval_run_id_missing');
  if (typeof approval.seller_id !== 'string' || !approval.seller_id) return fail('approval_seller_id_missing');
  if (!context.runId || !context.sellerId || typeof context.now !== 'number') return fail('approval_context_missing');
  if (approval.run_id !== context.runId) return fail('approval_run_mismatch');
  if (approval.seller_id !== context.sellerId) return fail('approval_seller_mismatch');
  if (TEXT_ITEMS.has(approval.plan_item) && context.instruction !== undefined && approval.approval_text.trim() !== String(context.instruction).trim()) return fail('approval_instruction_mismatch');
  if (Date.parse(approval.approved_at) > context.now + APPROVAL_CLOCK_SKEW_MS) return fail('approval_time_in_future');
  return { ok: true };
}

export async function loadApproval(path, expectedSha, allowedItems, read = readFile, context = {}) {
  let raw;
  try { raw = await read(path, 'utf8'); } catch { return { ok: false, reason: 'approval_missing' }; }
  let approval;
  try { approval = JSON.parse(raw); } catch { return { ok: false, reason: 'approval_malformed' }; }
  const verdict = validateApproval(approval, expectedSha, allowedItems, context);
  return verdict.ok ? { ok: true, approval } : verdict;
}

export function nextQueueName(existing) {
  let max = 0;
  for (const name of existing || []) {
    const match = /^(\d{3,})\.(?:json|claim)$/.exec(name);
    if (match) max = Math.max(max, Number(match[1]));
  }
  return String(max + 1).padStart(3, '0');
}

export function summarizeViewCase(payload) {
  const meta = payload?.viewCaseMetaData || {};
  const contacts = Array.isArray(payload?.contactList) ? payload.contactList : [];
  // Deliberately omits primaryEmail, sender and message text: stdout reaches chat.
  return {
    case_title: meta.caseTitle ?? null, case_status: meta.caseStatus ?? null, can_edit_case: meta.canEditCase ?? null,
    total_number_of_contacts: payload?.totalNumberOfContacts ?? null, contact_count: contacts.length,
    contacts: contacts.map(c => ({
      outbound: typeof c?.outbound === 'boolean' ? c.outbound : null, channel_type: c?.channelType ?? null,
      message_length: String(c?.message ?? '').length,
      attachment_names: (c?.attachments ?? c?.attachmentList ?? []).map?.(a => a?.fileName || a?.name || a?.attachmentName || '') ?? [],
    })),
  };
}

// ------------------------------------------------------------------ arguments

const FLAG_TYPES = {
  open: { 'via-lobby': 'bool', conversation: 'conversation', case: 'caseid' },
  state: {},
  navigate: { label: 'label' },
  type: { 'text-file': 'path', sha256: 'sha' },
  submit: { 'expect-sha256': 'sha', 'approval-file': 'path', 'expect-attachment': 'list', label: 'submitlabel' },
  approve: { 'expect-terms-sha256': 'sha', 'approval-file': 'path' },
  attach: { file: 'path', sha256: 'sha', 'approval-file': 'path' },
  transcript: { 'wait-new': 'int', timeout: 'int' },
  screenshot: { name: 'name' },
  'viewcase-raw': { 'case-id': 'caseid' },
  stop: {},
};
const REQUIRED = {
  navigate: ['label'], type: ['text-file', 'sha256'], submit: ['expect-sha256', 'approval-file'],
  approve: ['expect-terms-sha256', 'approval-file'], attach: ['file', 'sha256', 'approval-file'], 'viewcase-raw': ['case-id'],
};
export const COMMANDS = Object.freeze(Object.keys(FLAG_TYPES));
const INT_RANGE = { 'wait-new': [0, 50], timeout: [1, 1800] };

/** Validate command arguments. The server re-validates every queued command and
 * requires absolute paths; the client resolves relative paths before queueing. */
export function validateCommandArgs(command, args, { absolutePaths = true } = {}) {
  const types = FLAG_TYPES[command];
  if (!types) return { ok: false, reason: 'unknown_command' };
  if (!args || typeof args !== 'object' || Array.isArray(args)) return { ok: false, reason: 'args_invalid' };
  for (const key of Object.keys(args)) if (!(key in types)) return { ok: false, reason: `unknown_flag:${key}` };
  for (const key of REQUIRED[command] || []) if (args[key] === undefined) return { ok: false, reason: `missing_flag:${key}` };
  for (const [key, value] of Object.entries(args)) {
    const type = types[key];
    const bad = () => ({ ok: false, reason: `invalid_flag:${key}` });
    if (type === 'bool' && typeof value !== 'boolean') return bad();
    if (type === 'sha' && !(typeof value === 'string' && SHA.test(value))) return bad();
    if (type === 'path' && !(typeof value === 'string' && value && (!absolutePaths || isAbsolute(value)))) return bad();
    if (type === 'label' && !(typeof value === 'string' && collapse(value) && value.length <= 100)) return bad();
    if (type === 'submitlabel' && !SUBMIT_LABELS.includes(value)) return bad();
    if (type === 'name' && !(typeof value === 'string' && /^[A-Za-z0-9][A-Za-z0-9_.-]{0,39}$/.test(value))) return bad();
    if (type === 'caseid' && !(typeof value === 'string' && /^\d{5,30}$/.test(value))) return bad();
    if (type === 'conversation' && !(typeof value === 'string' && CONVERSATION_PATH.test(value))) return bad();
    if (type === 'int' && !(Number.isInteger(value) && value >= INT_RANGE[key][0] && value <= INT_RANGE[key][1])) return bad();
    if (type === 'list' && !(Array.isArray(value) && value.every(v => typeof v === 'string' && v && v.length <= 200 && !/[\\/]/.test(v)))) return bad();
  }
  return { ok: true };
}

export function parseArgs(argv) {
  const [mode, ...rest] = argv;
  const usage = message => codeError('usage', `${message}. Usage: seller-assistant.mjs serve --run <dir> [--max-minutes N] [--idle-minutes N] | send --run <dir> <command> [args]`);
  if (!['serve', 'send'].includes(mode)) throw usage('First argument must be serve or send');
  if (mode === 'serve') {
    const options = { mode, run: null, maxMinutes: 90, idleMinutes: 20 };
    for (let i = 0; i < rest.length; i += 2) {
      const key = rest[i], value = rest[i + 1];
      if (value === undefined) throw usage(`${key} needs a value`);
      if (key === '--run') { options.run = value; continue; }
      if (!['--max-minutes', '--idle-minutes'].includes(key)) throw usage(`Unknown serve argument ${key}`);
      const minutes = Number(value);
      if (!/^\d+$/.test(value) || minutes < 1 || minutes > 240) throw usage(`${key} must be an integer from 1 to 240`);
      options[key === '--max-minutes' ? 'maxMinutes' : 'idleMinutes'] = minutes;
    }
    if (!options.run) throw usage('--run <dir> is required');
    return options;
  }
  let run = null, command = null;
  const args = {};
  for (let i = 0; i < rest.length; i++) {
    const token = rest[i];
    if (token === '--run') {
      run = rest[++i];
      if (run === undefined) throw usage('--run needs a value');
      continue;
    }
    if (!command) {
      if (token.startsWith('--')) throw usage('The command name must come before its flags');
      if (!FLAG_TYPES[token]) throw usage(`Unknown command ${token}`);
      command = token;
      continue;
    }
    if (!token.startsWith('--')) throw usage(`Unexpected argument ${token}`);
    const key = token.slice(2), type = FLAG_TYPES[command][key];
    if (!type) throw usage(`Unknown flag --${key} for ${command}`);
    if (type === 'bool') { args[key] = true; continue; }
    const value = rest[++i];
    if (value === undefined || value.startsWith('--')) throw usage(`--${key} needs a value`);
    if (type === 'int') { if (!/^\d+$/.test(value)) throw usage(`--${key} must be an integer`); args[key] = Number(value); }
    else if (type === 'list') (args[key] ||= []).push(value);
    else if (type === 'path') args[key] = resolve(value);
    else args[key] = value;
  }
  if (!run) throw usage('--run <dir> is required');
  if (!command) throw usage('A command is required');
  const verdict = validateCommandArgs(command, args);
  if (!verdict.ok) throw usage(`Invalid arguments: ${verdict.reason}`);
  return { mode, run, command, args };
}

// ------------------------------------------------------------------ page side

/** Runs inside one frame's isolated world. It must stay self-contained because
 * it is serialized with Function.prototype.toString; `collapse` and `matchLabel`
 * are injected so the page and the tests share one matching rule. */
export function pageAgent(op, arg, lib) {
  const { collapse, matchLabel, detectTour, composerSubmitCheck, submitLabels, uploadLabels } = lib;
  const fail = (code, detail = '') => { throw new Error(`EW:${code}:${detail}`); };
  const roots = [document], els = [];
  for (let i = 0; i < roots.length; i++) for (const el of roots[i].querySelectorAll('*')) { els.push(el); if (el.shadowRoot) roots.push(el.shadowRoot); }
  const visible = el => { const r = el.getBoundingClientRect(); if (!(r.width > 0 && r.height > 0)) return false; return el.checkVisibility ? el.checkVisibility({ visibilityProperty: true, opacityProperty: true }) : true; };
  const parentOf = n => { const p = n && n.parentNode; if (!p) return null; return p.nodeType === 11 ? (p.host || null) : p; };
  const within = (outer, inner) => { for (let n = inner; n; n = parentOf(n)) if (n === outer) return true; return false; };
  const disabledOf = el => el.disabled === true || el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true';
  const labelOf = el => collapse(el.getAttribute('label') || el.getAttribute('aria-label') || el.innerText || el.textContent);
  const CONTROL = 'button,[role="button"],a,kat-button';
  const controls = () => {
    const raw = els.filter(el => el.matches(CONTROL) && visible(el)).map(el => ({ el, tag: el.tagName, label: labelOf(el), disabled: disabledOf(el) }));
    const kept = [];
    // A kat-button and the button inside its shadow root are one control.
    for (const c of raw) {
      const outer = raw.find(o => o !== c && o.label === c.label && within(o.el, c.el));
      if (outer) { outer.disabled = outer.disabled || c.disabled; continue; }
      kept.push(c);
    }
    return kept;
  };
  const composersOf = () => {
    const c = els.filter(el => visible(el) && (el.tagName === 'TEXTAREA' || (el.hasAttribute('contenteditable') && el.getAttribute('contenteditable') !== 'false')));
    return c.filter(el => !c.some(o => o !== el && within(o, el)));
  };
  const valueOf = el => el.tagName === 'TEXTAREA' ? el.value : (el.innerText || '');
  const composerLabel = el => collapse(el.getAttribute('placeholder') || el.getAttribute('aria-label') || el.getAttribute('aria-placeholder') || el.getAttribute('data-placeholder') || '');
  const leaves = scope => els.filter(el => el.children.length === 0 && !el.shadowRoot && (!scope || within(scope, el)) && visible(el));
  const FILE = /^[^\s\/\\:*?"<>|][^\/\\:*?"<>|\n]{0,199}\.[A-Za-z0-9]{1,8}$/;
  const COUNTER = /^\d{1,5}\s*\/\s*\d{1,5}$/;
  const STATUS = /^(?:working on it\b.*|here's what i found\b.*|thinking\b.*|connecting\b.*|.*\bis typing\b.*|.*\bhas joined\b.*|.*\bjoined the (?:chat|conversation)\b.*|.*\bhas left\b.*|.*\bchat (?:has )?ended\b.*)$/i;
  const all = controls();
  const comps = composersOf();
  const comp = comps.length === 1 ? comps[0] : null;
  // Composer region: the smallest ancestor that also holds the send control in
  // question (Submit by default) or an upload control (Upload file, Attach).
  const region = (el, label = 'Submit') => {
    const anchors = all.filter(c => c.label === label || uploadLabels.includes(c.label)).map(c => c.el);
    for (let n = parentOf(el), d = 0; n && d < 12; n = parentOf(n), d++) if (anchors.some(a => within(n, a))) return n;
    return parentOf(parentOf(el)) || el;
  };
  // Every visible control with this send label in this frame, each marked whether
  // it sits in the composer's region. A region that spans the conversation or a
  // message is too broad to vouch for any control (a rating or survey form lives there).
  const submitsOf = (el, c, label = 'Submit') => {
    const r = region(el, label);
    const broad = (c.basis === 'container' && within(r, c.area)) || c.msgs.some(m => within(r, m.el));
    return all.filter(x => x.label === label).map(x => ({ el: x.el, disabled: x.disabled, in_region: !broad && within(r, x.el) }));
  };
  // The case chat form's "Your name" input: its aria-label, a label element bound
  // to its id, or the form's input-name container (2026-10-01 reply form:
  // div[data-test-tag="input-name"] > kat-label + kat-input, the input in its shadow root).
  const nameFields = () => els.filter(el => el.tagName === 'INPUT' && (el.getAttribute('type') || 'text').toLowerCase() === 'text' && visible(el)).filter(el => {
    if (collapse(el.getAttribute('aria-label')) === 'Your name') return true;
    const id = el.getAttribute('id');
    if (id && els.some(l => l.tagName === 'LABEL' && l.getAttribute('for') === id && collapse(l.textContent) === 'Your name')) return true;
    for (let n = parentOf(el), d = 0; n && n.nodeType === 1 && d < 6; n = parentOf(n), d++) if (n.getAttribute('data-test-tag') === 'input-name') return true;
    return false;
  });
  const regionFacts = (el, c) => {
    const r = region(el);
    const texts = leaves(r).filter(x => !within(el, x)).map(x => collapse(x.textContent)).filter(Boolean);
    // File names can be direct text in a chip that also contains an icon or a
    // remove button, so the chip itself is not a leaf element.
    const directTexts = els.filter(x => within(r, x) && visible(x) && !within(el, x))
      .flatMap(x => [...(x.childNodes || [])].filter(n => n.nodeType === 3).map(n => collapse(n.textContent)))
      .filter(Boolean);
    const fileTexts = [...texts, ...directTexts].map(t => t.replace(/[\uE000-\uF8FF]/g, '').trim());
    const uploadError = [...texts, ...directTexts].some(t => /unsupported file was attached|upload failed|failed to upload/i.test(t));
    // Seller Assistant puts pending upload cards outside the smallest composer
    // region. Its composer placeholder changes while those cards are staged.
    const stagedFiles = /click send to upload/i.test(composerLabel(el))
      ? els.filter(x => visible(x) && x.matches('.file-name'))
        .filter(x => ![x, parentOf(x), parentOf(parentOf(x))].filter(Boolean)
          .some(n => /unsupported file was attached|upload failed|failed to upload/i.test(collapse(n.textContent))))
        .map(x => collapse(x.textContent)).filter(t => FILE.test(t))
      : [];
    const uploading = els.some(x => within(r, x) && visible(x) && (x.getAttribute('role') === 'progressbar' || x.getAttribute('aria-busy') === 'true')) ||
      texts.some(t => /^(?:uploading|upload failed|failed to upload)/i.test(t));
    const submit = submitsOf(el, c).map(x => ({ disabled: x.disabled, in_region: x.in_region }));
    const submitByLabel = Object.fromEntries(submitLabels.map(label => [label, submitsOf(el, c, label).map(x => ({ disabled: x.disabled, in_region: x.in_region }))]));
    return { chips: uploadError ? [] : [...new Set([...fileTexts.filter(t => FILE.test(t)), ...stagedFiles])], counters: texts.filter(t => COUNTER.test(t)), uploading, submit, submit_by_label: submitByLabel };
  };
  const busy = () => els.some(el => visible(el) && (el.getAttribute('role') === 'progressbar' || el.getAttribute('aria-busy') === 'true')) ||
    leaves(null).some(el => /^working on it\b/i.test(collapse(el.textContent)));
  const statusTexts = () => {
    const out = new Set();
    for (const el of els) {
      if (!el.matches('[role="status"],[role="alert"],[aria-live="polite"],[aria-live="assertive"]') || !visible(el)) continue;
      const t = collapse(el.innerText || el.textContent);
      if (t && t.length <= 200) out.add(t);
    }
    for (const el of leaves(null)) { const t = collapse(el.textContent); if (t.length <= 200 && STATUS.test(t)) out.add(t); }
    return [...out].slice(0, 30);
  };
  // Conversation area heuristic (to be confirmed by the first live transcript):
  // the visible log/conversation/messages container with the most text that does
  // not contain the composer, else the document body.
  const AREA = '[role="log"],[role="feed"],[data-testid*="conversation" i],[data-testid*="message-list" i],[data-testid*="messages" i],[class*="conversation" i],[class*="message-list" i],[class*="messages" i]';
  const MSG = '[data-testid*="message" i],[class*="message" i],[role="listitem"],[role="article"]';
  const LIST = '[data-testid*="messages" i],[data-testid*="message-list" i],[class*="messages" i],[class*="message-list" i]';
  const conv = () => {
    let best = null, len = -1;
    for (const el of els) {
      if (!el.matches(AREA) || !visible(el) || (comp && within(el, comp))) continue;
      const l = (el.innerText || '').length;
      if (l > len) { best = el; len = l; }
    }
    const area = best || document.body;
    const matches = els.filter(el => el !== area && within(area, el) && el.matches(MSG) && !el.matches(LIST) && visible(el));
    const msgs = matches.filter(el => !matches.some(o => o !== el && within(o, el))).map(el => ({ el, text: (el.innerText || '').trim() })).filter(m => m.text);
    const text = area.innerText || '';
    const blocks = text.split(/\n\s*\n/).filter(s => s.trim()).length;
    return { area, basis: best ? 'container' : 'body', msgs, text, message_count: msgs.length || blocks, message_detection: msgs.length ? 'structural' : 'text_blocks' };
  };
  const fileInputs = () => els.filter(el => el.tagName === 'INPUT' && el.type === 'file');
  // First-use tour: the innermost visible element whose short text holds
  // "Step N/M", outside the conversation, the messages and the composer. Its
  // nearest dialog, tooltip or popover ancestor is the tour container, unless
  // that ancestor also holds the composer or the conversation (then it is the
  // chat itself). Tour labels may be clicked only inside a unique container.
  const TOUR_BOX = '[role="dialog"],[role="alertdialog"],[aria-modal="true"],[role="tooltip"],[data-testid*="tour" i],[class*="tour" i],[class*="popover" i],[class*="coachmark" i]';
  const tourOf = c => {
    // Cheap gate: the per-element scan below runs only while "Step N/M" text
    // exists somewhere, so ordinary polling does not pay for it.
    if (!roots.some(r => detectTour((r.body || r).textContent || '').visible)) return { box: null, visible: false, text: null, reason: 'no_step_text' };
    const inChat = el => (c.basis === 'container' && within(c.area, el)) || c.msgs.some(m => within(m.el, el)) || (comp && within(comp, el));
    const steps = els.filter(el => !el.shadowRoot && visible(el) && collapse(el.textContent).length <= 60 && detectTour(collapse(el.textContent)).visible && !inChat(el));
    const inner = steps.filter(el => !steps.some(o => o !== el && within(el, o)));
    if (!inner.length) return { box: null, visible: false, text: null, reason: 'no_step_text' };
    const boxes = [];
    for (const el of inner) {
      for (let n = parentOf(el); n && n.nodeType === 1; n = parentOf(n)) {
        if (!n.matches(TOUR_BOX)) continue;
        if (!((comp && within(n, comp)) || (c.basis === 'container' && within(n, c.area))) && !boxes.includes(n)) boxes.push(n);
        break;
      }
    }
    const text = detectTour(collapse(inner[0].textContent)).text;
    if (boxes.length !== 1) return { box: null, visible: false, text, reason: boxes.length ? 'multiple_tour_containers' : 'no_tour_container' };
    const b = boxes[0];
    return { box: b, visible: true, text, reason: null, container: { tag: b.tagName, role: b.getAttribute('role'), testid: b.getAttribute('data-testid') } };
  };

  if (op === 'ready') return { url: location.href, ready: document.readyState };
  if (op === 'scan') {
    const c = conv();
    const files = fileInputs();
    const tour = tourOf(c);
    return {
      url: location.href, title: document.title, text: (document.body ? document.body.innerText : '').slice(0, 60000),
      composers: comps.map(el => ({ tag: el.tagName, label: composerLabel(el), value: valueOf(el).slice(0, 10000), disabled: disabledOf(el) || el.readOnly === true })),
      controls: all.slice(0, 300).map(x => ({ tag: x.tag, label: x.label.slice(0, 200), disabled: x.disabled, in_tour: Boolean(tour.box && within(tour.box, x.el)) })),
      tour: { visible: tour.visible, text: tour.text, reason: tour.reason, ...(tour.container ? { container: tour.container } : {}) },
      counters: leaves(null).map(el => collapse(el.textContent)).filter(t => COUNTER.test(t)).slice(0, 10),
      status: statusTexts(), busy: busy(),
      region: comp ? regionFacts(comp, c) : { chips: [], counters: [], uploading: false, submit: null, submit_by_label: null },
      file_inputs: { count: files.length, names: files.flatMap(el => [...(el.files || [])].map(f => f.name)) },
      name_field: (names => ({ count: names.length, value: names.length === 1 ? String(names[0].value ?? '') : null, disabled: names.length === 1 ? disabledOf(names[0]) || names[0].readOnly === true : null }))(nameFields()),
      conversation: { basis: c.basis, message_count: c.message_count, message_detection: c.message_detection },
    };
  }
  if (op === 'control') {
    // Submit is looked up only as the composer's own control, with the same rule
    // the controller applied to the scan.
    if (arg.composerSubmit) {
      if (!submitLabels.includes(arg.label)) fail('composer_submit_label', arg.label);
      if (!comp) fail('composer_count', String(comps.length));
      const list = submitsOf(comp, conv(), arg.label);
      const v = composerSubmitCheck({ disabled: disabledOf(comp) || comp.readOnly === true }, list.map(x => ({ disabled: x.disabled, in_region: x.in_region })));
      if (!v.ok) fail(v.reason, String(v.count ?? ''));
      return list[0].el;
    }
    if (arg.label === 'Approve' && arg.expectedTermsText) {
      const terms = pageAgent('terms', null, lib);
      if (terms.text !== arg.expectedTermsText) fail('terms_changed');
      const approvals = all.filter(x => x.label === 'Approve');
      return approvals[approvals.length - 1].el;
    }
    if (arg.label === 'Request changes' && arg.expectedTermsText) {
      const terms = pageAgent('terms', null, lib);
      if (terms.text !== arg.expectedTermsText) fail('terms_changed');
      const changes = all.filter(x => x.label === 'Request changes');
      if (changes.length !== all.filter(x => x.label === 'Approve').length) fail('request_changes_count', String(changes.length));
      return changes[changes.length - 1].el;
    }
    // Tour labels are matched only among the controls inside the tour container,
    // so the element returned here is the one the tour check approved.
    let pool = all;
    if (arg.tour) {
      const t = tourOf(conv());
      if (!t.visible) fail('tour_not_visible', t.reason || '');
      pool = all.filter(x => within(t.box, x.el));
    }
    const m = matchLabel(pool, arg.label);
    if (!m.ok) fail(`control_${m.reason}`, String(m.count));
    return pool[m.index].el;
  }
  if (op === 'composer') { if (!comp) fail('composer_count', String(comps.length)); return comp; }
  if (op === 'name-input') { const n = nameFields(); if (n.length !== 1) fail('name_field_count', String(n.length)); return n[0]; }
  if (op === 'file-input') { const f = fileInputs(); if (f.length !== 1) fail('file_input_count', String(f.length)); return f[0]; }
  if (op === 'terms') {
    // Terms heuristic: walk up from the unique Approve control. Prefer the nearest
    // dialog, card or message ancestor with visible text outside any control that
    // holds neither the composer nor the conversation area (basis "card"); else
    // the smallest ancestor with such text (basis "smallest_text"). Its innerText
    // is the terms text (it includes the button labels, which is stable).
    const approve = all.filter(c => c.label === 'Approve');
    if (!approve.length) fail('approve_count', '0');
    const CARD = '[role="dialog"],[role="alertdialog"],[aria-modal="true"],[role="article"],[role="listitem"],[role="group"],[role="region"],[data-testid*="card" i],[class*="card" i]';
    const c = conv();
    const ownText = n => {
      const walker = document.createTreeWalker(n, NodeFilter.SHOW_TEXT);
      let own = '';
      for (let t = walker.nextNode(); t; t = walker.nextNode()) {
        const p = t.parentElement;
        if (!p || !visible(p)) continue;
        const ctl = p.closest(CONTROL);
        if (ctl && within(n, ctl)) continue;
        own += ' ' + t.nodeValue;
      }
      return collapse(own);
    };
    const deepText = n => {
      const out = [];
      const walk = x => {
        if (x.nodeType === 3) { out.push(x.textContent || ''); return; }
        if (x.nodeType !== 1 && x.nodeType !== 11) return;
        if (x.nodeType === 1 && /^(?:SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(x.tagName)) return;
        if (x.nodeType === 1 && x.shadowRoot) walk(x.shadowRoot);
        for (const child of x.childNodes || []) walk(child);
      };
      walk(n);
      return collapse(out.join(' ')).slice(0, 20000);
    };
    const pack = (n, basis) => ({ text: approve.length > 1 ? deepText(n) : (n.innerText || n.textContent || '').slice(0, 20000), tag: n.tagName, role: n.getAttribute('role'), testid: n.getAttribute('data-testid'), basis });
    let smallest = null;
    for (let n = parentOf(approve[approve.length - 1].el); n && n.nodeType === 1; n = parentOf(n)) {
      const tooBroad = (comp && within(n, comp)) || (c.basis === 'container' && within(n, c.area));
      if (tooBroad || n === document.body) break;
      if (!ownText(n)) continue;
      if (!smallest) smallest = n;
      if (n.matches(CARD)) {
        const result = pack(n, 'card');
        if (approve.length === 1 || (result.text.includes('Issue summary') && result.text.includes('Attachments'))) return result;
      }
    }
    if (smallest && approve.length === 1) return pack(smallest, 'smallest_text');
    fail('terms_container_not_found');
  }
  if (op === 'deep_text') {
    // Read-only text of the whole frame, including open shadow roots, which
    // innerText skips. The 2026-09-30 email Issue summary rendered its fields
    // where neither the conversation area nor body.innerText reached them.
    const out = [];
    const BLOCK = /^(?:DIV|P|LI|UL|OL|H[1-6]|TR|TD|TH|SECTION|ARTICLE|HEADER|FOOTER|DT|DD|LABEL|BUTTON)$/;
    const walk = n => {
      if (out.length > 60000) return;
      if (n.nodeType === 3) { const t = n.textContent.replace(/\s+/g, ' '); if (t.trim()) out.push(t); return; }
      if (n.nodeType !== 1 && n.nodeType !== 11) return;
      if (n.nodeType === 1) {
        if (/^(?:SCRIPT|STYLE|NOSCRIPT|TEMPLATE)$/.test(n.tagName)) return;
        const cs = getComputedStyle(n);
        if (cs.display === 'none' || cs.visibility === 'hidden') return;
        if (n.tagName === 'BR') { out.push('\n'); return; }
        if (n.shadowRoot) walk(n.shadowRoot);
      }
      for (const c of n.childNodes) walk(c);
      if (n.nodeType === 1 && BLOCK.test(n.tagName)) out.push('\n');
    };
    walk(document.body || document.documentElement);
    return { text: out.join('').replace(/[ \t]+\n/g, '\n').replace(/\n[ \t]+/g, '\n').replace(/\n{3,}/g, '\n\n').slice(0, 200000) };
  }
  if (op === 'conversation') {
    const c = conv();
    const depthOf = el => { let d = 0; for (let n = el; n && n !== c.area; n = parentOf(n)) d++; return d; };
    const outline = els.filter(el => el !== c.area && within(c.area, el) && (el.getAttribute('role') || el.getAttribute('aria-label') || el.getAttribute('data-testid')))
      .slice(0, 400).map(el => ({ depth: depthOf(el), tag: el.tagName, role: el.getAttribute('role'), aria_label: (el.getAttribute('aria-label') || '').slice(0, 120) || null, testid: el.getAttribute('data-testid') }));
    return {
      basis: c.basis, text: c.text.slice(0, 200000), message_count: c.message_count, message_detection: c.message_detection,
      messages: c.msgs.slice(-300).map(m => ({ text: m.text.slice(0, 4000), role: m.el.getAttribute('role'), aria_label: m.el.getAttribute('aria-label'), testid: m.el.getAttribute('data-testid') })),
      outline, busy: busy(), status: statusTexts(),
      // The whole frame text as read-only backup: on the 2026-09-30 full page the
      // chosen area held only the seller's own message, not the assistant reply.
      page_text: (document.body?.innerText || '').slice(0, 200000),
    };
  }
  if (op === 'occurrences') {
    // Whitespace-collapsed occurrence count in the conversation area. A
    // contenteditable composer inside that area is subtracted.
    const c = conv();
    const needle = collapse(arg.text), prefix = needle.slice(0, 120);
    const count = (hay, n) => { if (!n) return 0; let k = 0, i = 0; while ((i = hay.indexOf(n, i)) !== -1) { k++; i += n.length; } return k; };
    const hay = collapse(c.text);
    const own = comp && comp.tagName !== 'TEXTAREA' && within(c.area, comp) ? collapse(valueOf(comp)) : '';
    return { full: count(hay, needle) - count(own, needle), prefix: count(hay, prefix) - count(own, prefix), composer_value: comp ? valueOf(comp) : null, message_count: c.message_count };
  }
  fail('unknown_op', op);
}

export function pageExpression(op, arg = null) {
  return `/*ew-sa:${op}*/(() => { const collapse = ${collapse}; const matchLabel = ${matchLabel}; const detectTour = ${detectTour}; const composerSubmitCheck = ${composerSubmitCheck}; return (${pageAgent})(${JSON.stringify(op)}, ${JSON.stringify(arg)}, { collapse, matchLabel, detectTour, composerSubmitCheck, submitLabels: ${JSON.stringify(SUBMIT_LABELS)}, uploadLabels: ${JSON.stringify(UPLOAD_LABELS)} }); })()`;
}

const HIT_TEST_FN = 'function(hit){for(let n=hit;n;n=(n.parentNode&&n.parentNode.nodeType===11)?n.parentNode.host:n.parentNode){if(n===this)return true;}return false;}';
const FOCUS_FN = 'function(){this.focus();let a=this.ownerDocument.activeElement;while(a&&a.shadowRoot&&a.shadowRoot.activeElement)a=a.shadowRoot.activeElement;return{focused:a===this,has_focus:this.ownerDocument.hasFocus()};}';
// Focus and select the whole value, so the inserted text replaces Amazon's prefill.
const FOCUS_SELECT_FN = 'function(){this.focus();if(typeof this.select==="function")this.select();let a=this.ownerDocument.activeElement;while(a&&a.shadowRoot&&a.shadowRoot.activeElement)a=a.shadowRoot.activeElement;const n=String(this.value??"").length;return{focused:a===this,selected:n===0||(this.selectionStart===0&&this.selectionEnd===n)};}';

const originOf = url => { try { return new URL(url).origin; } catch { return 'null'; } };

/** The one upload control of a frame: Upload file (Seller Assistant) or Attach
 * (case chat window). Both present is ambiguous. */
export function uploadControl(controls) {
  const found = UPLOAD_LABELS.map(label => matchLabel(controls, label));
  const ok = found.filter(m => m.ok);
  if (ok.length === 1) return ok[0];
  return ok.length ? { ok: false, reason: 'ambiguous', count: ok.length } : found[0];
}

/** Combine per-frame scan data into one state object. Pure; tested directly. */
export function assembleState(frames, data) {
  const list = frames.map(f => ({ ...f, reachable: f.same_origin ? Boolean(data[f.frame_id]) : false, composer_count: data[f.frame_id]?.composers?.length ?? 0 }));
  const selection = selectComposerFrame(list);
  const main = list[0] || {};
  const controls = [];
  for (const f of list) for (const c of data[f.frame_id]?.controls || []) controls.push({ ...c, frame_id: f.frame_id });
  const texts = list.map(f => data[f.frame_id]?.text || '').join('\n');
  // A tour counts only when exactly one frame reports a unique tour container.
  const tours = list.filter(f => data[f.frame_id]?.tour?.visible === true);
  const tourReason = tours.length > 1 ? 'multiple_tour_frames' : (list.map(f => data[f.frame_id]?.tour?.reason).find(r => r && r !== 'no_step_text') || 'no_step_text');
  const tour = tours.length === 1
    ? { visible: true, text: data[tours[0].frame_id].tour.text, frame_id: tours[0].frame_id, container: data[tours[0].frame_id].tour.container ?? null }
    : { visible: false, text: null, reason: tourReason };
  const selected = selection.ok ? data[selection.frame_id] : null;
  const raw = selected?.composers?.[0];
  const normalized = raw ? normalizeComposer(raw.value) : '';
  const frameControls = selection.ok ? controls.filter(c => c.frame_id === selection.frame_id) : [];
  const approve = controls.filter(c => collapse(c.label) === 'Approve');
  const conversationSource = selected || data[main.frame_id];
  const urls = [main.url, ...list.map(f => f.url)];
  const conversationUrl = urls.find(u => /\/assistant\/amzn1\.cyrano\.conversation\./.test(u || '')) || null;
  return {
    url: main.url || null, title: data[main.frame_id]?.title ?? null, conversation_url: conversationUrl,
    frames: list.map(f => ({ frame_id: f.frame_id, parent_id: f.parent_id ?? null, url: f.url, origin: f.origin, same_origin: f.same_origin, reachable: f.reachable, composer_count: f.composer_count, ...(f.error ? { error: f.error } : {}) })),
    selection,
    composer: raw ? { frame_id: selection.frame_id, tag: raw.tag, label: raw.label, value: raw.value, length: normalized.length, sha256: sha256(normalized), disabled: raw.disabled === true,
      counter_text: selected.region?.counters?.[0] ?? selected.counters?.[0] ?? null, submit_controls: Array.isArray(selected.region?.submit) ? selected.region.submit : null,
      submit_by_label: selected.region?.submit_by_label ?? null } : null,
    name_field: selected?.name_field ?? null,
    controls: controls.slice(0, 300),
    status_texts: [...new Set(list.flatMap(f => data[f.frame_id]?.status || []))],
    busy: list.some(f => data[f.frame_id]?.busy === true),
    tour,
    denial: detectDenial(texts),
    handoff: { approve_count: approve.length, approve_enabled: matchLabel(controls, 'Approve').ok, terms_text: null, terms_sha256: null },
    attachments: {
      upload_present: frameControls.some(c => UPLOAD_LABELS.includes(collapse(c.label))), upload_enabled: uploadControl(frameControls).ok,
      submit_enabled: matchLabel(frameControls, 'Submit').ok, chips: selected?.region?.chips || [], uploading: selected?.region?.uploading === true,
      file_input_count: selected?.file_inputs?.count ?? 0, input_files: selected?.file_inputs?.names || [],
    },
    message_count: conversationSource?.conversation?.message_count ?? 0,
    message_detection: conversationSource?.conversation?.message_detection ?? null,
  };
}

function pageError(details) {
  const text = details?.exception?.description || details?.text || 'page evaluation failed';
  const match = /EW:([a-z_]+):([^\n]*)/.exec(text);
  return match ? codeError(match[1], `${match[1]} ${match[2]}`.trim(), { detail: match[2] }) : codeError('page_error', text.slice(0, 300));
}

/** Frame-aware browser primitives over one CDP session (all calls go through
 * session.send, which applies the task-control guard). */
export function makeBrowser({ send, listPageTargets = async () => [], sleep = ms => new Promise(r => setTimeout(r, ms)), now = Date.now }, scOrigin) {
  const GROUP = 'ew-seller-assistant';
  // One isolated world per frame document, reused across evaluations: every
  // Page.createIsolatedWorld call makes a new world that lives until the frame
  // navigates, and the assistant is a single-page app polled for up to 90 minutes.
  // A cached world is dropped when the frame's loaderId changes, when the frame
  // disappears, or when Chromium reports the context gone (then one retry).
  const worlds = new Map(), loaders = new Map();
  const STALE_CONTEXT = /Cannot find (?:context|execution context)|context was destroyed|Execution context was destroyed/i;
  async function frames() {
    const { frameTree } = await send('Page.getFrameTree', {});
    const out = [];
    const walk = (node, parent) => {
      const f = node.frame;
      const url = f.url + (f.urlFragment || '');
      const origin = f.securityOrigin && f.securityOrigin !== '://' ? f.securityOrigin : originOf(f.url);
      out.push({ frame_id: f.id, parent_id: parent, url, origin, same_origin: origin === scOrigin });
      loaders.set(f.id, f.loaderId ?? null);
      for (const child of node.childFrames || []) walk(child, f.id);
    };
    walk(frameTree, null);
    const live = new Set(out.map(f => f.frame_id));
    for (const id of [...worlds.keys()]) if (!live.has(id)) worlds.delete(id);
    for (const id of [...loaders.keys()]) if (!live.has(id)) loaders.delete(id);
    return out;
  }
  async function world(frameId) {
    const loaderId = loaders.get(frameId) ?? null;
    const cached = worlds.get(frameId);
    if (cached && cached.loaderId === loaderId) return cached.contextId;
    const { executionContextId } = await send('Page.createIsolatedWorld', { frameId, worldName: GROUP });
    worlds.set(frameId, { contextId: executionContextId, loaderId });
    return executionContextId;
  }
  async function run(frameId, op, arg = null, { byValue = true, timeoutMs = 20000 } = {}) {
    // Isolated world: page scripts cannot observe or alter the driver's
    // functions, while the DOM (including open shadow roots) is shared.
    for (let attempt = 0; ; attempt++) {
      const contextId = await world(frameId);
      let response;
      try {
        response = await send('Runtime.evaluate', { expression: pageExpression(op, arg), contextId,
          returnByValue: byValue, awaitPromise: true, objectGroup: GROUP, timeout: timeoutMs }, { timeoutMs: timeoutMs + 5000 });
      } catch (error) {
        if (!isFatal(error) && attempt === 0 && STALE_CONTEXT.test(String(error?.message || ''))) { worlds.delete(frameId); continue; }
        throw error;
      }
      if (response.exceptionDetails) throw pageError(response.exceptionDetails);
      if (byValue) return response.result?.value;
      if (!response.result?.objectId) throw codeError('element_unavailable', `${op} returned no element`);
      return { objectId: response.result.objectId, contextId };
    }
  }
  // Locate and hit-test a control without dispatching any input.
  async function locate({ objectId, contextId }) {
    await send('Page.bringToFront', {});
    await send('DOM.scrollIntoViewIfNeeded', { objectId });
    // DOM.getContentQuads reports CSS pixels relative to the root (main frame)
    // viewport, also for nodes inside same-process iframes; Chromium converts
    // frame coordinates to the root frame, and Puppeteer adds offsets only for
    // out-of-process iframes. Input.dispatchMouseEvent takes the same main-frame
    // viewport coordinates. Only same-origin (same-process) frames are driven, so
    // no frame offset is added. The hit test below verifies this at run time: the
    // node at the click point must be the control or inside it, otherwise stop.
    const { quads } = await send('DOM.getContentQuads', { objectId });
    if (!quads?.length) throw codeError('click_no_quads', 'control has no layout box');
    const q = quads[0];
    const x = Math.round((q[0] + q[2] + q[4] + q[6]) / 4), y = Math.round((q[1] + q[3] + q[5] + q[7]) / 4);
    // DOM.getNodeForLocation reads its point as main-document coordinates
    // (Blink converts with DocumentToFrame), while the quad and the mouse events
    // use viewport coordinates. Add the main frame's layout-viewport scroll so a
    // scrolled page still hit-tests the click point. To be confirmed on the
    // read-only smoke run; a wrong offset fails closed as click_target_obscured.
    let scroll = { x: 0, y: 0 };
    try {
      const metrics = await send('Page.getLayoutMetrics', {});
      const view = metrics?.cssLayoutViewport || metrics?.layoutViewport || {};
      scroll = { x: Number(view.pageX) || 0, y: Number(view.pageY) || 0 };
    } catch (error) { if (isFatal(error)) throw error; }
    let inside = false;
    try {
      const hit = await send('DOM.getNodeForLocation', { x: x + scroll.x, y: y + scroll.y, includeUserAgentShadowDOM: true, ignorePointerEventsNone: false });
      const resolved = await send('DOM.resolveNode', { backendNodeId: hit.backendNodeId, executionContextId: contextId, objectGroup: GROUP });
      const answer = await send('Runtime.callFunctionOn', { objectId, functionDeclaration: HIT_TEST_FN, arguments: [{ objectId: resolved.object.objectId }], returnByValue: true });
      inside = answer.result?.value === true;
    } catch (error) { if (isFatal(error)) throw error; inside = false; }
    if (!inside) throw codeError('click_target_obscured', 'another element covers the control');
    return { x, y, scroll };
  }
  async function dispatch({ x, y }) {
    for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased']) {
      await send('Input.dispatchMouseEvent', { type, x, y, button: type === 'mouseMoved' ? 'none' : 'left', clickCount: type === 'mouseMoved' ? 0 : 1 });
    }
  }
  const api = {
    frames,
    async scan() {
      const list = await frames();
      const data = {};
      for (const f of list) {
        if (!f.same_origin) continue;
        try { data[f.frame_id] = await run(f.frame_id, 'scan'); }
        catch (error) { if (isFatal(error)) throw error; f.error = String(error.message).slice(0, 200); }
      }
      const state = assembleState(list, data);
      const approveFrames = [...new Set(state.controls.filter(c => collapse(c.label) === 'Approve').map(c => c.frame_id))];
      if (approveFrames.length === 1) {
        const frameId = approveFrames[0];
        try {
          const terms = await run(frameId, 'terms');
          Object.assign(state.handoff, { frame_id: frameId, terms_text: terms.text, terms_sha256: termsHash(terms.text), terms_container: { tag: terms.tag, role: terms.role, testid: terms.testid, basis: terms.basis } });
        } catch (error) { if (isFatal(error)) throw error; state.handoff.terms_error = error.code || error.message; }
      }
      return state;
    },
    async terms(frameId) { const t = await run(frameId, 'terms'); return { ...t, sha256: termsHash(t.text) }; },
    async prepareClick(frameId, label, { tour = false, composerSubmit = false, expectedTermsText = null } = {}) { return locate(await run(frameId, 'control', { label, tour, composerSubmit, expectedTermsText }, { byValue: false })); },
    dispatchClick: dispatch,
    async insertText(frameId, text) {
      const { objectId } = await run(frameId, 'composer', null, { byValue: false });
      await send('Page.bringToFront', {});
      const focus = await send('Runtime.callFunctionOn', { objectId, functionDeclaration: FOCUS_FN, returnByValue: true });
      if (focus.result?.value?.focused !== true) throw codeError('composer_focus_failed', 'composer did not take focus');
      await send('Input.insertText', { text });
      return focus.result.value;
    },
    async fillName(frameId, text) {
      const { objectId } = await run(frameId, 'name-input', null, { byValue: false });
      await send('Page.bringToFront', {});
      const focus = await send('Runtime.callFunctionOn', { objectId, functionDeclaration: FOCUS_SELECT_FN, returnByValue: true });
      if (focus.result?.value?.focused !== true || focus.result?.value?.selected !== true) throw codeError('name_focus_failed', 'name field did not take focus with its value selected');
      await send('Input.insertText', { text });
    },
    prepareFileInput: frameId => run(frameId, 'file-input', null, { byValue: false }),
    async setFile({ objectId }, path) { await send('DOM.setFileInputFiles', { files: [path], objectId }); },
    occurrences: (frameId, text) => run(frameId, 'occurrences', { text }),
    conversation: frameId => run(frameId, 'conversation', null, { timeoutMs: 30000 }),
    deepText: frameId => run(frameId, 'deep_text', null, { timeoutMs: 30000 }),
    async navigate(url) {
      const answer = await send('Page.navigate', { url }, { timeoutMs: 30000 });
      if (answer?.errorText) throw codeError('navigation_failed', answer.errorText);
      await sleep(1000);
      const end = now() + 30000;
      while (now() < end) {
        try {
          const main = (await frames())[0];
          const ready = await run(main.frame_id, 'ready');
          if (ready.ready === 'complete' && ready.url !== 'about:blank') return ready;
        } catch (error) { if (isFatal(error)) throw error; }
        await sleep(500);
      }
      throw codeError('navigation_timeout', `page did not finish loading: ${url}`);
    },
    async targets() {
      try {
        const { targetInfos } = await send('Target.getTargets', {});
        return targetInfos.filter(t => t.type === 'page').map(t => t.targetId);
      } catch (error) {
        if (isFatal(error)) throw error;
        return (await listPageTargets()).map(p => p.id);
      }
    },
    // Page targets with their URL and opener. The /json/list fallback has no
    // opener, so a popup found that way never passes the opener check.
    async targetInfos() {
      try {
        const { targetInfos } = await send('Target.getTargets', {});
        return targetInfos.filter(t => t.type === 'page').map(t => ({ targetId: t.targetId, type: t.type, url: t.url, openerId: t.openerId ?? null }));
      } catch (error) {
        if (isFatal(error)) throw error;
        return (await listPageTargets()).map(p => ({ targetId: p.id, type: p.type || 'page', url: p.url, openerId: null }));
      }
    },
    async release() { await send('Runtime.releaseObjectGroup', { objectGroup: GROUP }).catch(() => {}); },
  };
  return api;
}

// ------------------------------------------------------------------- handlers

const iso = ms => new Date(ms).toISOString();
async function atomicWrite(path, text) {
  const tmp = `${path}.tmp-${process.pid}`;
  await writeFile(tmp, text);
  await rename(tmp, path);
}
const pad = (n, width = 2) => String(n).padStart(width, '0');
const stepNumber = id => pad(Number(id));

// Every approvals.jsonl line carries the queue id of the command that wrote it,
// so a restarted serve can pair each attempt with its result.
async function logApproval(rt, entry) {
  await appendFile(join(rt.runDir, 'approvals.jsonl'), JSON.stringify({ at: iso(rt.deps.now()), queue_id: rt.current?.id ?? null, ...entry }) + '\n');
  if (entry.phase === 'result' && rt.dispatch) rt.dispatch.logged = true;
}

/** Record that an outbound action (Submit, Approve click or file upload) is being
 * dispatched. From here on no failure may read as "not sent". */
function markDispatched(rt, command, sha, kind) { rt.dispatch = { command, sha256: sha, kind, logged: false }; }

/** The signal and crash handler sets rt.aborting before its first await. From
 * then on no click, insert or upload may start; this throws a non-dispatch error. */
function assertNotAborting(rt) {
  if (rt.aborting) throw codeError('aborting', 'serve is shutting down; nothing was dispatched');
}

/** Write the attempt line for an outbound action. The abort flag is checked
 * before and after the write; the caller dispatches in the same tick as the
 * return, so an interrupt during the write still stops the action. An attempt
 * stopped this way gets a `blocked` result line. */
async function logAttempt(rt, entry) {
  assertNotAborting(rt);
  await logApproval(rt, { phase: 'attempt', ...entry });
  if (rt.aborting) {
    await logApproval(rt, { phase: 'result', command: entry.command, sha256: entry.sha256, status: 'blocked', reason: 'aborting' }).catch(() => {});
    assertNotAborting(rt);
  }
}

/** Result for any failure after an outbound dispatch: always uncertain, never a
 * plain error, with a result line in approvals.jsonl when one can be written. */
async function dispatchedFailure(rt, error) {
  const d = rt.dispatch;
  const reason = isFatal(error) ? 'control_lost' : (error?.code || 'confirmation_failed');
  if (isFatal(error)) rt.fatal = true;
  let logError = null;
  if (!d.logged) {
    try { await logApproval(rt, { phase: 'result', command: d.command, sha256: d.sha256, status: 'uncertain', reason }); }
    catch (e) { logError = String(e?.message || e).slice(0, 200); }
  }
  return { status: 'uncertain', [d.kind]: true, reason, sha256: d.sha256, message: String(error?.message || error).slice(0, 300), ...(logError ? { log_error: logError } : {}) };
}

/** Click one exact label. Errors before dispatch mean nothing was clicked;
 * errors during or after dispatch carry `dispatched: true`. `beforeDispatch`
 * runs after the control is located and hit-tested, right before the mouse
 * events. With `popup` (a check over one target's info) the click is expected to
 * open exactly one new window that passes the check; it is returned as `popup`
 * instead of halting the run. Any other new target halts the run as always. */
async function guardedClick(rt, frameId, label, beforeDispatch = null, { tour = false, composerSubmit = false, expectedTermsText = null, popup = null } = {}) {
  const before = new Set(await rt.browser.targets());
  const point = await rt.browser.prepareClick(frameId, label, { tour, composerSubmit, expectedTermsText });
  // Without beforeDispatch this check runs in the same tick as the dispatch.
  assertNotAborting(rt);
  if (beforeDispatch) await beforeDispatch();
  try {
    await rt.browser.dispatchClick(point);
    await rt.deps.sleep(1000);
    if (popup) {
      // A new window may report about:blank until its first navigation commits.
      const seen = await waitUntil(rt, async () => (await rt.browser.targetInfos()).filter(t => !before.has(t.targetId)),
        list => list.length > 0 && list.every(t => t.url && t.url !== 'about:blank'), 15000, 500);
      const created = seen.value;
      const verdict = created.length === 1 ? popup(created[0]) : { ok: false, reason: created.length ? 'multiple_new_targets' : 'chat_window_missing' };
      if (verdict.ok) return { point, new_targets: [], popup: created[0] };
      rt.lockout = created.length ? { reason: 'new_target', targets: created.map(t => t.targetId), check: verdict.reason } : { reason: 'chat_window_missing' };
      return { point, new_targets: created.map(t => t.targetId), popup: null, popup_reason: verdict.reason };
    }
    const created = (await rt.browser.targets()).filter(id => !before.has(id));
    if (created.length) rt.lockout = { reason: 'new_target', targets: created };
    return { point, new_targets: created };
  } catch (error) { error.dispatched = true; throw error; }
}

function allControlsMatch(state, label) {
  const same = state.controls.filter(c => state.frames.find(f => f.frame_id === c.frame_id)?.same_origin);
  return matchLabel(same, label);
}

async function waitUntil(rt, probe, done, timeoutMs, intervalMs = 1000) {
  const end = rt.deps.now() + timeoutMs;
  let value = await probe();
  while (!done(value) && rt.deps.now() < end) { await rt.deps.sleep(intervalMs); value = await probe(); }
  return { value, satisfied: done(value) };
}

function sameSet(a, b) {
  const x = [...new Set(a)].sort(), y = [...new Set(b)].sort();
  return x.length === y.length && x.every((v, i) => v === y[i]);
}

/** Everything that must hold before Submit (or Send, or Chat now: `label`) is
 * clicked. Returns { blocked } or the frame and composer facts. `approvedNames`
 * are the files this run logged as attached. */
function submitBlocker(state, expected, expectedFiles, approvedNames, frameId = null, label = 'Submit') {
  if (!state.selection.ok) return { blocked: { status: 'blocked', reason: state.selection.reason, details: state.selection.details } };
  if (frameId && state.selection.frame_id !== frameId) return { blocked: { status: 'blocked', reason: 'composer_frame_changed' } };
  if (state.busy) return { blocked: { status: 'blocked', reason: 'assistant_busy' } };
  if (state.composer.disabled) return { blocked: { status: 'blocked', reason: 'composer_disabled' } };
  const composer = checkComposer(state.composer.value, expected);
  if (!composer.ok) return { blocked: { status: 'refused', reason: composer.reason, composer_sha256: composer.sha256, composer_length: composer.length } };
  const files = attachmentCheck(state.attachments, expectedFiles, approvedNames);
  if (!files.ok) return { blocked: { status: 'refused', ...files, chips: state.attachments.chips, input_files: state.attachments.input_files, expected: expectedFiles } };
  if (state.attachments.uploading) return { blocked: { status: 'blocked', reason: 'upload_in_progress' } };
  const frame = state.selection.frame_id;
  const submit = matchLabel(state.controls.filter(c => c.frame_id === frame), label);
  if (!submit.ok) return { blocked: { status: 'blocked', reason: `control_${submit.reason}` } };
  const scoped = label === 'Submit' ? state.composer.submit_controls : (state.composer.submit_by_label?.[label] ?? null);
  const scope = composerSubmitCheck(state.composer, scoped);
  if (!scope.ok) return { blocked: { status: 'blocked', reason: scope.reason, ...(scope.count !== undefined ? { count: scope.count } : {}) } };
  return { frameId: frame, composer };
}

const approvalContext = rt => ({ runId: rt.config?.run_id, sellerId: rt.config?.account?.seller_id, now: rt.deps.now(),
  ...(rt.config?.registry_id ? { instruction: rt.config.authorization.source.instruction } : {}) });

/** A run bound to a case registry row asks the case service before every
 * outbound action; any refusal stops it before its attempt line is written.
 * Returns null when the action may go ahead. */
async function claimBeforeClick(rt) {
  if (!rt.config?.registry_id) return null;
  let verdict;
  try { verdict = await rt.deps.claimAttended(claimRequest(rt.config)); }
  catch (error) { verdict = { ok: false, reason: 'claim_unavailable', message: String(error?.message || error).slice(0, 300) }; }
  if (verdict?.ok === true) return null;
  return { status: 'refused', reason: 'claim_refused', claim_reason: verdict?.reason || 'claim_refused', ...(verdict?.message ? { message: verdict.message } : {}), stage: 'pre_click' };
}

function usageCount(rt, key) { return rt.counts.get(key) || 0; }
function bumpUsage(rt, key) { rt.counts.set(key, usageCount(rt, key) + 1); }

async function reverify(rt) {
  try { return await rt.deps.verifyIdentity(); }
  catch (error) {
    if (isFatal(error)) throw error;
    rt.lockout = { reason: 'identity_mismatch' };
    throw codeError('identity_mismatch', error.message);
  }
}

async function clickFailure(rt, error) {
  if (!error.dispatched) {
    // Nothing was clicked: the attempt line (if any) stays unmatched only when
    // beforeDispatch ran, which it does right before the click.
    if (rt.dispatch && !rt.dispatch.logged) return dispatchedFailure(rt, error);
    if (isFatal(error)) throw error;
    return { status: 'blocked', reason: error.code || 'click_not_prepared', message: String(error.message).slice(0, 300), clicked: false };
  }
  if (!error.code) error.code = 'click_failed';
  return dispatchedFailure(rt, error);
}

/** Chat now on a case reply form. The driver fills "Your name" with the run's
 * signature_name and the composer with CHAT_OPENING_LINE, both shown in the
 * operator's draft; the approval file is the one for the message this chat
 * delivers. After the click it adopts the one case chat window Amazon opens,
 * drives that window from then on and confirms the opening line there. */
async function chatNow(rt, args, approval) {
  const expected = args['expect-sha256'], key = `chat_now:${expected}`;
  if (usageCount(rt, key) >= 1) return { status: 'refused', reason: 'send_limit_reached', limit: 1 };
  if (rt.chat) return { status: 'refused', reason: 'case_chat_open' };
  if ((args['expect-attachment'] || []).length) return { status: 'refused', reason: 'chat_now_takes_no_attachment' };
  const name = rt.config?.signature_name;
  if (!name) return { status: 'refused', reason: 'signature_name_missing' };
  if (!rt.caseId) return { status: 'refused', reason: 'case_not_opened' };
  const opening = sha256(CHAT_OPENING_LINE);
  const onCase = s => isCaseViewPage(s.url, rt.caseId) && originOf(s.url) === rt.origin;
  const nameCount = s => (s.name_field?.count === 1 ? null : { status: 'blocked', reason: 'name_field_count', count: s.name_field?.count ?? 0 });
  const idle = await waitUntil(rt, () => rt.browser.scan(), s => !s.busy, 30000);
  if (!idle.satisfied) return { status: 'blocked', reason: 'assistant_busy' };
  const state = idle.value;
  if (!onCase(state)) return { status: 'refused', reason: 'not_on_case_page' };
  if (!state.selection.ok) return { status: 'blocked', reason: state.selection.reason, details: state.selection.details };
  const frameId = state.selection.frame_id;
  const count = nameCount(state);
  if (count) return count;
  if (state.name_field.disabled) return { status: 'blocked', reason: 'name_field_disabled' };
  if (state.composer.disabled) return { status: 'blocked', reason: 'composer_disabled' };
  const typed = normalizeComposer(state.composer.value);
  if (typed !== '' && typed !== CHAT_OPENING_LINE) return { status: 'refused', reason: 'composer_not_empty', composer_sha256: state.composer.sha256 };
  // Typing sends nothing; each field is written only when it is not already exact.
  if (state.name_field.value !== name) { assertNotAborting(rt); await rt.browser.fillName(frameId, name); }
  if (typed === '') { assertNotAborting(rt); await rt.browser.insertText(frameId, CHAT_OPENING_LINE); }
  const filled = await waitUntil(rt, () => rt.browser.scan(),
    s => s.name_field?.value === name && s.composer && normalizeComposer(s.composer.value) === CHAT_OPENING_LINE, 5000, 500);
  if (!filled.satisfied) return { status: 'error', reason: 'chat_form_readback_mismatch', name_matches: filled.value.name_field?.value === name, composer_sha256: filled.value.composer?.sha256 ?? null };
  const formBlocker = s => {
    if (!onCase(s)) return { status: 'refused', reason: 'not_on_case_page' };
    const n = nameCount(s);
    if (n) return n;
    if (s.name_field.value !== name) return { status: 'refused', reason: 'name_field_changed' };
    return submitBlocker(s, opening, [], [], frameId, 'Chat now').blocked || null;
  };
  const first = formBlocker(filled.value);
  if (first) return first;
  const identity = await reverify(rt);
  // Everything checked above is checked again after the identity read.
  const again = formBlocker(await rt.browser.scan());
  if (again) return { ...again, stage: 'pre_click' };
  const claim = await claimBeforeClick(rt);
  if (claim) return claim;
  let click;
  try {
    click = await guardedClick(rt, frameId, 'Chat now', async () => {
      await logAttempt(rt, { command: 'chat_now', sha256: expected, plan_item: approval.plan_item, label: approval.label ?? null, submit_label: 'Chat now', approval_file: args['approval-file'], approval, identity,
        case_id: rt.caseId, opening_line: CHAT_OPENING_LINE, opening_line_sha256: opening, name });
      bumpUsage(rt, key);
      markDispatched(rt, 'chat_now', expected, 'clicked');
    }, { composerSubmit: true, popup: info => isCaseChatTarget(info, { origin: rt.origin, caseId: rt.caseId, openerId: rt.taskTargetId }) });
  } catch (error) { return clickFailure(rt, error); }
  try {
    let result;
    if (!click.popup) {
      // guardedClick has set the lockout: the run halts after this result.
      result = { status: 'uncertain', clicked: true, reason: click.popup_reason || 'chat_window_missing', new_targets: click.new_targets };
    } else {
      const chat = await rt.deps.adoptChat(click.popup);
      Object.assign(rt, { chat, browser: chat.browser, baseline: null });
      // The chat shows the opening line as the issue ("Issue: Hello." on 2026-10-01).
      const shown = await waitUntil(rt, async () => {
        const s = await rt.browser.scan();
        const frame = s.selection.ok ? s.selection.frame_id : s.frames[0]?.frame_id;
        return frame ? rt.browser.occurrences(frame, CHAT_OPENING_LINE) : { full: 0 };
      }, o => o.full >= 1, 30000);
      result = { status: shown.satisfied ? 'sent' : 'uncertain', clicked: true, ...(shown.satisfied ? {} : { reason: 'opening_line_not_confirmed' }),
        chat: { target_id: click.popup.targetId, url: click.popup.url, slot: CHAT_SLOT } };
    }
    Object.assign(result, { sha256: expected, plan_item: approval.plan_item, submit_label: 'Chat now', case_id: rt.caseId, opening_line_sha256: opening });
    await logApproval(rt, { phase: 'result', command: 'chat_now', sha256: expected, status: result.status, delivery: result.status, reason: result.reason ?? null });
    return result;
  } catch (error) {
    if (!rt.chat) rt.lockout ??= { reason: 'chat_adoption_failed' };
    return dispatchedFailure(rt, error);
  }
}

export const handlers = {
  async state(rt) { return { status: 'ok', state: await rt.browser.scan() }; },

  async open(rt, args) {
    // After Chat now the controller drives the chat window; navigating it away
    // would leave the case chat.
    if (rt.chat) return { status: 'refused', reason: 'case_chat_open' };
    if (args.case) {
      if (args['via-lobby'] || args.conversation) return { status: 'refused', reason: 'case_with_other_target' };
      assertNotAborting(rt);
      rt.caseId = null;
      const url = `${rt.origin}${CASE_VIEW_PATH}?caseID=${encodeURIComponent(args.case)}`;
      await rt.browser.navigate(url);
      const reply = s => s.controls.some(c => collapse(c.label) === REPLY_LABEL);
      const ready = await waitUntil(rt, () => rt.browser.scan(), s => isCaseViewPage(s.url, args.case) && reply(s), 20000);
      const state = ready.value;
      const onCase = isCaseViewPage(state.url, args.case) && originOf(state.url) === rt.origin;
      if (!onCase) return { status: 'blocked', reason: 'case_page_not_reached', via: 'case', state };
      rt.caseId = args.case;
      return { status: 'ok', via: 'case', case_id: args.case, reply_present: reply(state), state };
    }
    rt.caseId = null;
    assertNotAborting(rt);
    await rt.browser.navigate(rt.origin + LOBBY_PATH);
    const lobbyWait = await waitUntil(rt, () => rt.browser.scan(),
      s => s.controls.some(c => ['Get help with a new issue', 'Ask Seller Assistant'].includes(collapse(c.label))), 20000);
    const lobbyState = lobbyWait.value;
    const lobby = { url: lobbyState.url, labels: lobbyState.controls.map(c => c.label).filter(Boolean).slice(0, 120),
      get_help_present: lobbyState.controls.some(c => collapse(c.label) === 'Get help with a new issue'),
      ask_present: lobbyState.controls.some(c => collapse(c.label) === 'Ask Seller Assistant') };
    let via = 'url';
    if (args['via-lobby'] && args.conversation) return { status: 'refused', reason: 'via_lobby_with_conversation', lobby };
    if (args.conversation) {
      assertNotAborting(rt);
      await rt.browser.navigate(rt.origin + args.conversation);
      via = 'conversation';
    } else if (args['via-lobby']) {
      const match = allControlsMatch(lobbyState, 'Get help with a new issue');
      if (!match.ok) return { status: 'blocked', reason: `control_${match.reason}`, lobby };
      const click = await guardedClick(rt, match.control.frame_id, 'Get help with a new issue');
      if (click.new_targets.length) return { status: 'blocked', reason: 'new_target', lobby, new_targets: click.new_targets };
      via = 'lobby';
    } else {
      assertNotAborting(rt);
      await rt.browser.navigate(rt.origin + ASSISTANT_PATH);
    }
    const assistantPage = s => /^\/assistant(?:\/|$)/.test(new URL(s.url || rt.origin).pathname);
    const ready = await waitUntil(rt, () => rt.browser.scan(), s => assistantPage(s) && (s.selection.ok || s.denial.detected), 30000);
    const state = ready.value;
    const onAssistant = assistantPage(state);
    return { status: onAssistant ? 'ok' : 'blocked', ...(onAssistant ? {} : { reason: 'assistant_not_reached' }), via, lobby, state };
  },

  async navigate(rt, args) {
    const state = await rt.browser.scan();
    const allowed = isNavigationAllowed(args.label, state, { origin: rt.origin, caseId: rt.caseId ?? null });
    if (!allowed.ok) return { status: 'refused', reason: allowed.reason, label: args.label };
    if (allowed.kind === 'reply' && !rt.caseId) return { status: 'refused', reason: 'case_not_opened', label: args.label };
    // A tour label must match exactly one control inside the tour container of
    // the one frame that shows the tour; the page re-checks this before the click.
    const tour = allowed.kind === 'tour';
    const summary = allowed.kind === 'summary';
    const match = summary
      ? { ok: Boolean(state.handoff.frame_id && state.handoff.terms_text), control: { frame_id: state.handoff.frame_id }, reason: 'summary_not_verified' }
      : tour
      ? matchLabel(state.controls.filter(c => c.frame_id === state.tour.frame_id && c.in_tour === true), args.label)
      : allControlsMatch(state, args.label);
    if (!match.ok) return { status: 'blocked', reason: `control_${match.reason}${tour ? '_in_tour' : ''}`, count: match.count };
    const click = await guardedClick(rt, match.control.frame_id, collapse(args.label), null, { tour, expectedTermsText: summary ? state.handoff.terms_text : null });
    if (click.new_targets.length) return { status: 'blocked', reason: 'new_target', new_targets: click.new_targets };
    return { status: 'ok', kind: allowed.kind, label: collapse(args.label) };
  },

  async type(rt, args) {
    let bytes;
    try { bytes = await rt.deps.readFile(args['text-file']); } catch { return { status: 'refused', reason: 'text_file_missing' }; }
    const file = checkTextFile(bytes, args.sha256);
    if (!file.ok) return { status: 'refused', reason: file.reason, ...(file.length ? { length: file.length } : {}) };
    const state = await rt.browser.scan();
    if (!state.selection.ok) return { status: 'blocked', reason: state.selection.reason, details: state.selection.details };
    if (state.composer.disabled) return { status: 'blocked', reason: 'composer_disabled' };
    if (normalizeComposer(state.composer.value) !== '') return { status: 'refused', reason: 'composer_not_empty', composer_sha256: state.composer.sha256 };
    // Input.insertText commits each LF as a paragraph or line-break edit, which a
    // rich-text chat editor may treat as Enter and send. Until the live smoke run
    // shows how this composer handles it, multi-line text goes only into a TEXTAREA.
    if (file.text.includes('\n') && state.composer.tag !== 'TEXTAREA') return { status: 'refused', reason: 'multiline_needs_textarea', composer_tag: state.composer.tag };
    const frameId = state.selection.frame_id;
    assertNotAborting(rt);
    await rt.browser.insertText(frameId, file.text);
    const read = await waitUntil(rt, () => rt.browser.scan(), s => s.composer && normalizeComposer(s.composer.value) === file.text, 5000, 500);
    const after = read.value;
    // An accidental submit would clear the composer and fail the readback below;
    // a changed message count alone may be a late assistant reply.
    const warning = after.message_count > state.message_count ? { warning: 'message_count_changed_during_type' } : {};
    if (!read.satisfied) return { status: 'error', reason: 'composer_readback_mismatch', expected_sha256: args.sha256, composer_sha256: after.composer?.sha256 ?? null, composer_length: after.composer?.length ?? null };
    return { status: 'ok', ...warning, composer: { sha256: after.composer.sha256, length: after.composer.length, label: after.composer.label, counter_text: after.composer.counter_text } };
  },

  async submit(rt, args) {
    const expected = args['expect-sha256'];
    const label = args.label || 'Submit';
    const loaded = await loadApproval(args['approval-file'], expected, COMMAND_PLAN_ITEMS.submit, rt.deps.readFile, approvalContext(rt));
    if (!loaded.ok) return { status: 'refused', reason: loaded.reason };
    const approval = loaded.approval;
    if (label === 'Chat now') return chatNow(rt, args, approval);
    const key = `submit:${expected}`, limit = SEND_LIMITS[approval.plan_item] || 1;
    if (usageCount(rt, key) >= limit) return { status: 'refused', reason: 'send_limit_reached', limit };
    const expectedFiles = args['expect-attachment'] || [];
    // Wait out a running assistant reply before judging the page.
    const idle = await waitUntil(rt, () => rt.browser.scan(), s => !s.busy, 30000);
    if (!idle.satisfied) return { status: 'blocked', reason: 'assistant_busy' };
    const approvedNames = approvedAttachmentNames(await readApprovalLog(rt.runDir));
    const first = submitBlocker(idle.value, expected, expectedFiles, approvedNames, null, label);
    if (first.blocked) return first.blocked;
    const { frameId, composer } = first;
    const identity = await reverify(rt);
    // Everything checked above is checked again after the identity read.
    const again = submitBlocker(await rt.browser.scan(), expected, expectedFiles, approvedNames, frameId, label);
    if (again.blocked) return { ...again.blocked, stage: 'pre_click' };
    const last = await rt.browser.occurrences(frameId, composer.text);
    const recheck = checkComposer(last.composer_value, expected);
    if (!recheck.ok) return { status: 'refused', reason: recheck.reason, stage: 'pre_click' };
    const claim = await claimBeforeClick(rt);
    if (claim) return claim;
    let click;
    try {
      click = await guardedClick(rt, frameId, label, async () => {
        await logAttempt(rt, { command: 'submit', sha256: expected, plan_item: approval.plan_item, label: approval.label ?? null, submit_label: label, approval_file: args['approval-file'], approval, identity,
          ...(expectedFiles.length ? { attachments: expectedFiles } : {}) });
        bumpUsage(rt, key);
        markDispatched(rt, 'submit', expected, 'clicked');
      }, { composerSubmit: true });
    } catch (error) { return clickFailure(rt, error); }
    try {
      const wait = await waitUntil(rt, () => rt.browser.occurrences(frameId, composer.text),
        o => normalizeComposer(o.composer_value) === '' && o.full === last.full + 1, 60000);
      const delivery = wait.satisfied ? 'sent' : 'uncertain';
      const reason = wait.satisfied ? undefined : (wait.value.prefix > last.prefix ? 'only_prefix_visible' : 'not_confirmed_in_conversation');
      rt.baseline = wait.value.message_count;
      // A new page target keeps the lockout, but the status still reports the
      // delivery so a sent message is never read as unsent.
      const result = click.new_targets.length
        ? { status: delivery, reason: 'new_target', delivery, clicked: true, new_targets: click.new_targets, ...(reason ? { confirmation_reason: reason } : {}) }
        : { status: delivery, clicked: true, ...(reason ? { reason } : {}) };
      Object.assign(result, { sha256: expected, plan_item: approval.plan_item, submit_label: label, occurrences: { before: last.full, after: wait.value.full, prefix_before: last.prefix, prefix_after: wait.value.prefix },
        composer_cleared: normalizeComposer(wait.value.composer_value) === '' });
      await logApproval(rt, { phase: 'result', command: 'submit', sha256: expected, status: result.status, delivery, reason: result.reason ?? null });
      return result;
    } catch (error) { return dispatchedFailure(rt, error); }
  },

  async approve(rt, args) {
    const expected = args['expect-terms-sha256'];
    const loaded = await loadApproval(args['approval-file'], expected, COMMAND_PLAN_ITEMS.approve, rt.deps.readFile, approvalContext(rt));
    if (!loaded.ok) return { status: 'refused', reason: loaded.reason };
    const key = `approve:${expected}`;
    if (usageCount(rt, key) >= 1) return { status: 'refused', reason: 'send_limit_reached', limit: 1 };
    // Same busy wait as submit: a reply still streaming must not be read as the
    // effect of the click.
    const idle = await waitUntil(rt, () => rt.browser.scan(), s => !s.busy, 30000);
    if (!idle.satisfied) return { status: 'blocked', reason: 'assistant_busy' };
    const state = idle.value;
    const multiSummary = state.handoff.approve_count > 1;
    const match = multiSummary
      ? { ok: Boolean(state.handoff.frame_id && state.handoff.terms_sha256 === expected), control: { frame_id: state.handoff.frame_id }, reason: 'summary_not_verified' }
      : allControlsMatch(state, 'Approve');
    if (!match.ok) return { status: 'blocked', reason: `control_${match.reason}` };
    const frameId = match.control.frame_id;
    const terms = await rt.browser.terms(frameId);
    if (terms.sha256 !== expected) return { status: 'refused', reason: 'terms_sha_mismatch', terms_sha256: terms.sha256, terms_text: terms.text, terms_container_basis: terms.basis ?? null };
    const identity = await reverify(rt);
    const recheck = await rt.browser.terms(frameId);
    if (recheck.sha256 !== expected) return { status: 'refused', reason: 'terms_sha_mismatch', stage: 'pre_click', terms_sha256: recheck.sha256 };
    const pre = await rt.browser.scan();
    if (pre.busy) return { status: 'blocked', reason: 'assistant_busy', stage: 'pre_click' };
    const preMatch = multiSummary
      ? { ok: pre.handoff.frame_id === frameId && pre.handoff.terms_sha256 === expected, control: { frame_id: pre.handoff.frame_id }, reason: 'summary_not_verified' }
      : allControlsMatch(pre, 'Approve');
    if (!preMatch.ok || preMatch.control.frame_id !== frameId) return { status: 'blocked', reason: preMatch.ok ? 'approve_frame_changed' : `control_${preMatch.reason}`, stage: 'pre_click' };
    const claim = await claimBeforeClick(rt);
    if (claim) return claim;
    let click;
    try {
      click = await guardedClick(rt, frameId, 'Approve', async () => {
        await logAttempt(rt, { command: 'approve', sha256: expected, plan_item: loaded.approval.plan_item, approval_file: args['approval-file'], approval: loaded.approval, identity });
        bumpUsage(rt, key);
        markDispatched(rt, 'approve', expected, 'clicked');
      }, { expectedTermsText: terms.text });
    } catch (error) { return clickFailure(rt, error); }
    try {
      const labelBefore = pre.composer?.label ?? null;
      // Approved only when the click visibly took: the Approve control is gone
      // or disabled, or the composer label changed. A new message alone is not
      // proof; it may be a reply that was already on its way. The effect must
      // show on two consecutive scans with a valid frame selection and the
      // Approve frame still reachable: one scan during a re-render can drop the
      // frame's controls and look like an effect.
      const approveLive = s => s.controls.some(c => collapse(c.label) === 'Approve' && !c.disabled && s.frames.find(f => f.frame_id === c.frame_id)?.same_origin !== false);
      const effect = s => s.selection?.ok === true && s.frames.some(f => f.frame_id === frameId && f.reachable !== false)
        && (!approveLive(s) || (s.composer?.label ?? null) !== labelBefore);
      let streak = 0;
      const wait = await waitUntil(rt, async () => { const s = await rt.browser.scan(); streak = effect(s) ? streak + 1 : 0; return s; },
        () => streak >= 2, 60000);
      rt.baseline = wait.value.message_count;
      const outcome = wait.satisfied ? 'approved' : 'uncertain';
      const result = click.new_targets.length
        ? { status: outcome, reason: 'new_target', delivery: outcome, clicked: true, new_targets: click.new_targets, ...(wait.satisfied ? {} : { confirmation_reason: 'no_visible_change' }) }
        : { status: outcome, clicked: true, ...(wait.satisfied ? {} : { reason: 'no_visible_change' }) };
      Object.assign(result, { terms_sha256: expected, terms_container_basis: terms.basis ?? null, composer_label_before: labelBefore, composer_label_after: wait.value.composer?.label ?? null,
        approve_control_after: approveLive(wait.value) ? 'enabled' : 'gone_or_disabled' });
      await logApproval(rt, { phase: 'result', command: 'approve', sha256: expected, status: result.status, delivery: outcome });
      return result;
    } catch (error) { return dispatchedFailure(rt, error); }
  },

  async attach(rt, args, cmd) {
    const loaded = await loadApproval(args['approval-file'], args.sha256, COMMAND_PLAN_ITEMS.attach, rt.deps.readFile, approvalContext(rt));
    if (!loaded.ok) return { status: 'refused', reason: loaded.reason };
    const key = `attach:${args.sha256}`;
    if (usageCount(rt, key) >= 1) return { status: 'refused', reason: 'send_limit_reached', limit: 1 };
    // The browser uploads a private copy in the run directory, hashed after it
    // was written, so a change to the source file after the check cannot reach
    // Amazon. The copy keeps the file name, which is what the chip shows.
    const name = basename(args.file);
    const copyDir = join(rt.runDir, 'uploads', stepNumber(cmd?.id ?? 0));
    const copy = join(copyDir, name);
    try {
      await mkdir(copyDir, { recursive: true, mode: 0o700 });
      await copyFile(args.file, copy, fsConstants.COPYFILE_EXCL);
    } catch (error) { return { status: 'refused', reason: error.code === 'ENOENT' ? 'file_missing' : 'file_copy_failed', message: String(error.message).slice(0, 200) }; }
    const fileSha = sha256(await rt.deps.readFile(copy));
    if (fileSha !== args.sha256) return { status: 'refused', reason: 'file_sha_mismatch', file_sha256: fileSha };
    const state = await rt.browser.scan();
    if (!state.selection.ok) return { status: 'blocked', reason: state.selection.reason, details: state.selection.details };
    const frameId = state.selection.frame_id;
    const upload = uploadControl(state.controls.filter(c => c.frame_id === frameId));
    if (!upload.ok) return { status: 'blocked', reason: `upload_${upload.reason}` };
    if (state.attachments.file_input_count !== 1) return { status: 'blocked', reason: 'file_input_count', count: state.attachments.file_input_count };
    if (state.attachments.input_files.length) return { status: 'blocked', reason: 'file_input_not_empty' };
    const input = await rt.browser.prepareFileInput(frameId);
    const identity = await reverify(rt);
    const claim = await claimBeforeClick(rt);
    if (claim) return claim;
    // logAttempt refuses once serve is aborting; everything from its return to
    // the setFile call below runs in one tick.
    await logAttempt(rt, { command: 'attach', sha256: args.sha256, plan_item: loaded.approval.plan_item, approval_file: args['approval-file'], approval: loaded.approval, file: args.file, upload_copy: copy, name, identity });
    bumpUsage(rt, key);
    markDispatched(rt, 'attach', args.sha256, 'attached');
    try {
      try { await rt.browser.setFile(input, copy); }
      catch (error) { if (!error.code) error.code = 'set_file_failed'; throw error; }
      const wait = await waitUntil(rt, () => rt.browser.scan(), s => s.attachments.chips.includes(name) && !s.attachments.uploading, 60000);
      const status = wait.satisfied ? 'attached' : 'uncertain';
      await logApproval(rt, { phase: 'result', command: 'attach', sha256: args.sha256, name, status });
      return { status, attached: true, ...(wait.satisfied ? {} : { reason: 'chip_not_confirmed' }), name, sha256: args.sha256, upload_copy: copy, chips: wait.value.attachments.chips };
    } catch (error) { return dispatchedFailure(rt, error); }
  },

  async transcript(rt, args, cmd) {
    // A wait never outlasts the serve budget (--max-minutes).
    const remaining = rt.deadline ? Math.max(0, rt.deadline - rt.deps.now()) : Infinity;
    const waitNew = args['wait-new'] || 0, timeoutMs = Math.min((args.timeout || 180) * 1000, remaining);
    const first = await rt.browser.scan();
    const frameId = first.selection.ok ? first.selection.frame_id : first.frames[0]?.frame_id;
    const base = rt.baseline ?? first.message_count;
    let satisfied = true, conversation = await rt.browser.conversation(frameId);
    if (waitNew > 0) {
      const wait = await waitUntil(rt, () => rt.browser.conversation(frameId), c => c.message_count >= base + waitNew && !c.busy, timeoutMs, 1500);
      satisfied = wait.satisfied; conversation = wait.value;
    }
    const textSha = sha256(conversation.text);
    const stem = `${stepNumber(cmd.id)}-transcript`;
    const record = { schema_version: 1, captured_at: iso(rt.deps.now()), url: first.url, conversation_url: first.conversation_url, frame_id: frameId,
      composer_label: first.composer?.label ?? null, text_sha256: textSha, ...conversation };
    const jsonPath = join(rt.runDir, 'transcripts', `${stem}.json`), textPath = join(rt.runDir, 'transcripts', `${stem}.txt`);
    await atomicWrite(textPath, conversation.text);
    const pagePath = join(rt.runDir, 'transcripts', `${stem}-page.txt`);
    await atomicWrite(pagePath, conversation.page_text || '');
    // Shadow-piercing text of every reachable frame, saved for reading only.
    const deep = [];
    if (typeof rt.browser.deepText === 'function') {
      for (const f of first.frames || []) {
        try { const d = await rt.browser.deepText(f.frame_id); if (d?.text) deep.push({ frame_id: f.frame_id, url: f.url || null, text: d.text }); }
        catch (error) { if (isFatal(error)) throw error; }
      }
    }
    const deepPath = join(rt.runDir, 'transcripts', `${stem}-deep.txt`);
    const deepText = deep.map(d => `=== frame ${d.frame_id} ${d.url || ''}\n${d.text}`).join('\n\n');
    await atomicWrite(deepPath, deepText);
    await atomicWrite(jsonPath, JSON.stringify(record, null, 2));
    rt.baseline = conversation.message_count;
    return { status: satisfied ? 'ok' : 'timeout', ...(satisfied ? {} : { reason: 'wait_new_timeout' }), path: jsonPath, text_path: textPath, text_sha256: textSha,
      message_count: conversation.message_count, new_messages: conversation.message_count - base, message_detection: conversation.message_detection,
      conversation_url: first.conversation_url, busy: conversation.busy, status_texts: conversation.status,
      denial: detectDenial(`${conversation.text}\n${conversation.page_text || ''}\n${deepText}`),
      text: conversation.text, page_text_path: pagePath, page_text: conversation.page_text || '', deep_text_path: deepPath, deep_text: deepText,
      messages: conversation.messages.slice(-20) };
  },

  async screenshot(rt, args, cmd) {
    const path = join(rt.runDir, 'screenshots', `${stepNumber(cmd.id)}-${args.name || 'screen'}.png`);
    const evidence = await rt.deps.screenshot(path);
    return { status: 'ok', path, receipt_path: `${path}.json`, task_id: evidence?.task_id ?? null, target_id: evidence?.target_id ?? null, captured_at: evidence?.captured_at ?? null };
  },

  async 'viewcase-raw'(rt, args, cmd) {
    const id = args['case-id'];
    const response = await rt.deps.evaluateMain(String.raw`(async()=>{const r=await fetch('/hill/hillservice/mons-api/ViewCase?caseId='+encodeURIComponent(${JSON.stringify(id)})+'&pageSize=50',{credentials:'same-origin'});return{status:r.status,body:await r.text()};})()`, 30000);
    const path = join(rt.runDir, 'viewcase', `${id}-${stepNumber(cmd.id)}.json`);
    await atomicWrite(path, String(response?.body ?? ''));
    const bodySha = sha256(String(response?.body ?? ''));
    if (response?.status !== 200) return { status: 'error', reason: `http_${response?.status}`, path, body_sha256: bodySha };
    let payload;
    try { payload = JSON.parse(response.body); } catch { return { status: 'error', reason: 'non_json', path, body_sha256: bodySha }; }
    return { status: 'ok', case_id: id, path, body_sha256: bodySha, summary: summarizeViewCase(payload) };
  },

};

function identitySummary(identity) { return identity ? { merchant_id: identity.merchant_id ?? null, marketplace_id: identity.marketplace_id ?? null, source: identity.source ?? null } : null; }

async function writeStep(rt, cmd, result) {
  let post = null, scanError = null;
  if (!rt.fatal) {
    try { post = await rt.browser.scan(); } catch (error) { scanError = error.code || error.message; if (isFatal(error)) rt.fatal = true; }
  }
  const step = { schema_version: 1, id: cmd.id, command: cmd.command, args: cmd.args, result,
    ...(post ? { url: post.url, conversation_url: post.conversation_url, frames: post.frames, selection: post.selection, composer: post.composer, controls: post.controls,
      status_texts: post.status_texts, tour: post.tour, denial: post.denial, handoff: post.handoff, attachments: post.attachments } : { scan_error: scanError }) };
  await atomicWrite(join(rt.runDir, 'steps', `${stepNumber(cmd.id)}-${cmd.command}.json`), JSON.stringify(step, null, 2));
}

/** Execute one queued command. Identity is verified before and after; a
 * mismatch locks out outbound commands until serve restarts. */
export async function executeCommand(rt, cmd) {
  rt.dispatch = null;
  if (!rt.current || rt.current.id !== cmd.id) rt.current = cmd;
  const started = rt.deps.now();
  const base = { schema_version: 1, id: cmd.id, command: cmd.command, started_at: iso(started) };
  const done = async result => {
    const final = { ...base, ...result, finished_at: iso(rt.deps.now()) };
    if (rt.lockout) final.lockout = rt.lockout;
    await writeStep(rt, cmd, final).catch(error => { final.step_error = error.message; });
    return final;
  };
  const verdict = validateCommandArgs(cmd.command, cmd.args || {});
  if (!verdict.ok) return done({ status: 'refused', reason: verdict.reason });
  if (cmd.expires_at && Date.parse(cmd.expires_at) < started) return done({ status: 'expired', reason: 'command_expired' });
  if (cmd.command === 'stop') {
    // Stop always stops. Identity is recorded, but a failure does not keep the tab.
    let identity = null, identityError = null;
    try { identity = identitySummary(await rt.deps.verifyIdentity()); }
    catch (error) { identityError = error.code || error.message; if (isFatal(error)) rt.fatal = true; }
    return done({ status: 'ok', stopping: true, identity: { before: identity }, ...(identityError ? { identity_error: identityError } : {}) });
  }
  if (rt.lockout && OUTBOUND.has(cmd.command)) return done({ status: 'blocked', reason: `locked_out:${rt.lockout.reason}` });
  if (rt.aborting) return done({ status: 'blocked', reason: 'aborting' });
  let before, data;
  try {
    try { before = await rt.deps.verifyIdentity(); }
    catch (error) {
      if (isFatal(error)) throw error;
      rt.lockout = { reason: 'identity_mismatch' };
      return done({ status: 'blocked', reason: 'identity_mismatch', message: error.message });
    }
    data = await handlers[cmd.command](rt, cmd.args || {}, cmd);
  } catch (error) {
    // After an outbound dispatch every failure is uncertain, never a plain error.
    if (rt.dispatch) return done({ ...(await dispatchedFailure(rt, error)), identity: { before: identitySummary(before) } });
    if (isFatal(error)) rt.fatal = true;
    if (error.code === 'aborting') return done({ status: 'blocked', reason: 'aborting', message: error.message, identity: { before: identitySummary(before) } });
    if (error.code === 'identity_mismatch') return done({ status: 'blocked', reason: 'identity_mismatch', message: error.message, identity: { before: identitySummary(before) } });
    return done({ status: 'error', reason: rt.fatal ? 'control_lost' : (error.code || 'exception'), message: String(error.message).slice(0, 500), identity: { before: identitySummary(before) } });
  } finally { if (rt.browser.release) await rt.browser.release().catch(() => {}); }
  let after;
  try { after = await rt.deps.verifyIdentity(); }
  catch (error) {
    if (isFatal(error)) rt.fatal = true;
    else rt.lockout = { reason: 'identity_mismatch' };
    // A dispatched action keeps its outcome at the top level so a sent message is
    // never read as unsent: sent_identity_unverified, approved_identity_unverified,
    // attached_identity_unverified, or uncertain.
    const acted = ACTION_DONE.has(data.status) ? `${data.status}_identity_unverified` : data.status === 'uncertain' ? 'uncertain' : 'blocked';
    return done({ status: acted, reason: rt.fatal ? 'control_lost' : 'identity_mismatch', action_status: data.status, delivery: data.delivery ?? data.status, data, identity: { before: identitySummary(before), after: null } });
  }
  return done({ ...data, identity: { before: identitySummary(before), after: identitySummary(after) } });
}

export async function readApprovalLog(runDir) {
  let text = '';
  try { text = await readFile(join(runDir, 'approvals.jsonl'), 'utf8'); } catch { return []; }
  const entries = [];
  for (const line of text.split('\n')) {
    if (!line.trim()) continue;
    try { entries.push(JSON.parse(line)); } catch { /* A torn last line is ignored; attempts are written before any click. */ }
  }
  return entries;
}

/** File names this run uploaded and confirmed (an attach result logged as
 * attached) that no submit has used yet. A submit attempt that carried a name
 * uses one confirmed attach of it, unless its result line says it was blocked
 * before the click. A sent or uncertain submit therefore needs a new approved
 * attach before a chip with the same name is accepted again. */
export function approvedAttachmentNames(entries) {
  const notDispatched = new Set(entries.filter(e => e.phase === 'result' && e.command === 'submit' && e.status === 'blocked' && typeof e.queue_id === 'string').map(e => e.queue_id));
  const available = new Map();
  for (const e of entries) {
    if (e.phase === 'result' && e.command === 'attach' && e.status === 'attached' && typeof e.name === 'string') available.set(e.name, (available.get(e.name) || 0) + 1);
    else if (e.phase === 'attempt' && e.command === 'submit' && Array.isArray(e.attachments) && !notDispatched.has(e.queue_id)) {
      for (const name of new Set(e.attachments)) if (available.get(name)) available.set(name, available.get(name) - 1);
    }
  }
  return [...available].filter(([, n]) => n > 0).map(([name]) => name);
}

/** Queue ids with an attempt line and no result line: the action may have happened. */
export function unmatchedAttempts(entries) {
  const open = new Map();
  for (const e of entries) {
    if (typeof e.queue_id !== 'string') continue;
    if (e.phase === 'attempt') open.set(e.queue_id, e);
    else if (e.phase === 'result') open.delete(e.queue_id);
  }
  return open;
}

export async function loadUsageCounts(runDir) {
  const counts = new Map();
  for (const entry of await readApprovalLog(runDir)) {
    if (entry.phase === 'attempt') counts.set(`${entry.command}:${entry.sha256}`, (counts.get(`${entry.command}:${entry.sha256}`) || 0) + 1);
  }
  return counts;
}

const OUTBOUND_NOTE = 'The command may have run. Check the transcript and approvals.jsonl before resending; it is never retried automatically.';

/** Write an interrupted result unless a real one exists. A `cancelled` marker is
 * replaced: a client wrote it while serve was already running the command. */
async function writeInterrupted(runDir, id, result) {
  const path = join(runDir, 'results', `${id}.json`);
  try {
    const existing = JSON.parse(await readFile(path, 'utf8'));
    if (existing?.status !== 'cancelled') return false;
    result = { ...result, replaced: 'cancelled' };
  } catch (error) { if (error.code !== 'ENOENT' && !(error instanceof SyntaxError)) throw error; }
  await atomicWrite(path, JSON.stringify(result, null, 2));
  return true;
}

function interruptedResult(id, command, at, extra = {}) {
  const outbound = OUTBOUND.has(command);
  return { schema_version: 1, id, command: command ?? null, status: outbound ? 'uncertain' : 'error', reason: 'interrupted', note: OUTBOUND_NOTE, ...extra, finished_at: iso(at) };
}

/** Mark every command a previous serve started but did not finish: a
 * results/NNN.running marker without a result, or an attempt line without a
 * result line. These commands are never executed again. */
export async function recoverInterrupted(runDir, now = Date.now()) {
  const recovered = [];
  const results = await readdir(join(runDir, 'results'));
  const entries = await readApprovalLog(runDir);
  const open = unmatchedAttempts(entries);
  const ids = new Set([...results.filter(n => /^\d{3,}\.running$/.test(n)).map(n => n.slice(0, -8)), ...open.keys()]);
  for (const id of [...ids].sort((a, b) => Number(a) - Number(b))) {
    let command = null;
    try { command = JSON.parse(await readFile(join(runDir, 'queue', `${id}.json`), 'utf8')).command ?? null; } catch { command = open.get(id)?.command ?? null; }
    const attempt = open.get(id);
    if (attempt) {
      const kind = attempt.command === 'attach' ? 'attached' : 'clicked';
      await appendFile(join(runDir, 'approvals.jsonl'), JSON.stringify({ at: iso(now), queue_id: id, phase: 'result', command: attempt.command, sha256: attempt.sha256, status: 'uncertain', reason: 'interrupted' }) + '\n');
      if (await writeInterrupted(runDir, id, interruptedResult(id, command ?? attempt.command, now, { status: 'uncertain', [kind]: true }))) recovered.push(id);
    } else if (await writeInterrupted(runDir, id, interruptedResult(id, command, now))) recovered.push(id);
    await unlink(join(runDir, 'results', `${id}.running`)).catch(() => {});
  }
  return recovered;
}

/** Signal and crash path: mark the command in flight uncertain (outbound) or
 * interrupted before the process exits. */
export async function markInFlight(rt, cause) {
  const cmd = rt?.current;
  if (!cmd) return null;
  const d = rt.dispatch;
  if (d && !d.logged) await logApproval(rt, { phase: 'result', command: d.command, sha256: d.sha256, status: 'uncertain', reason: 'interrupted', cause }).catch(() => {});
  const result = interruptedResult(cmd.id, cmd.command, rt.deps.now(), { cause, ...(d ? { status: 'uncertain', [d.kind]: true } : {}) });
  const written = await writeInterrupted(rt.runDir, cmd.id, result);
  if (written) await unlink(join(rt.runDir, 'results', `${cmd.id}.running`)).catch(() => {});
  return written ? result : null;
}

/** Process the lowest-numbered queued command without a result. Returns the
 * result, or null when the queue is empty. Before a command runs, serve writes
 * results/NNN.running; a command found with that marker or with an unmatched
 * attempt line is marked interrupted and never runs again. */
export async function processNext(rt) {
  const resultsDir = join(rt.runDir, 'results');
  const names = (await readdir(join(rt.runDir, 'queue'))).filter(n => /^\d{3,}\.json$/.test(n)).sort((a, b) => Number.parseInt(a) - Number.parseInt(b));
  const done = new Set(await readdir(resultsDir));
  const name = names.find(n => !done.has(n));
  if (!name) return null;
  const id = name.slice(0, -5);
  const runningPath = join(resultsDir, `${id}.running`);
  if (done.has(`${id}.running`) || unmatchedAttempts(await readApprovalLog(rt.runDir)).has(id)) {
    await recoverInterrupted(rt.runDir, rt.deps.now());
    try { return JSON.parse(await readFile(join(resultsDir, name), 'utf8')); } catch { return interruptedResult(id, null, rt.deps.now()); }
  }
  // Once serve is aborting no new command starts; a later serve picks it up.
  if (rt.aborting) return null;
  let cmd;
  try { cmd = JSON.parse(await readFile(join(rt.runDir, 'queue', name), 'utf8')); } catch { cmd = null; }
  // expires_at is required: a queued command nobody waits for must not run later.
  const expiresOk = cmd && typeof cmd.expires_at === 'string' && ISO_TZ.test(cmd.expires_at) && !Number.isNaN(Date.parse(cmd.expires_at));
  if (!cmd || cmd.schema_version !== 1 || cmd.id !== id || !COMMANDS.includes(cmd.command) || !expiresOk) {
    const refused = { schema_version: 1, id, command: cmd?.command ?? null, status: 'refused', reason: 'command_malformed', finished_at: iso(rt.deps.now()) };
    await atomicWrite(join(resultsDir, name), JSON.stringify(refused, null, 2));
    return refused;
  }
  if (rt.aborting) return null;
  rt.current = cmd;
  await atomicWrite(runningPath, JSON.stringify({ schema_version: 1, id, command: cmd.command, pid: process.pid, started_at: iso(rt.deps.now()) }));
  // Handshake with a client that gave up: it writes `cancelled` first and then
  // looks for this marker, so exactly one side wins.
  if (existsSync(join(resultsDir, name))) {
    await unlink(runningPath).catch(() => {});
    rt.current = null;
    try { return JSON.parse(await readFile(join(resultsDir, name), 'utf8')); } catch { return { id, status: 'cancelled' }; }
  }
  const result = await executeCommand(rt, cmd);
  if (cmd.command === 'stop' && result.stopping === true) { rt.stopRequested = { id, result }; rt.current = null; return result; }
  await atomicWrite(join(resultsDir, name), JSON.stringify(result, null, 2));
  await unlink(runningPath).catch(() => {});
  rt.current = null;
  rt.dispatch = null;
  return result;
}

// ---------------------------------------------------------------- processes

export async function readRunConfig(runDir) {
  let raw;
  try { raw = await readFile(join(runDir, 'run.json'), 'utf8'); } catch { throw codeError('run_config_missing', `No run.json in ${runDir}`); }
  let parsed;
  try { parsed = JSON.parse(raw); } catch { throw codeError('run_config_invalid', 'run.json is not valid JSON'); }
  return validateRunConfig(parsed);
}

async function ensureRunDirs(runDir) {
  for (const sub of RUN_SUBDIRS) await mkdir(join(runDir, sub), { recursive: true });
}

const alive = pid => { try { process.kill(pid, 0); return true; } catch (error) { return error.code === 'EPERM'; } };

async function claimServe(runDir) {
  const path = join(runDir, 'serve.pid');
  for (let attempt = 0; attempt < 2; attempt++) {
    try {
      const handle = await open(path, 'wx', 0o600);
      try { await handle.writeFile(JSON.stringify({ pid: process.pid, started_at: new Date().toISOString() })); } finally { await handle.close(); }
      const cleanup = () => { try { unlinkSync(path); } catch { /* already gone */ } };
      process.once('exit', cleanup);
      return cleanup;
    } catch (error) {
      if (error.code !== 'EEXIST') throw error;
      let owner = null;
      try { owner = JSON.parse(await readFile(path, 'utf8')); } catch { /* unreadable: treat as live */ }
      if (owner && Number.isInteger(owner.pid) && !alive(owner.pid) && attempt === 0) { await unlink(path).catch(() => {}); continue; }
      throw codeError('serve_already_running', `Another serve holds ${path}`);
    }
  }
  throw codeError('serve_already_running', `Another serve holds ${path}`);
}

async function loadBrowserDeps() {
  const [cdp, sc, tabs, lock, ui, cases, registry, policy] = await Promise.all([
    import('../report-fetcher/cdp.mjs'), import('../report-fetcher/sc-account.mjs'), import('../browserctl/task-tabs.mjs'),
    import('../browserctl/session-lock.mjs'), import('./browser-ui.mjs'), import('./cases.mjs'),
    import('../browserctl/lease-registry.mjs'), import('../browserctl/policy.mjs')]);
  return { cdp, sc, tabs, lock, ui, cases, registry, policy };
}

/** Bind the case chat window to a named additional slot of this run's task, the
 * way task-tabs binds a page it created: reserve the slot, bind the existing
 * target, guard its session with the slot's control token and renew it on the
 * policy heartbeat. Cleanup then treats the window as task-controlled and
 * neither adopts nor closes it. `release(outcome)` ends the binding. */
export async function adoptChatTarget({ registry, cdp, policy, port, taskId, owner, origin, target }) {
  const spec = { port, taskId, slot: CHAT_SLOT };
  const reservation = await registry.reserveTaskTab({ ...spec, workflow: 'amazon-communications', owner, origin, policy });
  if (reservation.kind !== 'create') {
    if (reservation.controlToken) await registry.abandonTaskTabReservation({ ...spec, controlToken: reservation.controlToken }).catch(() => {});
    throw codeError('chat_slot_unavailable', `${taskId}/${CHAT_SLOT} is ${reservation.kind}${reservation.reason ? `: ${reservation.reason}` : ''}`);
  }
  const { controlToken, reservationToken } = reservation;
  let bound = false, session = null, listed = null;
  try {
    await registry.bindReservedTaskTab({ ...spec, targetId: target.targetId, reservationToken, controlToken, owner, origin, policy });
    bound = true;
    listed = (await cdp.listPages()).find(p => p.id === target.targetId);
    if (!listed?.webSocketDebuggerUrl) throw codeError('chat_target_unavailable', `chat window ${target.targetId} has no connection endpoint`);
    session = await cdp.Session.open(listed.webSocketDebuggerUrl);
    session.setTaskControlGuard(() => registry.assertTaskTabControl({ ...spec, controlToken, targetId: target.targetId }), { initialUrl: listed.url });
    await session.assertTaskControl();
  } catch (error) {
    session?.close();
    await (bound ? registry.releaseTaskTabControl({ ...spec, controlToken, outcome: 'error', policy })
      : registry.abandonTaskTabReservation({ ...spec, controlToken })).catch(() => {});
    throw error;
  }
  let renewing = false;
  const heartbeat = setInterval(async () => {
    if (renewing) return;
    renewing = true;
    try {
      const renewed = await registry.touchTaskTabControl({ ...spec, controlToken, targetId: target.targetId, policy });
      if (!renewed) throw codeError('TASK_TAB_CONTROL_LOST', 'chat slot renewal did not confirm ownership');
    } catch (error) { session.invalidateTaskControl(error); } finally { renewing = false; }
  }, policy.cleanup.heartbeat_interval_ms);
  heartbeat.unref?.();
  let released = false;
  return {
    ...spec, targetId: target.targetId, url: listed.url, session,
    async release(outcome) {
      if (released) return null;
      released = true;
      clearInterval(heartbeat);
      session.close();
      return registry.releaseTaskTabControl({ ...spec, controlToken, outcome, policy });
    },
  };
}

/** Identity check used before and after every command. It samples the live
 * header and GetUserContext IDs like browser-ui context(). When the page does
 * not expose live IDs it falls back to the IDs read on /home at startup plus the
 * exact header tokens, the same rule cases.mjs applies on case pages. Retries
 * for 15 s because the header paints after the page body. */
function identityVerifier(B, page, account, homeIdentity) {
  const ownership = { exclusiveContext: true, sellerCentral: { marketplace: account.marketplace, origin: B.ui.origins[account.marketplace] } };
  return async () => {
    const end = Date.now() + 15000;
    let last = 'unverified';
    for (;;) {
      await page.session.assertTaskControl(ownership);
      let state, live;
      try {
        state = await B.ui.snapshot(page.session);
        live = await B.sc.readIdentity(page.session);
      } catch (error) {
        // A read during a re-render (right after Submit) can fail; retry inside the window.
        if (isFatal(error)) throw error;
        last = `identity read failed: ${String(error.message).slice(0, 200)}`;
        if (Date.now() >= end) throw codeError('identity_mismatch', last);
        await new Promise(r => setTimeout(r, 1000));
        continue;
      }
      // A live ID that differs stops at once; home IDs fill only missing fields.
      const resolved = resolveIdentity(live, homeIdentity, account);
      if (!resolved.ok) throw codeError('identity_mismatch', resolved.reason);
      state.identity = resolved.identity;
      if (B.ui.contextMatches(state, account, 'sc')) {
        await page.session.assertTaskControl(ownership);
        return { merchant_id: resolved.identity.merchantId, marketplace_id: resolved.identity.marketplace ?? null, source: resolved.source, url: state.url };
      }
      last = `account header or IDs not verified at ${state.url}`;
      if (Date.now() >= end) throw codeError('identity_mismatch', last);
      await new Promise(r => setTimeout(r, 1000));
    }
  };
}

/** Process the queue until stop, a budget runs out, control is lost, or an
 * identity mismatch or new page target halts the run. Only stop releases as
 * success; everything else releases as error (two-hour inspection lease). */
export async function serveLoop(rt, { started, maxMs, idleMs, pollMs = 500 }) {
  let lastActivity = rt.deps.now();
  for (;;) {
    if (rt.aborting) return { exitReason: 'aborting', outcome: 'error' };
    if (rt.deps.now() - started > maxMs) return { exitReason: 'max_minutes', outcome: 'error' };
    const result = await processNext(rt);
    if (rt.aborting) return { exitReason: 'aborting', outcome: 'error' };
    if (result) lastActivity = rt.deps.now();
    if (rt.stopRequested) return { exitReason: 'stop', outcome: 'success' };
    if (rt.fatal) return { exitReason: 'control_lost', outcome: 'error' };
    if (rt.lockout) return { exitReason: `halted_${rt.lockout.reason}`, outcome: 'error' };
    if (!result) {
      if (rt.deps.now() - lastActivity > idleMs) return { exitReason: 'idle_minutes', outcome: 'error' };
      await rt.deps.sleep(pollMs);
    }
  }
}

/** Signal and crash handler. The aborting flag is set synchronously, before
 * any await, so no click, insert or upload starts after the interrupt while
 * `finish` marks the command in flight and releases the tab. */
export function abortHandler(ctl, name, finish) {
  return async error => {
    if (ctl.exiting) return;
    ctl.exiting = true;
    if (ctl.rt) ctl.rt.aborting = true;
    if (error instanceof Error) console.error(`${name}:`, error.message);
    await finish(error);
  };
}

export async function serve({ run, maxMinutes = 90, idleMinutes = 20 }) {
  const runDir = resolve(run);
  const config = await readRunConfig(runDir);
  // Same session check as cases.mjs run(), before any browser module loads.
  const binding = assertSession(process.env);
  await ensureRunDirs(runDir);
  const releasePid = await claimServe(runDir);
  // Commands a previous serve started but never finished are marked uncertain
  // (outbound) or interrupted and are never executed again.
  const recovered = await recoverInterrupted(runDir);
  const B = await loadBrowserDeps();
  const account = B.cases.caseBrowserAccount(config.account);
  const origin = B.ui.origins[account.marketplace];
  if (!origin) { releasePid(); throw codeError('marketplace_unsupported', `No Seller Central origin for ${account.marketplace}`); }
  const taskId = B.tabs.taskIdFor('amazon-communications', `seller-assistant:${config.run_id}`);
  // Lock finding (session-lock.mjs, browserctl.mjs run): `browserctl run` holds the
  // root 9223 lock and passes its token to this child. acquireSessionLock here does
  // not deadlock: it sees the parent's token and creates a child link
  // (cdp-9223.lock.child-<token>); repeat calls in this process are re-entrant
  // (a use count). Holding the link, as cases.mjs run() does, keeps the lock for
  // the whole chat: releaseTaskPage then does not ask the launcher to drop the
  // root lock early, so no Grimoire job can take 9223 between commands. The task
  // heartbeat is started by acquireTaskPage (30 s interval, token-checked) and
  // keeps running while this loop sleeps; no extra heartbeat is needed. The
  // operator session on 9222 takes no port lock (acquireServeLock).
  const unlock = acquireServeLock(binding, B.lock);
  let page = null, outcome = 'error', exitCode = 1, rt = null;
  const statusPath = join(runDir, 'serve.json');
  const ctl = { exiting: false, rt: null };
  // The case chat window stays an interactive (handoff) lease after a clean stop,
  // because the chat with Amazon may still be open; otherwise an inspection lease.
  const releaseChat = async result => {
    try { await rt?.chat?.release?.(result === 'success' ? 'handoff' : 'error'); }
    catch (e) { console.error('chat window release failed:', e.message); }
  };
  const abort = (name, code) => abortHandler(ctl, name, async () => {
    try { await markInFlight(rt, name); } catch (e) { console.error(`${name} could not mark the command in flight:`, e.message); }
    await releaseChat('error');
    try { if (page) await B.tabs.releaseTaskPage(page, { outcome: 'error' }); }
    catch (e) { console.error(`${name} browser release failed:`, e.message); }
    finally { process.exit(code); }
  });
  const onTerm = abort('SIGTERM', 143), onInt = abort('SIGINT', 130);
  const onCrash = abort('uncaughtException', 1), onRejection = abort('unhandledRejection', 1);
  process.once('SIGTERM', onTerm); process.once('SIGINT', onInt);
  process.on('uncaughtException', onCrash); process.on('unhandledRejection', onRejection);
  const started = Date.now();
  let exitReason = 'unknown';
  try {
    page = await B.tabs.acquireTaskPage({ taskId, workflow: 'amazon-communications', initialUrl: `${origin}/home`, exclusiveContext: true,
      sellerCentral: { marketplace: account.marketplace, origin }, closeOnFailure: false });
    await B.sc.switchAccount(page.session, origin, { accountName: account.seller_central_name, marketplaceLabel: account.marketplace_label,
      marketplace: account.marketplace, parentAccountName: account.parent_account_name }, { returnTo: '/home' });
    const homeIdentity = await B.sc.readIdentity(page.session);
    const session = page.session;
    const policy = B.policy.loadBrowserPolicy();
    ctl.rt = rt = {
      runDir, config, account, origin, lockout: null, fatal: false, aborting: ctl.exiting, baseline: null, counts: await loadUsageCounts(runDir), deadline: started + maxMinutes * 60000,
      taskTargetId: page.targetId, caseId: null, chat: null,
      browser: makeBrowser({ send: (m, p, o) => session.send(m, p, o), listPageTargets: () => B.cdp.listPages() }, origin),
      deps: {
        verifyIdentity: identityVerifier(B, page, account, homeIdentity),
        screenshot: path => B.ui.screenshot(page, path, account, 'sc'),
        evaluateMain: (expression, timeoutMs) => B.cdp.evaluate(session, expression, timeoutMs),
        claimAttended: async request => {
          const path = join(runDir, 'claim-attended.json');
          await atomicWrite(path, JSON.stringify(request, null, 2));
          return runClaimAttended(path);
        },
        adoptChat: async target => {
          const chat = await adoptChatTarget({ registry: B.registry, cdp: B.cdp, policy, port: page.port, taskId, owner: `seller-assistant:${process.pid}`, origin, target });
          return { ...chat, browser: makeBrowser({ send: (m, p, o) => chat.session.send(m, p, o), listPageTargets: () => B.cdp.listPages() }, origin) };
        },
        readFile, now: Date.now, sleep: ms => new Promise(r => setTimeout(r, ms)),
      },
    };
    const identity = await rt.deps.verifyIdentity();
    const serving = { status: 'serving', run_id: config.run_id, pid: process.pid, session: binding.session, port: binding.port, task_id: taskId, target_id: page.targetId, started_at: iso(started), identity: identitySummary(identity), recovered_interrupted: recovered };
    await atomicWrite(statusPath, JSON.stringify(serving, null, 2));
    console.log(JSON.stringify(serving));
    const loop = await serveLoop(rt, { started, maxMs: maxMinutes * 60000, idleMs: idleMinutes * 60000 });
    exitReason = loop.exitReason; outcome = loop.outcome;
    // Timeouts release as error so the chat tab stays in a two-hour inspection
    // lease instead of the ten-minute success grace.
    exitCode = outcome === 'success' ? 0 : ['max_minutes', 'idle_minutes'].includes(exitReason) ? 0 : 1;
  } catch (error) {
    exitReason = error.code || 'startup_failed';
    const failure = { status: 'error', run_id: config.run_id, reason: exitReason, message: String(error.message).slice(0, 500) };
    await atomicWrite(statusPath, JSON.stringify(failure, null, 2)).catch(() => {});
    console.log(JSON.stringify(failure));
    exitCode = 1;
  } finally {
    process.removeListener('SIGTERM', onTerm); process.removeListener('SIGINT', onInt);
    process.removeListener('uncaughtException', onCrash); process.removeListener('unhandledRejection', onRejection);
    await releaseChat(outcome);
    let release = null;
    try { if (page) release = await B.tabs.releaseTaskPage(page, { outcome }); } catch (error) { release = { error: error.message }; }
    if (rt?.stopRequested) {
      const { id, result } = rt.stopRequested;
      await atomicWrite(join(runDir, 'results', `${id}.json`), JSON.stringify({ ...result, released: !release?.error, release_outcome: outcome, ...(release?.error ? { release_error: release.error } : {}) }, null, 2)).catch(() => {});
      await unlink(join(runDir, 'results', `${id}.running`)).catch(() => {});
    }
    await atomicWrite(statusPath, JSON.stringify({ status: 'stopped', run_id: config.run_id, reason: exitReason, release_outcome: outcome, stopped_at: iso(Date.now()) }, null, 2)).catch(() => {});
    unlock();
    releasePid();
  }
  return exitCode;
}

export async function allocateQueueEntry(runDir) {
  const queue = join(runDir, 'queue');
  for (let attempt = 0; attempt < 1000; attempt++) {
    const name = nextQueueName(await readdir(queue));
    try { const handle = await open(join(queue, `${name}.claim`), 'wx', 0o600); await handle.close(); return name; }
    catch (error) { if (error.code !== 'EEXIST') throw error; }
  }
  throw codeError('queue_busy', 'Could not allocate a queue number');
}

export async function sendCommand({ run, command, args }, { pollMs = 500, out = console.log } = {}) {
  const runDir = resolve(run);
  await readRunConfig(runDir);
  let owner = null;
  try { owner = JSON.parse(await readFile(join(runDir, 'serve.pid'), 'utf8')); } catch { /* checked below */ }
  if (!owner || !alive(owner.pid)) { out(JSON.stringify({ status: 'error', reason: 'serve_not_running', run_dir: runDir })); return 2; }
  const timeoutSeconds = command === 'transcript' ? Math.max(600, (args.timeout || 180) + 120) : 600;
  const id = await allocateQueueEntry(runDir);
  const created = Date.now();
  const entry = { schema_version: 1, id, command, args, created_at: iso(created), expires_at: iso(created + timeoutSeconds * 1000) };
  await atomicWrite(join(runDir, 'queue', `${id}.json`), JSON.stringify(entry, null, 2));
  const resultPath = join(runDir, 'results', `${id}.json`);
  const printResult = async () => {
    const result = JSON.parse(await readFile(resultPath, 'utf8'));
    if (result?.status === 'cancelled' && await commandInFlight(runDir, id)) return null;
    out(JSON.stringify(result, null, 2));
    return SUCCESS.has(result.status) ? 0 : 1;
  };
  // Serve started the command (marker or attempt line): it may have run, so the
  // answer is uncertain, never cancelled. With serve gone, the uncertain result is
  // also written so a later serve cannot run it.
  const uncertain = async (reason, serveGone) => {
    const result = interruptedResult(id, command, Date.now(), { status: 'uncertain', reason, in_flight: true });
    if (serveGone) await writeInterrupted(runDir, id, result).catch(() => {});
    out(JSON.stringify(result));
    return 2;
  };
  const giveUp = async (reason, serveGone) => {
    if (await commandInFlight(runDir, id)) return uncertain(reason, serveGone);
    const cancelled = await cancelQueued(resultPath, id, reason);
    if (!cancelled) { try { const code = await printResult(); if (code !== null) return code; } catch { /* torn write */ } }
    // Serve may have claimed the command between the check and the marker.
    if (await commandInFlight(runDir, id)) return uncertain(reason, serveGone);
    out(JSON.stringify({ status: 'cancelled', reason, id, cancelled, note: 'The command never started. A later serve skips it.' }));
    return 2;
  };
  while (Date.now() - created < timeoutSeconds * 1000) {
    try { const code = await printResult(); if (code !== null) return code; } catch { /* not written yet */ }
    if (!alive(owner.pid)) {
      try { const code = await printResult(); if (code !== null) return code; } catch { /* no result */ }
      return giveUp('serve_exited', true);
    }
    await new Promise(r => setTimeout(r, pollMs));
  }
  return giveUp('client_timeout', !alive(owner.pid));
}

/** True when serve started this command: results/NNN.running exists, or
 * approvals.jsonl has its attempt line without a result line. */
export async function commandInFlight(runDir, id) {
  if (existsSync(join(runDir, 'results', `${id}.running`))) return true;
  return unmatchedAttempts(await readApprovalLog(runDir)).has(id);
}

/** Mark a queued command as cancelled so a later serve skips it. Exclusive
 * create: an existing result is never overwritten. Returns false when a result
 * already exists. */
export async function cancelQueued(resultPath, id, reason) {
  let handle;
  try { handle = await open(resultPath, 'wx', 0o600); }
  catch (error) { if (error.code === 'EEXIST') return false; throw error; }
  try { await handle.writeFile(JSON.stringify({ schema_version: 1, id, status: 'cancelled', reason, finished_at: new Date().toISOString() }, null, 2)); }
  finally { await handle.close(); }
  return true;
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  try {
    const parsed = parseArgs(process.argv.slice(2));
    const code = parsed.mode === 'serve' ? await serve(parsed) : await sendCommand(parsed);
    process.exit(code);
  } catch (error) {
    console.log(JSON.stringify({ status: 'error', reason: error.code || 'usage', message: error.message }));
    process.exit(2);
  }
}
