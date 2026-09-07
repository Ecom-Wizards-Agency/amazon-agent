/** FlatFilePro upload/map/apply driver. Requires a scoped canary; no live calls in tests. */
import { readFile } from 'node:fs/promises';
import { basename, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { acquireTaskPage,releaseTaskPage,taskIdFor } from '../browserctl/task-tabs.mjs';
import * as ui from './browser-ui.mjs';

export function verifyPreview(state,body) {
  const headers=state.rows.find(r=>r.includes('sku')||r.includes('SKU'));
  ui.check(headers,'Preview must expose exact table headers');
  const skuIndex=headers.findIndex(x=>x==='sku'||x==='SKU');
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
  const page=await acquireTaskPage({taskId:taskIdFor('amazon-operations',plan.operation_id),workflow:'amazon-flatfilepro',initialUrl:'https://app.flatfile.pro',exclusiveContext:true});
  let attempted=false,outcome='error';
  const result=data=>({schema_version:1,plan_hash:input.plan_hash,...data});
  try {
    let state=await ui.context(page.session,plan.account,'ffp');
    // Always start a fresh import, never apply an old mapped preview.
    await ui.click(page.session,'Upload');
    await ui.waitFor(()=>ui.snapshot(page.session),s=>s.controls.some(c=>c.label==='UPLOAD FILE'));
    await ui.context(page.session,plan.account,'ffp');
    await ui.attach(page.session,body.upload);
    state=await ui.waitFor(()=>ui.snapshot(page.session),s=>s.text.includes(basename(body.upload))||s.files.includes(basename(body.upload)));
    await ui.click(page.session,'SKU');
    await ui.fill(page.session,'Search file columns','sku');
    await ui.click(page.session,'sku');
    for(const field of body.mapping) {
      await ui.context(page.session,plan.account,'ffp');
      await ui.fill(page.session,'Search file columns',field);
      state=await ui.waitFor(()=>ui.snapshot(page.session),s=>s.controls.some(c=>c.label===field));
      await ui.click(page.session,field);
      await ui.fill(page.session,'Search attributes',field);
      state=await ui.waitFor(()=>ui.snapshot(page.session),s=>s.controls.some(c=>c.label===field||c.label.endsWith(`(${field})`)));
      const candidates=state.controls.filter(c=>c.label===field||c.label.endsWith(`(${field})`));
      ui.check(candidates.length===1,'Ambiguous exact attribute option');
      await ui.click(page.session,candidates[0].label);
      await ui.click(page.session,'MAP ATTRIBUTES');
    }
    state=await ui.context(page.session,plan.account,'ffp');
    verifyPreview(state,body);
    const evidence=join(dirname(input.receipt_path),'flatfilepro-before-apply.png');
    await ui.screenshot(page.session,evidence);
    await ui.receipt(input.receipt_path,result({status:'uncertain',reason:'before_apply',evidence}));
    attempted=true;
    await ui.click(page.session,'Update Listings');
    state=await ui.waitFor(()=>ui.snapshot(page.session),s=>!s.controls.some(c=>c.label==='Update Listings'),15000);
    ui.check(ui.contextMatches(state,plan.account,'ffp'),'Context changed after apply');
    const url=new URL(state.url);
    const id=url.searchParams.get('importId')||url.searchParams.get('import_id')||(/\/(?:imports|uploads)\/([A-Za-z0-9-]+)(?:\/|$)/.exec(url.pathname)||[])[1];
    ui.check(id,'Applied but no unambiguous import reference; reconcile before retry');
    outcome='success';
    const answer=result({status:'processing',submission_id:id,reason:'awaiting_amazon_processing',evidence});
    await ui.receipt(input.receipt_path,answer);return answer;
  } catch(error) {
    const answer=result({status:attempted?'uncertain':'blocked',reason:attempted?'apply_outcome_uncertain':'ui_contract_unavailable',message:error.message});
    await ui.receipt(input.receipt_path,answer);return answer;
  } finally {await releaseTaskPage(page,{outcome});}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href) {
  let input;try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');input=JSON.parse(await readFile(process.argv[3],'utf8'));console.log(JSON.stringify(await run(input)));}catch(error){console.log(JSON.stringify({schema_version:1,plan_hash:input?.plan_hash,status:'blocked',reason:'adapter_preflight',message:error.message}));process.exitCode=2;}
}
