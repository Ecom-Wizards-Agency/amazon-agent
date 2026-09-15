/** Exact public slots with independent ASIN observations and bounded retries. */
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {evaluate} from '../report-fetcher/cdp.mjs';
import {acquireTaskPage,releaseTaskPage,taskIdFor} from '../browserctl/task-tabs.mjs';
import {ensureDeliveryPostcode,assertDeliveryPostcode} from '../report-fetcher/marketplace-postcode.mjs';
import {check} from './browser-ui.mjs';

export function selectExactSlots(record,expectedAsin,wantedSlots) {
 check(record.resolved_asin===expectedAsin&&record.title,'Live image page resolved to another product or lacks a title');
 check(!record.selected_asin||record.selected_asin===expectedAsin,'Selected variation differs from requested ASIN');
 const output=[];
 for(const slot of wantedSlots){const matches=record.images.filter(x=>x.variant===slot);check(matches.length<=1,'Ambiguous repeated image slot');if(matches.length===1&&matches[0].url?.startsWith('https://'))output.push({slot,live_url:matches[0].url});}
 return output;
}

/** Runs in the page; exported for fixtures. Never reads session storage. */
export function readImageRecord() {
 const record={title:document.querySelector('#productTitle')?.textContent.trim(),
  resolved_asin:(location.pathname.match(/\/dp\/([A-Z0-9]{10})/)||[])[1],
  selected_asin:document.querySelector('input#ASIN')?.value||null,images:[],source_id:location.href};
 // Everything stays inside this function because it is serialized into the page.
 // Decode a literal only. Never invoke Amazon's parseJSON or execute script text.
 const quoted=(source,start)=>{
  const quote=source[start];if(quote!=="'"&&quote!=='"')throw new Error('Expected quoted image JSON');
  let value='';
  for(let i=start+1;i<source.length;i++){
   let c=source[i];if(c===quote)return {value,end:i+1};
   if(c==='\n'||c==='\r')throw new Error('Unescaped newline in image string');
   if(c!=='\\'){value+=c;continue;}
   c=source[++i];
   const escapes={"'":"'",'"':'"','\\':'\\','/':'/','b':'\b','f':'\f','n':'\n','r':'\r','t':'\t','v':'\v'};
   if(Object.hasOwn(escapes,c)){value+=escapes[c];continue;}
   if(c==='0'&&!/[0-9]/.test(source[i+1]||'')){value+='\0';continue;}
   if(c==='x'||c==='u'){
    const count=c==='x'?2:4,hex=source.slice(i+1,i+1+count);
    if(hex.length!==count||!/^[a-f0-9]+$/i.test(hex))throw new Error('Invalid hex escape in image string');
    value+=String.fromCharCode(parseInt(hex,16));i+=count;continue;
   }
   throw new Error('Unsupported escape in image string');
  }
  throw new Error('Unterminated image string');
 };
 const balanced=(source,start)=>{
  const stack=[];
  for(let i=start;i<source.length;i++){
   const c=source[i];
   if(c==='"'||c==="'"){i=quoted(source,i).end-1;continue;}
   if(c==='['||c==='{')stack.push(c);
   else if(c===']'||c==='}'){
    if(stack.pop()!==(c===']'?'[':'{'))throw new Error('Unbalanced image payload');
    if(!stack.length)return i+1;
   }
  }
  throw new Error('Unterminated image payload');
 };
 const space=(s,i)=>{while(/\s/.test(s[i]||'')&&i<s.length)i++;return i;};
 const candidates=[];
 for(const script of document.querySelectorAll('script')){
  const source=script.textContent||'';
  const colors=/['"]colorImages['"]\s*:\s*\{/g;
  let color;
  while((color=colors.exec(source))){
   const start=colors.lastIndex-1,end=balanced(source,start);
   let depth=1;
   for(let i=start+1;i<end-1;i++){
    const c=source[i];
    if(c!=='"'&&c!=="'"){if(c==='{'||c==='[')depth++;else if(c==='}'||c===']')depth--;continue;}
    const key=quoted(source,i);i=key.end-1;
    let at=space(source,key.end);
    if(depth!==1||key.value!=='initial'||source[at]!==':')continue;
    at=space(source,at+1);let payload,after;
    if(source[at]==='['){after=balanced(source,at);payload=JSON.parse(source.slice(at,after));}
    else{
     const call=/^A\.\$\.parseJSON\s*\(\s*/.exec(source.slice(at));
     if(!call)throw new Error('Unsupported initial image expression');
     const literal=quoted(source,at+call[0].length);after=space(source,literal.end);
     if(source[after]!==')')throw new Error('Image parseJSON requires one literal argument');
     after++;payload=JSON.parse(literal.value);
    }
    after=space(source,after);
    if(![',','}'].includes(source[after]))throw new Error('Image payload cannot contain executable expressions');
    if(!Array.isArray(payload)||!payload.length||payload.some(x=>!x||typeof x!=='object'||typeof x.variant!=='string'||typeof(x.hiRes||x.large)!=='string'))throw new Error('Invalid image array');
    candidates.push(payload.map(x=>({variant:x.variant,url:x.hiRes||x.large})));i=after-1;
   }
   colors.lastIndex=end;
  }
 }
 if(candidates.length){
  const first=JSON.stringify(candidates[0]);
  if(candidates.some(x=>JSON.stringify(x)!==first))throw new Error('Conflicting initial image arrays');
  record.images=candidates[0];
 }
 if(!record.images.some(x=>x.variant==='MAIN')){const main=document.querySelector('#landingImage');if(main)record.images.push({variant:'MAIN',url:main.getAttribute('data-old-hires')||main.src});}
 return record;
}

/** Only fresh successful observations from a partial run can skip a retry. */
export async function collectByAsin(input,readAsin,clock=()=>Date.now()) {
 const groups=new Map();
 for(const [sku,target] of Object.entries(input.targets)){
  check(/^[A-Z0-9]{10}$/.test(target.asin),'Valid bound ASIN required');
  check(Array.isArray(target.slots)&&target.slots.length&&new Set(target.slots).size===target.slots.length,'Unique requested slots required');
  check(target.slots.every(slot=>/^(MAIN|SWCH|PT0[1-9])$/.test(slot)),'Unsupported image slot');
  const group=groups.get(target.asin)||{slots:new Set(),skus:[]};
  target.slots.forEach(slot=>group.slots.add(slot));group.skus.push(sku);groups.set(target.asin,group);
 }
 const previous=input.previous;
 const canResume=previous?.status==='partial'&&previous.operation_id===input.operation_id&&previous.plan_hash===input.plan_hash&&JSON.stringify(previous.account)===JSON.stringify(input.account);
 const images=[],observations=[],errors=[];
 const started=clock();
 for(const [asin,group] of groups){
  const prior=canResume&&previous.observations?.find(x=>x.asin===asin&&x.complete===true&&
   Number.isFinite(Date.parse(x.observed_at))&&clock()-Date.parse(x.observed_at)>=0&&clock()-Date.parse(x.observed_at)<900000&&
   [...group.slots].every(slot=>x.images.some(image=>image.slot===slot)));
  try{
   check(prior||clock()-started<180000,'Collection time budget exhausted; retry remaining ASINs');
   const observation=prior||await readAsin(asin,[...group.slots]);
   check(observation.asin===asin&&observation.source_id?.startsWith('https://')&&Number.isFinite(Date.parse(observation.observed_at)),'ASIN observation identity or time missing');
   const found=new Set(observation.images.map(x=>x.slot));
   check(found.size===observation.images.length&&observation.images.every(x=>group.slots.has(x.slot)),'Duplicate or unexpected observed slot');
   const complete=[...group.slots].every(slot=>found.has(slot));
   observations.push({...observation,complete});
   if(!complete)errors.push({asin,reason:'missing_slots',slots:[...group.slots].filter(slot=>!found.has(slot))});
   for(const sku of group.skus)for(const image of observation.images)
    if(input.targets[sku].slots.includes(image.slot))images.push({sku,asin,...image,source_id:observation.source_id,observed_at:observation.observed_at});
  }catch(error){errors.push({asin,reason:'image_collection_unavailable',message:error.message});}
 }
 return {schema_version:1,account:input.account,operation_id:input.operation_id,plan_hash:input.plan_hash,
  status:errors.length?(observations.length?'partial':'blocked'):'collected',observed_at:new Date(clock()).toISOString(),images,observations,errors};
}

async function readAsin(page,tld,asin,slots) {
 const navigation=await page.session.send('Page.navigate',{url:`https://www.amazon.${tld}/dp/${asin}?th=1&psc=1`});
 check(!navigation.errorText,`PDP navigation failed: ${navigation.errorText}`);
 const waitFor=async(predicate,timeout,stage)=>{
  const end=Date.now()+timeout;
  while(Date.now()<end){try{const result=await evaluate(page.session,`(${predicate})()`,5000);if(result)return result;}catch{}
   await new Promise(resolve=>setTimeout(resolve,250));}
  const state=await evaluate(page.session,`({url:location.href,readyState:document.readyState,titlePresent:Boolean(document.querySelector('#productTitle')),imageScripts:[...document.scripts].filter(s=>s.textContent.includes('colorImages')).length})`,5000).catch(()=>({unavailable:true}));
  throw new Error('PDP readiness timed out at '+stage+': '+JSON.stringify(state));
 };
 await waitFor(`()=>document.readyState!=='loading'&&location.pathname.includes('/dp/${asin}')`,15000,'navigation');
 const delivery=await ensureDeliveryPostcode(page.session,tld,{attempts:2});check(delivery.ok,'Delivery location unavailable');
 const verified=await assertDeliveryPostcode(page.session,tld);check(verified.ok,'Delivery location changed');
 const record=await waitFor(`()=>{const record=(${readImageRecord.toString()})();return record.title&&record.images.some(x=>x.variant?.startsWith('PT'))?record:null;}`,20000,'image payload');
 const finalDelivery=await assertDeliveryPostcode(page.session,tld);check(finalDelivery.ok,'Delivery location changed before observation');
 return {asin,images:selectExactSlots(record,asin,slots),source_id:record.source_id,observed_at:new Date().toISOString()};
}

export async function collect(input) {
 const tld={US:'com',DE:'de',AU:'com.au',UK:'co.uk',IT:'it',FR:'fr',ES:'es',CA:'ca'}[input.account.marketplace];check(tld,'Unsupported image marketplace');
 let page,outcome='error';
 try{
  page=await acquireTaskPage({taskId:taskIdFor('amazon-operations',input.operation_id),slot:'public-images',workflow:'amazon-listing-capture',initialUrl:'about:blank'});
  const result=await collectByAsin(input,(asin,slots)=>readAsin(page,tld,asin,slots));
  outcome=result.status==='collected'?'success':'error';return result;
 }catch(error){return {schema_version:1,account:input.account,operation_id:input.operation_id,plan_hash:input.plan_hash,status:'blocked',reason:'image_collection_unavailable',message:error.message,images:[]};}
 finally{if(page)await releaseTaskPage(page,{outcome});}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){try{check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');console.log(JSON.stringify(await collect(JSON.parse(await readFile(process.argv[3],'utf8')))));}catch(error){console.log(JSON.stringify({schema_version:1,status:'blocked',reason:'collector_preflight',message:error.message}));process.exitCode=2;}}
