/** Pure preview/import contracts plus durable local submission evidence. */
import { open, rename, readFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { createHash } from 'node:crypto';
import { check } from './browser-ui.mjs';

export function importIdentity(url) {
  const parsed = new URL(url);
  check(parsed.origin === 'https://app.flatfile.pro', 'Import identity must belong to FlatFilePro');
  const candidates = [parsed.searchParams.get('importId'), parsed.searchParams.get('import_id'),
    (/\/(?:imports|uploads)\/([A-Za-z0-9-]+)(?:\/|$)/.exec(parsed.pathname) || [])[1]].filter(Boolean);
  check(candidates.length && new Set(candidates).size === 1 && /^[A-Za-z0-9-]+$/.test(candidates[0]), 'Import identity is missing or ambiguous before submit');
  return {import_id: candidates[0], import_url: parsed.href};
}

export function uploadedFileIdentity(url, labels, account, filename) {
  const parsed=new URL(url);
  check(parsed.origin==='https://app.flatfile.pro'&&parsed.pathname==='/import','Uploaded file identity requires the observed /import page');
  check(/^[A-Z0-9]+$/.test(account.seller_id||'')&&/^[A-Z0-9]+$/.test(account.marketplace_id||''),'Uploaded file requires exact seller and marketplace IDs');
  check(/^[A-Za-z0-9_.-]+\.xlsx$/.test(filename),'Invalid local workbook filename');
  const prefix=`${account.seller_id}-${account.marketplace_id}/`;
  const matches=labels.filter(value=>typeof value==='string'&&value.startsWith(prefix)&&value.endsWith(`-${filename} (SKU)`));
  check(matches.length===1,'Expected one exact seller-specific uploaded workbook with SKU matching');
  const uploadKey=matches[0].slice(0,-6),serverName=uploadKey.slice(prefix.length);
  check(/^[0-9]+-/.test(serverName)&&serverName.replace(/^[0-9]+-/,'')===filename,'Uploaded workbook identifier is malformed');
  return {identity_kind:'uploaded_file',import_url:parsed.origin+'/import',upload_key:uploadKey,upload_filename:filename,match_basis:'SKU'};
}

export function destinationSearchField(field) {
  // The observed v2 schema uses one-based flattened occurrences. Restrict
  // translation to verified secondary product image slots, never offer/safety.
  const canonical=/^other_product_image_locator_([1-8])\.0\.media_location$/.exec(field);
  return canonical ? `other_product_image_locator_${canonical[1]}__1__media_location` : field;
}

export function exactDestination(options, field, searchValue = null) {
  const matches=options.filter(option=>option.label===field||option.label.endsWith(`(${field})`));
  if(matches.length===0&&/^other_product_image_locator_[1-8]__1__media_location$/.test(field)&&searchValue===field&&options.length===1) {
    // Current autocomplete hides columnName in each option but searches it.
    // This is only a candidate: selected technical label MUST be read back
    // before MAP ATTRIBUTES, which is the actual mapping mutation.
    return options[0];
  }
  check(matches.length===1,'ffp_image_slot_unverifiable: no unique visible destination technical identifier; localized labels or option positions cannot identify an Amazon image slot');
  return matches[0];
}

export function verifySelectedDestination(value, field) {
  check(value===field||value.endsWith(`(${field})`),'ffp_image_slot_unverifiable: selected destination does not expose the exact technical identifier');
  return true;
}

export function sameUploadedFile(expected, actual) {
  check(expected.identity_kind==='uploaded_file'&&actual.identity_kind==='uploaded_file'&&
    expected.upload_key===actual.upload_key&&expected.upload_filename===actual.upload_filename&&actual.match_basis==='SKU',
    'Selected uploaded workbook changed');
  return true;
}

export function pageNavigation(state) {
  const controls = (state.controls || []).filter(c => /^(?:Next|Next page|Go to next page|›|»)$/.test(c.label));
  check(controls.length <= 1, 'Ambiguous preview pagination controls');
  const page = /\bPage\s+(\d+)\s+of\s+(\d+)\b/i.exec(state.text || '');
  const range = /\b(?:Showing\s+)?(\d+)\s*(?:to|[-–])\s*(\d+)\s+of\s+(\d+)\b/i.exec(state.text || '');
  if (page) {
    check(Number(page[1]) >= 1 && Number(page[1]) <= Number(page[2]), 'Invalid preview page count');
    check(Number(page[1]) === Number(page[2]) || (controls.length === 1 && !controls[0].disabled), 'Preview has more pages but no usable Next control');
    check(Number(page[1]) !== Number(page[2]) || !controls.length || controls[0].disabled, 'Preview page count contradicts Next control');
  }
  if (range) {
    const [,first,last,total]=range.map(Number);
    check(first >= 1 && first <= last && last <= total, 'Invalid preview row range');
    check(last === total || (controls.length === 1 && !controls[0].disabled), 'Preview has unseen rows but no usable Next control');
    check(last !== total || !controls.length || controls[0].disabled, 'Preview row total contradicts Next control');
  }
  check(page || range || controls.length === 1, 'Preview pagination completeness is not observable');
  return {next: controls[0] && !controls[0].disabled ? controls[0].label : null,
    page: page ? Number(page[1]) : null, pages: page ? Number(page[2]) : null,
    range: range ? {first:Number(range[1]),last:Number(range[2]),total:Number(range[3])} : null};
}

export async function collectPreview(read, next) {
  let headers = null, all = [], text = [], previousPage = null;
  const seen = new Set();
  for (let index = 0; index < 1000; index++) {
    const state = await read();
    const matches = state.rows.filter(row => row.includes('sku') || row.includes('SKU'));
    check(matches.length === 1, 'Preview must expose one exact SKU table');
    const current = matches[0];
    check(!headers || JSON.stringify(headers) === JSON.stringify(current), 'Preview headers changed between pages');
    headers = current;
    const skuIndex = current.findIndex(value => value === 'sku' || value === 'SKU');
    const rows = state.rows.filter(row => row !== current && row[skuIndex]);
    const key = JSON.stringify(rows);
    check(!seen.has(key), 'Preview pagination repeated a page');
    seen.add(key); all.push(...rows); text.push(state.text);
    const navigation = pageNavigation(state);
    if(navigation.range) check(navigation.range.first === all.length-rows.length+1 && navigation.range.last === all.length, 'Preview range does not cover the collected rows');
    if (navigation.page !== null) {
      check(navigation.page === (previousPage === null ? 1 : previousPage + 1), 'Preview pagination skipped a page');
      previousPage = navigation.page;
    }
    if (!navigation.next) return {rows: [headers, ...all], text: text.join('\n'), page_count: index + 1};
    await next(navigation.next, state);
  }
  throw new Error('Preview exceeds pagination limit');
}

export async function durableReceipt(path, value) {
  const temporary = path + '.new';
  const handle = await open(temporary, 'w', 0o600);
  try { await handle.writeFile(JSON.stringify(value)); await handle.sync(); } finally { await handle.close(); }
  await rename(temporary, path);
  const directory = await open(dirname(path), 'r');
  try { await directory.sync(); } finally { await directory.close(); }
}

export async function reserveSubmission(path, value) {
  // O_EXCL closes the race even when two direct adapters share a browser owner.
  // A partial receipt after process death also blocks another submission.
  const handle = await open(path, 'wx', 0o600);
  try { await handle.writeFile(JSON.stringify(value)); await handle.sync(); } finally { await handle.close(); }
  const directory = await open(dirname(path), 'r');
  try { await directory.sync(); } finally { await directory.close(); }
}

export async function readAttempt(path, input) {
  let record;
  try { record = JSON.parse(await readFile(path, 'utf8')); }
  catch (error) { if (error.code === 'ENOENT') return null; throw error; }
  check(record.plan_hash === input.plan_hash && JSON.stringify(record.account) === JSON.stringify(input.plan.account), 'Import receipt differs from the bound account or plan');
  check(record.upload_sha256 === createHash('sha256').update(await readFile(input.plan.body.upload)).digest('hex'), 'Import receipt upload hash mismatch');
  if(record.identity_kind==='uploaded_file') {
    sameUploadedFile(record,uploadedFileIdentity(record.import_url,[record.upload_key+' (SKU)'],input.plan.account,record.upload_filename));
  } else check(importIdentity(record.import_url).import_id === record.import_id, 'Import receipt URL differs from its identity');
  return record;
}

export async function verifyImagePreflight(input, at = Date.now()) {
  if (input.plan.body.image_policy !== 'secondary_slots_only') return;
  const receipt = input.image_preflight;
  check(receipt?.path && receipt.sha256 && receipt.report_generated_at, 'Fresh image preflight evidence is required before submit');
  const age = at - Date.parse(receipt.report_generated_at);
  check(Number.isFinite(age) && age >= 0 && age <= 300000, 'Image preflight expired before submit');
  check(createHash('sha256').update(await readFile(receipt.path)).digest('hex') === receipt.sha256, 'Image preflight report changed');
}

export function recoveryStatus(statuses) {
  const supported = {Processing: 'processing', Pending: 'processing', Queued: 'processing', Completed: 'complete', Complete: 'complete', Failed: 'failed'};
  const values = [...new Set(statuses.map(value => String(value).trim()).filter(Boolean))];
  check(values.length === 1 && supported[values[0]], 'Exact import processing status is unavailable or contradictory');
  return supported[values[0]];
}
