/** Discover a selectable FFP account and prove its seller/marketplace IDs. */
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {acquireTaskPage,releaseTaskPage,taskIdFor} from '../browserctl/task-tabs.mjs';
import {evaluate} from '../report-fetcher/cdp.mjs';
import * as ui from './browser-ui.mjs';

const selector=`[...document.querySelectorAll('input[role="combobox"]')].filter(e=>e.getClientRects().length&&(e.parentElement.querySelector('legend')?.textContent||'').trim()==='Seller & Marketplace')`;
const norm=value=>String(value||'').replace(/\s+/g,' ').trim().toLowerCase();
export function selectCandidate(options,binding){
 const matches=options.filter(o=>norm(o.label)===norm(binding.seller_name)&&norm(o.country)===norm(binding.marketplace_name));
 ui.check(matches.length===1,'FlatFilePro account option is unavailable or ambiguous');return matches[0];
}
export function authorizedBinding(body,account){
 const rows=body?.sp_api_authorized_marketplaces||body?.data?.sp_api_authorized_marketplaces;
 ui.check(Array.isArray(rows),'FlatFilePro authorized marketplace response unavailable');
 const matches=rows.filter(r=>r.selling_partner_id===account.seller_id&&r.marketplace_id===account.marketplace_id);
 ui.check(matches.length===1&&matches[0].seller_name&&matches[0].marketplace_name,'FlatFilePro seller/marketplace binding is unavailable or ambiguous');
 const {seller_name,marketplace_name}=matches[0];return {seller_name,marketplace_name};
}
export function verifyBinding(observed,account){
 const url=new URL(observed.url);
 ui.check(url.origin==='https://app.flatfile.pro'&&url.pathname==='/amazon-listings-items','FlatFilePro binding requires the Listings page');
 ui.check(url.searchParams.getAll('sellerId').length===1&&url.searchParams.getAll('marketplaceId').length===1&&url.searchParams.get('sellerId')===account.seller_id&&url.searchParams.get('marketplaceId')===account.marketplace_id,'FlatFilePro selected seller/marketplace IDs differ');
 ui.check(typeof observed.display==='string'&&observed.display.trim()&&typeof observed.option==='string'&&observed.option.trim(),'FlatFilePro selector labels unavailable');
 return {seller_id:account.seller_id,marketplace_id:account.marketplace_id,flatfilepro_display_name:observed.display.trim(),flatfilepro_option_name:observed.option.trim(),source_url:url.href};
}
export async function discoverBinding(session,account){
 await session.assertTaskControl({exclusiveContext:true});
 let response,finished=new Set();
 await session.send('Network.enable');
 const stops=[session.subscribe('Network.responseReceived',p=>{const u=new URL(p.response.url);if(['XHR','Fetch'].includes(p.type)&&u.origin==='https://api.flatfile.pro'&&u.pathname==='/brands/get-authorized-marketplaces')response={id:p.requestId,status:p.response.status};}),session.subscribe('Network.loadingFinished',p=>finished.add(p.requestId))];
 try{
 await session.send('Page.navigate',{url:'https://app.flatfile.pro/exports'});
 await ui.waitFor(async()=>response,r=>r&&finished.has(r.id));
 ui.check(response.status===200,`FlatFilePro authorized marketplace read failed: HTTP ${response.status}`);
 const raw=await session.send('Network.getResponseBody',{requestId:response.id});
 const binding=authorizedBinding(JSON.parse(raw.base64Encoded?Buffer.from(raw.body,'base64').toString():raw.body),account);
 await ui.waitFor(()=>evaluate(session,`(()=>{const a=${selector};return location.origin==='https://app.flatfile.pro'&&a.length===1&&Boolean(a[0].value)})()`),Boolean);
 await evaluate(session,`(()=>{const a=${selector};if(a.length!==1)throw Error('Ambiguous account selector');const b=a[0].parentElement.querySelector('button[aria-label="Open"]');if(!b)throw Error('Account selector cannot open');b.click()})()`);
 const options=await ui.waitFor(()=>evaluate(session,`[...document.querySelectorAll('[role="option"]')].filter(e=>e.getClientRects().length).map((e,index)=>({label:e.innerText.trim(),country:e.parentElement.previousElementSibling?.innerText?.trim(),index}))`),a=>a.length>0);
 const chosen=selectCandidate(options,binding);
 await evaluate(session,`(()=>{const a=[...document.querySelectorAll('[role="option"]')].filter(e=>e.getClientRects().length),e=a[${chosen.index}];if(!e||e.innerText.trim()!==${JSON.stringify(chosen.label)})throw Error('Account option changed');e.click()})()`);
 await ui.waitFor(()=>evaluate(session,`(()=>{const a=${selector};return a.length===1&&a[0].value})()`),Boolean);
 await ui.clickFlatFilePro(session,'Listings');
 const observed=await ui.waitFor(()=>evaluate(session,`(()=>{const a=${selector};return {url:location.href,display:a.length===1?a[0].value:null}})()`),v=>new URL(v.url).pathname==='/amazon-listings-items'&&Boolean(v.display));
 await session.assertTaskControl({exclusiveContext:true});
 return verifyBinding({...observed,option:chosen.label},account);
 }finally{for(const stop of stops)if(typeof stop==='function')stop();}
}
export async function collect(input,deps={}){
 const common={schema_version:1,account:input.account,plan_hash:input.plan_hash,source_kind:'flatfilepro_account_binding'};
 let page,outcome='error';const now=deps.now||Date.now;
 const release=async()=>{if(page){const current=page;page=null;await(deps.release||releaseTaskPage)(current,{outcome,closeTarget:input.close_tab_after===true});}};
 const onSigterm=async()=>{try{await release();}finally{process.exit(143);}};
 process.once('SIGTERM',onSigterm);
 try{
  ui.check(input.schema_version===1&&input.operation_id&&/^[a-f0-9]{64}$/.test(input.plan_hash||''),'Invalid account binding request');
  ui.check(input.account?.seller_id&&input.account?.marketplace_id,'Account IDs are required');
  const minimum=Date.parse(input.minimum_after);ui.check(Number.isFinite(minimum)&&minimum<=now(),'Invalid binding read boundary');
  const directory=resolve(input.output_dir);await mkdir(directory,{recursive:true});
  page=await(deps.acquire||acquireTaskPage)({taskId:taskIdFor('amazon-operations',input.task_key||input.operation_id),slot:'ffp-account-binding',workflow:'amazon-flatfilepro',initialUrl:'https://app.flatfile.pro/exports',exclusiveContext:true});
  const binding=await(deps.discover||discoverBinding)(page.session,input.account);
  // Verify again at the collector boundary, including injected readers.
  const checked=verifyBinding({url:binding.source_url,display:binding.flatfilepro_display_name,option:binding.flatfilepro_option_name},input.account);
  const result={...common,...checked,status:'collected',verified:true,observed_at:new Date(now()).toISOString()};
  ui.check(Date.parse(result.observed_at)>=minimum,'Account binding is stale');
  const bytes=Buffer.from(JSON.stringify(result)),sha256=createHash('sha256').update(bytes).digest('hex'),path=join(directory,`account-binding-${sha256}.json`);
  await writeFile(path,bytes,{flag:'wx'}).catch(async error=>{if(error.code!=='EEXIST'||!(await readFile(path)).equals(bytes))throw error;});
  outcome='success';await release();return {...result,path,sha256};
 }catch(error){return {...common,status:'blocked',reason:'ffp_account_binding_unavailable',message:error.message};}
 finally{process.removeListener('SIGTERM',onSigterm);await release();}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');console.log(JSON.stringify(await collect(JSON.parse(await readFile(process.argv[3],'utf8')))));}catch(error){console.log(JSON.stringify({status:'blocked',reason:'collector_preflight',message:error.message}));process.exitCode=2;}}
