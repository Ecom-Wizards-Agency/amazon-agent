/** Live public image slots from the observed Amazon ImageBlock contract. */
import { readFile } from 'node:fs/promises';
import { pathToFileURL } from 'node:url';
import { evaluate } from '../report-fetcher/cdp.mjs';
import { acquireTaskPage, releaseTaskPage, taskIdFor } from '../browserctl/task-tabs.mjs';
import { ensureDeliveryPostcode } from '../report-fetcher/marketplace-postcode.mjs';
import { check } from './browser-ui.mjs';

export function selectExactSlots(record, expectedAsin, wantedSlots) {
 check(record.resolved_asin===expectedAsin&&record.title,'Live image page resolved to another product or lacks a title');
 const output=[];
 for(const slot of wantedSlots){const matches=record.images.filter(x=>x.variant===slot);check(matches.length<=1,'Ambiguous repeated image slot');if(matches.length===1&&matches[0].url?.startsWith('https://'))output.push({slot,live_url:matches[0].url});}
 return output;
}
export async function collect(input) {
 const tld={US:'com',DE:'de',AU:'com.au',UK:'co.uk',IT:'it',FR:'fr',ES:'es',CA:'ca'}[input.account.marketplace];check(tld,'Unsupported image marketplace');
 const page=await acquireTaskPage({taskId:taskIdFor('amazon-operations',input.operation_id),slot:'public-images',workflow:'amazon-listing-capture',initialUrl:'about:blank'});
 let outcome='error';const images=[];
 try{
  for(const [sku,targets] of Object.entries(input.targets)){
   check(/^[A-Z0-9]{10}$/.test(targets.asin),'Valid bound ASIN required');
   await page.session.send('Page.navigate',{url:`https://www.amazon.${tld}/dp/${targets.asin}?th=1&psc=1`});
   const delivery=await ensureDeliveryPostcode(page.session,tld);check(delivery.ok,'Delivery location unavailable');
   const record=await evaluate(page.session,`(async()=>{
    for(let i=0;i<60&&!document.querySelector('#productTitle');i++)await new Promise(r=>setTimeout(r,250));
    const record={title:document.querySelector('#productTitle')?.textContent.trim(),resolved_asin:(location.pathname.match(/\\/dp\\/([A-Z0-9]{10})/)||[])[1],images:[],source_id:location.href};
    const script=[...document.querySelectorAll('script')].map(s=>s.textContent||'').find(text=>text.includes('colorImages')&&text.includes('initial'));
    if(script){const fragment=script.slice(script.indexOf('colorImages'));const start=fragment.indexOf('[');let depth=0,end=-1;for(let i=start;i<fragment.length;i++){if(fragment[i]==='[')depth++;else if(fragment[i]===']'&&--depth===0){end=i+1;break;}}if(end>start){try{record.images=JSON.parse(fragment.slice(start,end).replace(/'/g,'"')).map(x=>({variant:x.variant,url:x.hiRes||x.large}));}catch{}}}
    if(!record.images.some(x=>x.variant==='MAIN')){const main=document.querySelector('#landingImage');if(main)record.images.push({variant:'MAIN',url:main.getAttribute('data-old-hires')||main.src});}
    return record;
   })()`,30000);
   for(const item of selectExactSlots(record,targets.asin,targets.slots))images.push({sku,...item,source_id:record.source_id});
  }
  outcome='success';return{schema_version:1,account:input.account,plan_hash:input.plan_hash,status:'collected',observed_at:new Date().toISOString(),images};
 }catch(error){return{schema_version:1,status:'blocked',reason:'image_collection_unavailable',message:error.message};}
 finally{await releaseTaskPage(page,{outcome});}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){try{check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');console.log(JSON.stringify(await collect(JSON.parse(await readFile(process.argv[3],'utf8')))));}catch(error){console.log(JSON.stringify({schema_version:1,status:'blocked',reason:'collector_preflight',message:error.message}));process.exitCode=2;}}
