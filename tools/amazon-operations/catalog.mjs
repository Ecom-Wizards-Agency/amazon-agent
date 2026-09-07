/** Catalog upload adapter from observed Seller Central bulk-upload contracts. */
import { readFile } from 'node:fs/promises';
import { basename, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { acquireTaskPage,releaseTaskPage,taskIdFor } from '../browserctl/task-tabs.mjs';
import * as ui from './browser-ui.mjs';

export function verifyCatalogPreview(state,stage) {
  ui.check(state.text.includes('Preview file and fix errors'),'Catalog validation preview missing');
  const ready=/Ready to submit\s*(\d+)/i.exec(state.text),errors=/Action required\s*(\d+)/i.exec(state.text);
  ui.check(ready&&Number(ready[1])===stage.skus.length&&errors&&Number(errors[1])===0,'Catalog preview row counts or errors differ');
  ui.check(stage.skus.every(sku=>state.rows.some(row=>row.includes(sku))),'Catalog preview does not expose every exact SKU');
  ui.check(!state.aiEnabled,'AI-generated content cannot be enabled');
}
export async function run(input) {
  await ui.verifyEnvelope(input);
  const {plan}=input,stage=plan.body.stages[input.stage-1];
  ui.check(stage&&input.stage>=1,'Invalid catalog stage');
  const origin=ui.origins[plan.account.marketplace];ui.check(origin,'Unsupported marketplace');
  const page=await acquireTaskPage({taskId:taskIdFor('amazon-operations',plan.operation_id),workflow:'amazon-catalog',initialUrl:origin+'/home',exclusiveContext:true});
  let attempted=false,outcome='error';
  const result=data=>({schema_version:1,plan_hash:input.plan_hash,stage:input.stage,...data});
  try {
    await ui.context(page.session,plan.account,'catalog');
    await page.session.send('Page.navigate',{url:origin+'/product-search/bulk'});
    await ui.waitFor(()=>ui.snapshot(page.session),s=>/Upload a catalog(?:ue)? spreadsheet/.test(s.text));
    await ui.context(page.session,plan.account,'catalog');
    await ui.attach(page.session,stage.upload,{id:'kat-file-attachment'});
    let state=await ui.waitFor(()=>ui.snapshot(page.session),s=>s.files.includes(basename(stage.upload))||s.text.includes(basename(stage.upload)));
    ui.check(!state.aiEnabled,'AI-generated content cannot be enabled');
    await ui.context(page.session,plan.account,'catalog');
    await ui.click(page.session,'Validate your file');
    state=await ui.waitFor(()=>ui.snapshot(page.session),s=>s.text.includes('Preview file and fix errors'),120000);
    verifyCatalogPreview(state,stage);
    state=await ui.context(page.session,plan.account,'catalog');verifyCatalogPreview(state,stage);
    const evidence=join(dirname(input.receipt_path),`catalog-stage-${input.stage}-before-submit.png`);
    await ui.screenshot(page.session,evidence);
    await ui.receipt(input.receipt_path,result({status:'uncertain',reason:'before_submit',evidence}));
    attempted=true;
    await ui.click(page.session,null,{id:'submit-button'});
    state=await ui.waitFor(()=>ui.snapshot(page.session),s=>new URL(s.url).searchParams.has('reference_id'),20000);
    ui.check(ui.contextMatches(state,plan.account,'catalog'),'Context changed after submission');
    const id=new URL(state.url).searchParams.get('reference_id');ui.check(/^\d+$/.test(id),'Unexpected submission reference');
    outcome='success';const answer=result({status:'processing',submission_id:id,evidence,reason:'awaiting_processing_and_relationship_verification'});
    await ui.receipt(input.receipt_path,answer);return answer;
  } catch(error) {
    const answer=result({status:attempted?'uncertain':'blocked',reason:attempted?'submission_outcome_uncertain':'ui_contract_unavailable',message:error.message});
    await ui.receipt(input.receipt_path,answer);return answer;
  } finally {await releaseTaskPage(page,{outcome});}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href) {
  let input;try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');input=JSON.parse(await readFile(process.argv[3],'utf8'));console.log(JSON.stringify(await run(input)));}catch(error){console.log(JSON.stringify({schema_version:1,plan_hash:input?.plan_hash,status:'blocked',reason:'adapter_preflight',message:error.message}));process.exitCode=2;}
}
