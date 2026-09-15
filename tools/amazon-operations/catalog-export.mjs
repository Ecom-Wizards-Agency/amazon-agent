/** Fresh Category Listings Report collector. Generates reports, never catalog writes. */
// Optional top-level task_key shares job tabs; complete_task === true completes them after release.
// Optional top-level close_tab_after === true closes the task tab at release.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { join } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';
import { evaluate } from '../report-fetcher/cdp.mjs';
import { acquireTaskPage, releaseTaskPage, closeReleasedTaskPage, completeBrowserTask, taskIdFor } from '../browserctl/task-tabs.mjs';
import * as ui from './browser-ui.mjs';
import { reserveSubmission } from './flatfilepro-contracts.mjs';

export const MARKER_EXPIRY_MS=24*60*60*1000;

export function matchingCompletedReports(statuses, marker, minimumAfter) {
  const minimum=Math.max(Date.parse(marker.requested_at),Date.parse(minimumAfter));
  ui.check(Number.isFinite(minimum),'Unparseable report freshness boundary');
  return statuses.filter(entry=>{
    const type=entry.reportType||{};
    const exact=[type.translationStringId,type.name,type.label,type.value].some(v=>v===marker.report_value||v===marker.report_label);
    const date=Date.parse(entry.submissionDate);
    return exact&&entry.processingState?.name==='DONE'&&Number.isFinite(date)&&date>=minimum;
  }).sort((a,b)=>Date.parse(b.submissionDate)-Date.parse(a.submissionDate));
}
async function statuses(session) {
  return evaluate(session,`(async()=>{const response=await fetch(location.origin+'/listing/api/status/inventory-reports',{credentials:'same-origin',headers:{Accept:'application/json'}});if(!response.ok)throw new Error('Report status HTTP '+response.status);const data=await response.json();return data.statuses||[];})()`);
}
async function selectReport(session) {
  const selected=await evaluate(session,`(()=>{
    const roots=[document],els=[];for(let i=0;i<roots.length;i++)for(const el of roots[i].querySelectorAll('*')){els.push(el);if(el.shadowRoot)roots.push(el.shadowRoot);}
    const label='Category Listings Report';const clean=x=>String(x||'').replace(/\\s+/g,' ').trim();
    const options=els.filter(el=>el.tagName==='OPTION'&&clean(el.textContent)===label);
    if(options.length===1&&options[0].parentElement?.tagName==='SELECT'){
      const select=options[0].parentElement;select.value=options[0].value;select.dispatchEvent(new Event('input',{bubbles:true}));select.dispatchEvent(new Event('change',{bubbles:true}));
      return {report_value:options[0].value,report_label:label};
    }
    return null;
  })()`);
  if(selected) return selected;
  // Only the documented semantic controls are eligible; no guessed nearby report.
  await ui.click(session,'Select Report Type');
  await ui.click(session,'Category Listings Report');
  const choice=await evaluate(session,`(()=>{const roots=[document],els=[];for(let i=0;i<roots.length;i++)for(const el of roots[i].querySelectorAll('*')){els.push(el);if(el.shadowRoot)roots.push(el.shadowRoot);}const choices=els.filter(el=>el.matches('kat-dropdown,select,[role="combobox"]')&&/Category Listings Report/.test(el.innerText||el.textContent||''));if(choices.length!==1)return null;return{report_value:choices[0].value||choices[0].getAttribute('value'),report_label:'Category Listings Report'};})()`);
  ui.check(choice?.report_value,'Selected Category Listings Report has no observable exact type identifier');return choice;
}
export async function collect(input) {
  ui.check(input.schema_version===1&&input.account&&input.operation_id&&input.minimum_after&&input.output_dir,'Invalid collector request');
  const origin=ui.origins[input.account.marketplace];ui.check(origin,'Unsupported marketplace');
  const directory=input.output_dir;await mkdir(directory,{recursive:true});
  const markerPath=join(directory,'report-request.json');
  const taskSpec={closeOnFailure:input.close_tab_after===true,taskId:taskIdFor('amazon-operations',input.task_key || input.operation_id),slot:'verification',workflow:'amazon-reporting',initialUrl:origin+'/listing/reports/ref=xx_invreport_favb_xx',exclusiveContext:true,sellerCentral:{marketplace:input.account.marketplace,origin}};
  let page,releasedPage,outcome='error';
  const persistRequest=async(marker,reserve=false)=>{
    const targetId=page.targetId;
    releasedPage=page;
    await releaseTaskPage(page,{outcome:'success'});page=null;
    if(reserve)await reserveSubmission(markerPath,marker);else await ui.receipt(markerPath,marker);
    page=await acquireTaskPage({...taskSpec,expectedTargetId:targetId});releasedPage=null;
    ui.check(isDeepStrictEqual(JSON.parse(await readFile(markerPath,'utf8')),marker),'Report reservation changed during receipt write');
    const state=await ui.context(page.session,input.account,'catalog');
    ui.check(new URL(state.url).pathname.startsWith('/listing/reports'),'Report page changed during receipt write');
  };
  const onSigterm=async()=>{
    if(page?._released)return;
    try{if(page)await releaseTaskPage(page,{outcome:'error',closeTarget:input.close_tab_after===true});if(releasedPage&&input.close_tab_after===true)await closeReleasedTaskPage(releasedPage);}
    catch(error){console.error('SIGTERM browser release failed:',error.message);}
    finally{process.exit(143);}
  };
  process.once('SIGTERM',onSigterm);
  const common={schema_version:1,account:input.account,plan_hash:input.plan_hash,observed_at:new Date().toISOString()};
  try {
    page=await acquireTaskPage(taskSpec);
    // Navigation text renders before the account selector. Wait for the same
    // exact identity check used before every report action; never infer identity
    // from page length or accept a partially rendered header.
    await ui.waitFor(async()=>{
      try{return await ui.context(page.session,input.account,'catalog');}
      catch(error){
        if(error.message==='Exact selected account/marketplace cannot be verified against live IDs or a uniquely bound registry label')return null;
        throw error;
      }
    },Boolean);
    if(new URL((await ui.snapshot(page.session)).url).pathname.indexOf('/listing/reports')!==0){
      await page.session.send('Page.navigate',{url:origin+'/listing/reports/ref=xx_invreport_favb_xx'});
      await ui.waitFor(()=>ui.snapshot(page.session),s=>s.text.includes('Report'));
    }
    await ui.context(page.session,input.account,'catalog');
    let marker;
    if(existsSync(markerPath)) {
      marker=JSON.parse(await readFile(markerPath,'utf8'));
      ui.check(marker.plan_hash===input.plan_hash&&marker.minimum_after===input.minimum_after,'Report request belongs to another operation revision');
      // A completed reservation is still owned by this run; never replace it
      // with a second report request after a restart.
    }
    if(!marker) {
      const choice=await selectReport(page.session);
      await ui.context(page.session,input.account,'catalog');
      marker={...choice,plan_hash:input.plan_hash,minimum_after:input.minimum_after,requested_at:new Date().toISOString(),state:'request_outcome_unknown'};
      await persistRequest(marker,true); // Never repeat an unknown report-generation click after restart.
      ui.check(JSON.stringify(await selectReport(page.session))===JSON.stringify(choice),'Selected report changed during receipt write');
      await ui.context(page.session,input.account,'catalog');
      await ui.click(page.session,'Request Report');
      marker.state='requested';await persistRequest(marker);
    }
    await ui.context(page.session,input.account,'catalog');
    const completed=matchingCompletedReports(await statuses(page.session),marker,input.minimum_after);
    if(!completed.length){
      const expired=Date.now()-Date.parse(marker.requested_at)>=MARKER_EXPIRY_MS;
      outcome=expired?'error':'success';return{...common,status:expired?'blocked':'processing',reason:expired?'marker_expired':'fresh_category_report_pending',report_request:markerPath};
    }
    const report=completed[0];
    const links=(report.actions||[]).map(x=>x.link).filter(Boolean);
    ui.check(links.length===1,'Category report must expose one unambiguous download action');
    const url=new URL(links[0],origin);ui.check(url.origin===origin&&url.pathname.startsWith('/listing/'),'Report download link is outside observed listing-report route');
    await ui.context(page.session,input.account,'catalog');
    const content=await evaluate(page.session,`(async()=>{const response=await fetch(${JSON.stringify(url.href)},{credentials:'same-origin'});if(!response.ok)throw new Error('Report download HTTP '+response.status);const bytes=new Uint8Array(await response.arrayBuffer());if(bytes.length>30000000)throw new Error('Report exceeds 30 MB');let raw='';for(let i=0;i<bytes.length;i+=32768)raw+=String.fromCharCode(...bytes.subarray(i,i+32768));return{base64:btoa(raw),content_type:response.headers.get('content-type')};})()`,60000);
    await ui.context(page.session,input.account,'catalog');
    await page.session.assertTaskControl({exclusiveContext:true,sellerCentral:{marketplace:input.account.marketplace,origin}});
    outcome='success';
    await releaseTaskPage(page,{outcome,closeTarget:input.close_tab_after===true});
    page=null;
    const bytes=Buffer.from(content.base64,'base64');
    const extension=bytes.subarray(0,2).toString()==='PK'?'.xlsx':'.tsv';
    const path=join(directory,'category-listings'+extension);await writeFile(path,bytes);
    marker.state='downloaded';marker.downloaded_at=new Date().toISOString();await ui.receipt(markerPath,marker);
    outcome='success';return{...common,status:'collected',path,sha256:createHash('sha256').update(bytes).digest('hex'),source_id:url.href,report_generated_at:report.submissionDate,report_type:report.reportType,complete_report:true};
  }catch(error){return{...common,status:'blocked',reason:'category_report_collection_unavailable',message:error.message};}
  finally{
    process.removeListener('SIGTERM',onSigterm);
    if(page)await releaseTaskPage(page,{outcome,closeTarget:input.close_tab_after===true});
    if(releasedPage&&input.close_tab_after===true)await closeReleasedTaskPage(releasedPage);
    if(input.complete_task===true)await completeBrowserTask({taskId:taskIdFor('amazon-operations',input.task_key || input.operation_id)}).catch(error=>console.error('Browser task completion failed:',error.message));
  }
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');console.log(JSON.stringify(await collect(JSON.parse(await readFile(process.argv[3],'utf8')))));}
 catch(error){console.log(JSON.stringify({schema_version:1,status:'blocked',reason:'collector_preflight',message:error.message}));process.exitCode=2;}
}
