/** Observed FFP /exports workflow, isolated from listing submissions. */
// Request envelope: optional task_key (stable job string) overrides input.operation_id for browser tabs only.
// Optional top-level close_tab_after === true closes the task tab at release.
// Keep task_key outside plan; operation_id still identifies receipts and revisions.
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { createHash } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';
import https from 'node:https';
import { evaluate } from '../report-fetcher/cdp.mjs';
import { acquireTaskPage, releaseTaskPage, closeReleasedTaskPage, taskIdFor } from '../browserctl/task-tabs.mjs';
import { durableReceipt, reserveSubmission } from './flatfilepro-contracts.mjs';
import * as ui from './browser-ui.mjs';

export const MARKER_EXPIRY_MS=24*60*60*1000;
// The exact browser-ui context failure; matched verbatim, never by substring.
export const CONTEXT_UNVERIFIED='Exact selected account/marketplace cannot be verified against live IDs or a uniquely bound registry label';

const EXPORT_ORIGIN='https://ffp-export.s3.us-east-2.amazonaws.com';
const NAME=/^all-(\d{4})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{3})\.xlsx$/;
const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');

export function exportDate(name) {
  const match=NAME.exec(name);
  ui.check(match,'Unsupported FFP export filename');
  const value=`${match[1]}-${match[2]}-${match[3]}T${match[4]}:${match[5]}:${match[6]}.${match[7]}Z`;
  const timestamp=Date.parse(value);
  ui.check(Number.isFinite(timestamp)&&new Date(timestamp).toISOString()===value,'Invalid FFP export UTC timestamp');
  return value;
}

export function validateExportLink(link,account) {
  ui.check(/^[A-Z0-9]+$/.test(account.seller_id||'')&&/^[A-Z0-9]+$/.test(account.marketplace_id||''),'Verified seller and marketplace IDs are required');
  const date=exportDate(link.name),url=new URL(link.href);
  ui.check(url.origin===EXPORT_ORIGIN&&!url.username&&!url.password&&!url.search&&!url.hash &&
    url.pathname===`/${account.seller_id}-${account.marketplace_id}/${link.name}`,'FFP export link does not match the observed host and exact seller/marketplace path');
  return {...link,generated_at:date};
}

export function selectCompletedExport(state,marker,account,minimumAfter,at=Date.now()) {
  const minimum=Math.max(Date.parse(minimumAfter),Date.parse(marker.requested_at));
  ui.check(Number.isFinite(minimum),'Invalid export freshness boundary');
  const candidates=[];
  for(const link of state.links) {
    if(!NAME.test(link.name)||marker.before_names.includes(link.name))continue;
    const candidate=validateExportLink(link,account);
    const time=Date.parse(candidate.generated_at);
    ui.check(time<=at,'Export filename timestamp is in the future');
    if(time>=minimum)candidates.push(candidate);
  }
  ui.check(candidates.length<=1,'More than one new FFP export matches this request; do not guess');
  if(!candidates.length)return null;
  // The completion notice is a transient toast, so a resumed page never shows it again.
  // Whenever the page still carries one it must name this exact seller and marketplace; a notice
  // for other IDs is never acceptable. With no notice at all, the single candidate stays bound by
  // what a resume can still verify: the public bucket and exact /<seller>-<marketplace>/ path from
  // validateExportLink, the marker's before_names and the filename timestamp checked above.
  const notices=[...state.text.matchAll(/Export of listings complete for ([A-Z0-9]+) on marketplace ([A-Z0-9]+), download it now\./g)];
  ui.check(!notices.length||notices.some(m=>m[1]===account.seller_id&&m[2]===account.marketplace_id),'FFP export completion does not confirm the exact seller and marketplace');
  return candidates[0];
}

async function exportsState(session,account) {
  const state=await ui.context(session,account,'ffp');
  ui.check(new URL(state.url).pathname==='/exports','Expected the observed FFP exports page');
  const links=await evaluate(session,`(()=>[...document.querySelectorAll('a')].filter(el=>el.getBoundingClientRect().width>0&&el.getBoundingClientRect().height>0).map(el=>({name:(el.innerText||el.textContent||'').trim(),href:el.href})))()`);
  return {...state,links};
}

