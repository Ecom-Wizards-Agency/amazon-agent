/** FlatFilePro upload/map/apply driver. Requires a scoped canary; no live calls in tests. */
import { readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { evaluate } from '../report-fetcher/cdp.mjs';
import { acquireTaskPage,releaseTaskPage,taskIdFor } from '../browserctl/task-tabs.mjs';
import * as ui from './browser-ui.mjs';
import { submitAttended, submittedRunIdentity } from './flatfilepro-submit.mjs';
import { collectPreview, destinationSearchField, durableReceipt, exactDestination, importIdentity, readAttempt, recoveryStatus, reserveSubmission, sameUploadedFile, uploadedFileIdentity, verifyImagePreflight, verifySelectedDestination } from './flatfilepro-contracts.mjs';

async function importForm(session,account) {
  const state=await ui.context(session,account,'ffp');
  const form=await evaluate(session,`(()=>{const visible=e=>e.getBoundingClientRect().width>0&&e.getBoundingClientRect().height>0;return{
    file_labels:[...document.querySelectorAll('[role="button"]')].filter(e=>visible(e)&&(e.parentElement.querySelector('legend')?.textContent||'').trim()==='File').map(e=>(e.innerText||e.textContent||'').trim()),
    radios:[...document.querySelectorAll('input[type="radio"]')].map(e=>({value:e.value,checked:e.checked})),
    inputs:[...document.querySelectorAll('input[role="combobox"]')].filter(visible).map(e=>({label:(e.parentElement.querySelector('legend')?.textContent||'').trim(),value:e.value})),
    options:[...document.querySelectorAll('[role="option"]')].filter(visible).map(e=>({label:(e.innerText||e.textContent||'').trim()}))};})()`);
  return {...state,...form};
}

async function selectSourceHeader(session,account,label,field) {
  await ui.context(session,account,'ffp');
  await evaluate(session,`(()=>{const inputs=[...document.querySelectorAll('input[role="combobox"]')].filter(e=>e.getBoundingClientRect().width>0&&(e.parentElement.querySelector('legend')?.textContent||'').trim()===${JSON.stringify(label)});if(inputs.length!==1)throw Error('Expected one labeled FlatFilePro autocomplete');inputs[0].focus();inputs[0].select()})()`);
  await session.send('Input.insertText',{text:field});
  const state=await ui.waitFor(()=>importForm(session,account),s=>s.options.length>0||s.text.includes('No options'));
  return state.options;
}

export async function stageImport(input,page) {
  const {plan}=input,account=plan.account,directory=dirname(input.receipt_path);
  const bytes=await readFile(plan.body.upload),hash=createHash('sha256').update(bytes).digest('hex');
  const filename=`ffp-${input.plan_hash}.xlsx`,path=join(directory,filename),journalPath=join(directory,'flatfilepro-upload.json');
  await writeFile(path,bytes,{flag:'wx'}).catch(async error=>{
    if(error.code!=='EEXIST')throw error;
    ui.check(createHash('sha256').update(await readFile(path)).digest('hex')===hash,'Previously staged workbook bytes changed');
  });
  let journal;
  try{journal=JSON.parse(await readFile(journalPath,'utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
  if(journal)ui.check(journal.plan_hash===input.plan_hash&&journal.upload_sha256===hash&&JSON.stringify(journal.account)===JSON.stringify(account),'Upload journal differs from the exact account or workbook');
  let state=await importForm(page.session,account);
  if(!journal) {
    ui.check(state.controls.some(c=>c.label==='UPLOAD EXCEL FILE'),'Observed UPLOAD EXCEL FILE control is unavailable');
    await evaluate(page.session,`(()=>{const radios=[...document.querySelectorAll('input[type="radio"]')].filter(e=>e.value==='sku');if(radios.length!==1)throw Error('Expected exact SKU identifier radio');if(!radios[0].checked)radios[0].click()})()`);
    state=await importForm(page.session,account);
    ui.check(state.radios.filter(r=>r.checked).length===1&&state.radios.find(r=>r.checked)?.value==='sku','SKU match basis was not selected');
    journal={schema_version:1,plan_hash:input.plan_hash,account,upload_sha256:hash,upload_filename:filename,state:'upload_outcome_unknown'};
    await reserveSubmission(journalPath,journal);
    await ui.attach(page.session,path);
    state=await ui.waitFor(()=>importForm(page.session,account),s=>s.file_labels.some(value=>value.endsWith(`-${filename} (SKU)`)),60000);
  } else if(!state.file_labels.some(value=>value.endsWith(`-${filename} (SKU)`))) {
    // Resume the exact previously uploaded file. A lost upload response never
    // causes another attachment of the same workbook.
    await evaluate(page.session,`(()=>{const buttons=[...document.querySelectorAll('[role="button"]')].filter(e=>e.getBoundingClientRect().width>0&&(e.parentElement.querySelector('legend')?.textContent||'').trim()==='File');if(buttons.length!==1)throw Error('Expected exact File selector');buttons[0].click()})()`);
    state=await ui.waitFor(()=>importForm(page.session,account),s=>s.options.length>0||s.text.includes('No options'));
    const candidate=uploadedFileIdentity(state.url,state.options.map(x=>x.label),account,filename);
    await ui.clickFlatFilePro(page.session,candidate.upload_key+' (SKU)');
    state=await importForm(page.session,account);
  }
  const identity=uploadedFileIdentity(state.url,state.file_labels,account,filename);
  if(journal.identity)sameUploadedFile(journal.identity,identity);
  journal={...journal,state:'uploaded',identity};await durableReceipt(journalPath,journal);
  if(!state.inputs.some(x=>x.label==='Search attribute headings')) {
    ui.check(state.controls.filter(c=>c.label==='IMPORT'&&!c.disabled).length===1,'Expected the observed IMPORT parsing control');
    await ui.clickFlatFilePro(page.session,'IMPORT');
    state=await ui.waitFor(()=>importForm(page.session,account),s=>s.inputs.some(x=>x.label==='Search attribute headings'));
  }
  sameUploadedFile(identity,uploadedFileIdentity(state.url,state.file_labels,account,filename));
  return identity;
}

export function verifyPreview(state,body) {
  const headers=state.rows.find(r=>r.includes('sku')||r.includes('SKU'));
  ui.check(headers,'Preview must expose exact table headers');
  const skuIndex=headers.findIndex(x=>x==='sku'||x==='SKU');
  const expectedFields = new Set(Object.values(body.expected_rows).flatMap(row => Object.keys(row)));
  const technical = headers.filter((_,i)=>i!==skuIndex).map(h => [...expectedFields].filter(f=>h===f||h.endsWith(`(${f})`)));
  ui.check(technical.every(matches=>matches.length===1) && new Set(technical.flat()).size===technical.length && technical.length===expectedFields.size,'Preview attribute mismatch: unexpected, duplicated, or missing mapped attribute');
  const data=state.rows.filter(r=>r!==headers && r[skuIndex]);
  ui.check(data.every(r=>Object.hasOwn(body.expected_rows,r[skuIndex])),'Preview contains an unrequested SKU');
  ui.check(data.length===Object.keys(body.expected_rows).length,'Preview SKU count mismatch or duplicated SKU');
  ui.check(new Set(data.map(r=>r[skuIndex])).size===data.length,'Duplicate preview rows');
  for(const row of data) for(const [field,value] of Object.entries(body.expected_rows[row[skuIndex]])) {
    const indexes=headers.map((h,i)=>h===field||h.endsWith(`(${field})`)?i:-1).filter(i=>i>=0);
    ui.check(indexes.length===1&&row[indexes[0]]===String(value),'Preview value or exact technical field mismatch');
  }
  ui.check(!/validation errors?|invalid value|force update/i.test(state.text),'Preview contains validation/force-update state');
  return true;
}
export async function run(input) {
  await ui.verifyEnvelope(input);
  const {plan}=input,body=plan.body;
  ui.check(body.adapter==='flatfilepro.cdp','Wrong adapter');
  const attemptPath=join(dirname(input.receipt_path),'flatfilepro-attempt.json');
  const prior=await readAttempt(attemptPath,input);
  if(input.mode==='reconcile') return reconcileImport(input,prior);
  if(prior?.submission_intent) return {schema_version:1,plan_hash:input.plan_hash,status:'uncertain',attempted:true,reason:'prior_submit_requires_reconciliation'};
  const page=await acquireTaskPage({taskId:taskIdFor('amazon-operations',plan.operation_id),workflow:'amazon-flatfilepro',initialUrl:'https://app.flatfile.pro/import',exclusiveContext:true});
  let attempted=false,outcome='error';
  const result=data=>({schema_version:1,plan_hash:input.plan_hash,...data});
  try {
    // A competing invocation may have submitted while this one waited for the
    // managed browser lock. Recheck only after exclusive ownership is acquired.
    if((await readAttempt(attemptPath,input))?.submission_intent) return result({status:'uncertain',attempted:true,reason:'prior_submit_requires_reconciliation'});
    let state=await ui.selectFlatFileProAccount(page.session,plan.account);
    if(new URL(state.url).pathname!=='/import') {
      await page.session.send('Page.navigate',{url:'https://app.flatfile.pro/import'});
      await ui.waitFor(()=>ui.snapshot(page.session),s=>s.controls.some(c=>c.label==='UPLOAD EXCEL FILE'));
    }
    const uploadIdentity=await stageImport(input,page);
    for(const field of body.mapping) {
      const headings=await selectSourceHeader(page.session,plan.account,'Search attribute headings',field);
      ui.check(headings.filter(c=>c.label===field).length===1,'Exact source workbook header is unavailable or ambiguous');
      await ui.clickFlatFilePro(page.session,field);
      const target=destinationSearchField(field);
      const destinations=await selectSourceHeader(page.session,plan.account,'Search attributes',target);
      const searched=await importForm(page.session,plan.account);
      const searchInputs=searched.inputs.filter(x=>x.label==='Search attributes');
      ui.check(searchInputs.length===1,'Expected one destination search input');
      const destination=exactDestination(destinations,target,searchInputs[0].value);
      await ui.clickFlatFilePro(page.session,destination.label);
      const selected=await importForm(page.session,plan.account);
      const selectedInputs=selected.inputs.filter(x=>x.label==='Search attributes');
      ui.check(selectedInputs.length===1,'Expected one selected destination input');
      verifySelectedDestination(selectedInputs[0].value,target);
      await ui.clickFlatFilePro(page.session,'MAP ATTRIBUTES');
    }
    state=await ui.context(page.session,plan.account,'ffp');
    const preview=await collectPreview(()=>ui.context(page.session,plan.account,'ffp'),async(label,before)=>{
      await ui.clickFlatFilePro(page.session,label);
      await ui.waitFor(()=>ui.snapshot(page.session),value=>JSON.stringify(value.rows)!==JSON.stringify(before.rows));
    });
    verifyPreview(preview,body);
    state=await ui.context(page.session,plan.account,'ffp');
    const currentUpload=await importForm(page.session,plan.account);
    sameUploadedFile(uploadIdentity,uploadedFileIdentity(state.url,currentUpload.file_labels,plan.account,uploadIdentity.upload_filename));
    let identity;
    try{identity=importIdentity(state.url);}catch{
      if(body.image_policy==='secondary_slots_only'&&(input.allow_attended_canary===true||input.allow_validated_image_adapter===true))identity=uploadIdentity;
      else throw new Error('ffp_submission_recovery_unverified: exact uploaded workbook '+uploadIdentity.upload_key+' is recorded, but /import exposes no verified submission-history reference; the adapter stopped before Update Listings');
    }
    const evidence=join(dirname(input.receipt_path),'flatfilepro-before-apply.png');
    await ui.screenshot(page,evidence,plan.account,'ffp');
    await verifyImagePreflight(input);
    state=await ui.context(page.session,plan.account,'ffp');
    if(identity.identity_kind==='uploaded_file') {
      const fresh=await importForm(page.session,plan.account);
      sameUploadedFile(identity,uploadedFileIdentity(fresh.url,fresh.file_labels,plan.account,identity.upload_filename));
    } else ui.check(importIdentity(state.url).import_id===identity.import_id,'Import identity changed before submit');
    attempted=true; // A failed/existing reservation is uncertain, never retryable.
    const attempt={schema_version:1,plan_hash:input.plan_hash,account:plan.account,...identity,
      upload_sha256:createHash('sha256').update(await readFile(body.upload)).digest('hex'),
      submission_intent:true,started_at:new Date().toISOString(),preview_pages:preview.page_count,evidence};
    if(identity.identity_kind==='uploaded_file') {
      const submitted=await submitAttended({session:page.session,click:()=>ui.clickFlatFilePro(page.session,'Update Listings'),attemptPath,attempt});
      await ui.context(page.session,plan.account,'ffp');
      outcome='success';
      const answer=result({status:'processing',attempted:true,...submitted,reason:'awaiting_amazon_processing',evidence});
      await ui.receipt(input.receipt_path,answer);return answer;
    }
    await reserveSubmission(attemptPath,attempt);
    await ui.clickFlatFilePro(page.session,'Update Listings');
    state=await ui.waitFor(()=>ui.snapshot(page.session),s=>!s.controls.some(c=>c.label==='Update Listings'),15000);
    ui.check(ui.contextMatches(state,plan.account,'ffp'),'Context changed after apply');
    const id=importIdentity(state.url).import_id;
    ui.check(id===identity.import_id,'Import identity changed after submit; reconcile original import');
    outcome='success';
    const answer=result({status:'processing',attempted:true,submission_id:id,reason:'awaiting_amazon_processing',evidence});
    await ui.receipt(input.receipt_path,answer);return answer;
  } catch(error) {
    const specific=['ffp_image_slot_unverifiable','ffp_submission_recovery_unverified'].find(code=>error.message.startsWith(code+':'));
    const answer=result({status:attempted?'uncertain':'blocked',attempted,reason:attempted?'apply_outcome_uncertain':specific||'ui_contract_unavailable',message:error.message});
    await ui.receipt(input.receipt_path,answer);return answer;
  } finally {await releaseTaskPage(page,{outcome});}
}

export async function reconcileImport(input, attempt) {
  const common={schema_version:1,account:input.plan.account,plan_hash:input.plan_hash,observed_at:new Date().toISOString()};
  if(!attempt?.submission_intent) return {...common,status:'blocked',reason:'no_durable_import_identity'};
  if(attempt.identity_kind==='uploaded_file') {
    if(attempt.submission_id) {
      const identity=submittedRunIdentity({runId:attempt.submission_id});
      ui.check(identity.submission_url===attempt.submission_url&&Number.isFinite(Date.parse(attempt.submission_response_at)),'Captured submission receipt is incomplete or changed');
      return {...common,status:'collected',submission_id:identity.submission_id,source_id:identity.submission_url,
        processing_status:'processing',collection:'Recovered durable submission response; Amazon image verification remains required'};
    }
    return {...common,status:'blocked',reason:'ffp_submission_recovery_unverified',message:'The server upload key is preserved, but upload alone does not prove submission. Activity history correlation is required; no upload or Update Listings click was repeated.'};
  }
  const page=await acquireTaskPage({taskId:taskIdFor('amazon-operations',input.plan.operation_id),workflow:'amazon-flatfilepro',initialUrl:attempt.import_url,exclusiveContext:true});
  let outcome='error';
  try {
    await ui.context(page.session,input.plan.account,'ffp');
    await page.session.send('Page.navigate',{url:attempt.import_url});
    await ui.waitFor(()=>ui.snapshot(page.session),state=>state.text.length>0);
    const state=await ui.context(page.session,input.plan.account,'ffp');
    ui.check(importIdentity(state.url).import_id===attempt.import_id,'Recovery opened another import');
    const statuses=await evaluate(page.session,`(()=>[...document.querySelectorAll('[data-testid="import-status"],[data-test="import-status"],[aria-label="Import status"]')].filter(el=>el.getBoundingClientRect().width>0&&el.getBoundingClientRect().height>0).map(el=>el.innerText||el.textContent))()`);
    const processing=recoveryStatus(statuses);
    outcome='success';
    return {...common,status:'collected',source_id:attempt.import_url,submission_id:attempt.import_id,processing_status:processing};
  }catch(error){return {...common,status:'blocked',reason:'import_recovery_unavailable',message:error.message};}
  finally{await releaseTaskPage(page,{outcome});}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href) {
  let input;try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');input=JSON.parse(await readFile(process.argv[3],'utf8'));console.log(JSON.stringify(await run(input)));}catch(error){console.log(JSON.stringify({schema_version:1,plan_hash:input?.plan_hash,status:'blocked',reason:'adapter_preflight',message:error.message}));process.exitCode=2;}
}