export function fetchExport(url,{maximumBytes=30*1024*1024,timeoutMs=90000}={}) {
  return new Promise((resolve,reject)=>{
    const request=https.get(url,{headers:{Accept:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, application/octet-stream'},timeout:timeoutMs},response=>{
      if(response.statusCode!==200){response.resume();reject(new Error(`FFP export download HTTP ${response.statusCode}; redirects are not followed`));return;}
      let size=0;const chunks=[];
      response.on('data',chunk=>{
        size+=chunk.length;
        if(size>maximumBytes){request.destroy(new Error('FFP export exceeds the 30 MiB limit'));return;}
        chunks.push(chunk);
      });
      response.on('error',reject);
      response.on('end',()=>resolve({bytes:Buffer.concat(chunks),content_type:response.headers['content-type']||null}));
    });
    request.on('timeout',()=>request.destroy(new Error('FFP export download timed out')));
    request.on('error',reject);
  });
}

export async function collect(input,dependencies={}) {
  const common={schema_version:1,account:input.account,plan_hash:input.plan_hash};
  let page,releasedPage,outcome='error';
  const acquire=dependencies.acquire||acquireTaskPage,release=dependencies.release||releaseTaskPage;
  const read=dependencies.read||exportsState,click=dependencies.click||ui.clickFlatFilePro,download=dependencies.download||fetchExport;
  const at=dependencies.now||(()=>Date.now());
  // The click re-renders the exports page with its completion toast, which briefly hides the
  // 'Seller & Marketplace' selector value. Retry that exact verification failure, as
  // catalog-export.mjs does after navigation; every other failure still blocks immediately.
  // Only reads that follow the click use this; the read gating the click stays strict.
  const readAfterClick=async(session,account,{timeoutMs=15000,intervalMs=500}={})=>{
    const end=Date.now()+timeoutMs;
    for(;;) {
      try{return await read(session,account);}
      catch(error){
        if(error.message!==CONTEXT_UNVERIFIED||Date.now()>=end)throw error;
        await new Promise(done=>setTimeout(done,intervalMs));
      }
    }
  };
  const taskSpec={closeOnFailure:input.close_tab_after===true,taskId:taskIdFor('amazon-operations',input.task_key || input.operation_id),slot:'ffp-export',workflow:'amazon-flatfilepro',initialUrl:'https://app.flatfile.pro/exports',exclusiveContext:true};
  const onSigterm=async()=>{
    if(page?._released)return;
    try{if(page)await release(page,{outcome:'error',closeTarget:input.close_tab_after===true});if(releasedPage&&input.close_tab_after===true)await closeReleasedTaskPage(releasedPage);}
    catch(error){console.error('SIGTERM browser release failed:',error.message);}
    finally{process.exit(143);}
  };
  process.once('SIGTERM',onSigterm);
  try {
    ui.check(input.schema_version===1&&input.account&&input.operation_id&&/^[a-f0-9]{64}$/.test(input.plan_hash||'')&&input.output_dir&&Number.isFinite(Date.parse(input.minimum_after))&&Date.parse(input.minimum_after)<=at(),'Invalid FFP export collector request');
    const directory=resolve(input.output_dir);await mkdir(directory,{recursive:true});
    const markerPath=join(directory,'ffp-export-request.json');
    let marker;
    try{marker=JSON.parse(await readFile(markerPath,'utf8'));}catch(error){if(error.code!=='ENOENT')throw error;}
    if(marker) {
      ui.check(marker.plan_hash===input.plan_hash&&JSON.stringify(marker.account)===JSON.stringify(input.account)&&marker.minimum_after===input.minimum_after,'FFP export marker belongs to another account or operation revision');
      if(marker.state==='downloaded') {
        ui.check(resolve(marker.path)===join(directory,marker.name),'Saved export path escaped its run directory');
        validateExportLink({name:marker.name,href:marker.source_id},input.account);
        ui.check(Date.parse(marker.report_generated_at)>=Math.max(Date.parse(input.minimum_after),Date.parse(marker.requested_at)),'Saved export predates this request');
        ui.check(sha256(await readFile(marker.path))===marker.sha256,'Saved FFP export changed');
        return {...common,...marker.result,status:'collected',observed_at:new Date(at()).toISOString()};
      }
    }
    const persistRequest=async(reserve=false,afterClick=false)=>{
      const targetId=page.targetId;
      releasedPage=page;
      await release(page,{outcome:'success'});page=null;
      if(reserve)await reserveSubmission(markerPath,marker);else await durableReceipt(markerPath,marker);
      page=await acquire({...taskSpec,expectedTargetId:targetId});releasedPage=null;
      ui.check(isDeepStrictEqual(JSON.parse(await readFile(markerPath,'utf8')),marker),'FFP export reservation changed during receipt write');
      return afterClick?readAfterClick(page.session,input.account):read(page.session,input.account);
    };
    page=await acquire(taskSpec);
    await page.session.send('Page.navigate',{url:'https://app.flatfile.pro/exports'});
    if(!dependencies.read) {
      await ui.waitFor(()=>ui.snapshot(page.session),value=>value.text.length>80);
      await ui.selectFlatFileProAccount(page.session,input.account);
    }
    let state=await read(page.session,input.account);
    if(!marker) {
      const buttons=state.controls.filter(c=>c.label==='EXPORT ALL LISTINGS');
      ui.check(buttons.length===1&&!buttons[0].disabled,'Exact EXPORT ALL LISTINGS control is unavailable or busy');
      marker={schema_version:1,account:input.account,plan_hash:input.plan_hash,minimum_after:input.minimum_after,
        requested_at:new Date(at()).toISOString(),before_names:[...new Set(state.links.filter(l=>NAME.test(l.name)).map(l=>l.name))],state:'request_outcome_unknown'};
      state=await persistRequest(true);
      ui.check(state.controls.filter(c=>c.label==='EXPORT ALL LISTINGS'&&!c.disabled).length===1&&
        JSON.stringify([...new Set(state.links.filter(l=>NAME.test(l.name)).map(l=>l.name))])===JSON.stringify(marker.before_names),'FFP export state changed during receipt write');
      // The marker survives a lost click response. Resume observes, never clicks again.
      try {await click(page.session,'EXPORT ALL LISTINGS');}
      catch(error){outcome='success';return {...common,status:'processing',reason:'ffp_export_request_outcome_unknown',message:error.message,report_request:markerPath,observed_at:new Date(at()).toISOString()};}
      marker.state='requested';state=await persistRequest(false,true);
    }
    let selected=selectCompletedExport(state,marker,input.account,input.minimum_after,at());
    if(!selected&&!dependencies.read){
      // The account selector renders before the export history finishes loading.
      // Re-read this request's completion link; never issue another export click.
      try{
        selected=await ui.waitFor(async()=>selectCompletedExport(await read(page.session,input.account),marker,input.account,input.minimum_after,at()),Boolean,10000);
      }catch(error){if(error.message!=='Expected page state did not appear')throw error;}
    }
    if(!selected){
      const expired=at()-Date.parse(marker.requested_at)>=MARKER_EXPIRY_MS;
      outcome=expired?'error':'success';return {...common,status:expired?'blocked':'processing',reason:expired?'marker_expired':'ffp_export_pending',report_request:markerPath,observed_at:new Date(at()).toISOString()};
    }
    await read(page.session,input.account); // Verify ownership before leaving the browser.
    await release(page,{outcome:'success',closeTarget:input.close_tab_after===true});
    page=null;
    // Download only the publicly readable observed S3 object, without cookies or browser routing.
    const downloaded=await download(selected.href);
    ui.check(downloaded.bytes.length>4&&downloaded.bytes.subarray(0,2).toString()==='PK','FFP export is not an XLSX ZIP file');
    page=await acquire(taskSpec);
    ui.check(isDeepStrictEqual(JSON.parse(await readFile(markerPath,'utf8')),marker),'FFP export reservation changed during download');
    await page.session.send('Page.navigate',{url:'https://app.flatfile.pro/exports'});
    if(!dependencies.read){
      await ui.waitFor(()=>ui.snapshot(page.session),value=>value.text.length>80);
    }
    await read(page.session,input.account); // Account ownership remains valid through retrieval.
    await release(page,{outcome:'success',closeTarget:input.close_tab_after===true});
    page=null;
    const path=join(directory,selected.name);await writeFile(path,downloaded.bytes,{flag:'wx'}).catch(async error=>{
      if(error.code!=='EEXIST')throw error;
      ui.check(sha256(await readFile(path))===sha256(downloaded.bytes),'Existing export file differs; preserve it for inspection');
    });
    const result={path,sha256:sha256(downloaded.bytes),source_id:selected.href,report_generated_at:selected.generated_at,
      report_type:'FlatFilePro all listings export',complete_report:true,content_type:downloaded.content_type};
    marker={...marker,state:'downloaded',name:selected.name,...result,result};
    await durableReceipt(markerPath,marker);
    outcome='success';return {...common,...result,status:'collected',observed_at:new Date(at()).toISOString()};
  }catch(error){return {...common,status:'blocked',reason:'ffp_export_collection_unavailable',message:error.message,observed_at:new Date(at()).toISOString()};}
  finally{process.removeListener('SIGTERM',onSigterm);if(page)await release(page,{outcome,closeTarget:input.close_tab_after===true});
    if(releasedPage&&input.close_tab_after===true)await closeReleasedTaskPage(releasedPage);}
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');console.log(JSON.stringify(await collect(JSON.parse(await readFile(process.argv[3],'utf8')))));}
  catch(error){console.log(JSON.stringify({schema_version:1,status:'blocked',reason:'collector_preflight',message:error.message}));process.exitCode=2;}
}
