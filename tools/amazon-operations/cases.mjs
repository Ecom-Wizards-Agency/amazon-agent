/** Seller Support cases: managed UI submission and independent GET readback.
 * Only fixed semantic controls may be clicked; no caller selectors/scripts.
 */
import { readFile, writeFile, open, unlink, realpath } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { homedir } from 'node:os';
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { evaluate } from '../report-fetcher/cdp.mjs';
import { switchAccount, readIdentity } from '../report-fetcher/sc-account.mjs';
import { acquireTaskPage, releaseTaskPage, taskIdFor } from '../browserctl/task-tabs.mjs';
import { acquireSessionLock } from '../browserctl/session-lock.mjs';
import * as ui from './browser-ui.mjs';

const HERE=dirname(fileURLToPath(import.meta.url));
export const caseBrowserAccount=account=>({...account,marketplace:account.marketplace==='AUS'?'AU':account.marketplace});
const caseOrigin=account=>ui.origins[caseBrowserAccount(account).marketplace];
const sha=value=>createHash('sha256').update(value).digest('hex');
const bodyText=value=>String(value||'').replace(/\r\n?/g,'\n').replace(/^\n+|\n+$/g,'');
const caseUrl=(origin,id)=>`${origin}/cu/case-dashboard/view-case?caseID=${encodeURIComponent(id)}`;
const clean=value=>String(value||'').replace(/\s+/g,' ').trim();
const fail=(code,message)=>{throw Object.assign(new Error(message),{code});};

export function capability(state,metadata={}) {
  if(/\/ap\/signin|\/signin|\/ap\/challenge/.test(state.url||''))return{state:'login_required'};
  if(/you (?:do not|don't) have (?:access|permission)|access denied|not authorized to (?:view|edit)|insufficient permissions/i.test(state.text||''))return{state:'permission_denied'};
  if(metadata.canEditCase===false&&!/^(?:closed|resolved)$/i.test(metadata.caseStatus||''))return{state:'permission_denied'};
  const reply=(state.controls||[]).filter(x=>x.label==='Reply');
  if(reply.length===1&&!reply[0].disabled)return{state:'reply_available'};
  if(/^(?:closed|resolved)$/i.test(metadata.caseStatus||''))return{state:'closed'};
  if(metadata.canEditCase===false)return{state:'permission_denied'};
  return{state:'unknown'};
}

export function decodeMessageEntities(value) {
  const named={amp:'&',quot:'\"',apos:"'",lt:'<',gt:'>',nbsp:'\u00a0'};
  return String(value||'').replace(/&(#x[0-9a-f]+|#[0-9]+|amp|quot|apos|lt|gt|nbsp);/gi,(whole,key)=>{
    if(key[0]!=='#')return named[key.toLowerCase()];
    const point=key[1].toLowerCase()==='x'?parseInt(key.slice(2),16):parseInt(key.slice(1),10);
    return point>0&&point<=0x10ffff&&!(point>=0xd800&&point<=0xdfff)?String.fromCodePoint(point):whole;
  });
}

export function normalizeCase(id,payload) {
  const m=payload?.viewCaseMetaData;
  ui.check(m&&Array.isArray(payload.contactList),'Case response metadata/correspondence missing');
  if(m.caseId!=null)ui.check(String(m.caseId)===id,'Readback returned another case');
  const total=Number(payload.totalNumberOfContacts??payload.totalContacts??payload.totalContactCount??m.totalContactCount??NaN);
  const continuation=payload.currentToken||payload.nextToken||payload.nextPageToken||payload.pagination?.nextToken||payload.hasMore===true;
  const complete=!continuation&&Number.isFinite(total)&&total===payload.contactList.length&&payload.contactList.every(c=>c.messageTruncated===false);
  const contacts=payload.contactList.map(c=>{
    const numeric=Number(c.timestamp), date=Number.isFinite(numeric)&&numeric>0?new Date(numeric<1e12?numeric*1000:numeric):new Date(c.timestamp);
    ui.check(c.contactId!=null&&Number.isFinite(date.getTime()),'Contact identity or timestamp missing');
    const attachments=c.attachments??c.attachmentList??[];
    ui.check(Array.isArray(attachments),'Unrecognized attachment metadata');
    return{id:String(c.contactId),is_amazon:typeof c.outbound==='boolean'?c.outbound:/^amazon$/i.test(c.sender||'')?true:/^(?:you|seller)$/i.test(c.sender||'')?false:null,
      timestamp:date.toISOString(),message:bodyText(c.messageDecoded?c.message:decodeMessageEntities(c.message)),sender:c.sender||'Unknown',
      attachments:attachments.map(a=>({name:a.fileName||a.name||a.attachmentName||'',url:a.url||a.downloadUrl||null,sha256:a.sha256||null}))};
  });
  return{case_id:id,subject:String(m.caseTitle||''),case_status:String(m.caseStatus||'Unknown'),can_edit:m.canEditCase===true,history_complete:complete,contacts,metadata:m};
}

export async function waitForCaseContext(sample,assertControl,account,homeIdentity,timeout=15000) {
  let last;
  try{return await ui.waitFor(async()=>{
    await assertControl();
    const state=await sample();last=state;
    if(capability(state).state==='login_required')fail('login_required','Grimoire requires login');
    state.identity=homeIdentity;
    return state;
  },state=>ui.contextMatches(state,caseBrowserAccount(account),'cases'),timeout);}
  catch(error){
    if(error.code==='login_required'||error.code?.startsWith('TASK_'))throw error;
    fail('case_context_unverified',`Case account/marketplace did not become verifiable at ${last?.url||'unknown page'}`);
  }
}

async function context(page,account,homeIdentity) {
  const assertControl=()=>page.session.assertTaskControl({exclusiveContext:true,sellerCentral:{marketplace:caseBrowserAccount(account).marketplace,origin:caseOrigin(account)}});
  // Case SPA navigation paints the surrounding menu before its account header.
  // Wait for the exact header under the retained claim; never read case data
  // using the menu alone or an account supplied only by the caller.
  return waitForCaseContext(()=>ui.snapshot(page.session),assertControl,account,homeIdentity);
}

async function fetchCase(page,account,id,homeIdentity) {
  const state=await context(page,account,homeIdentity);
  const response=await evaluate(page.session,String.raw`(async()=>{const r=await fetch('/hill/hillservice/mons-api/ViewCase?caseId='+encodeURIComponent(${JSON.stringify(id)})+'&pageSize=50',{credentials:'same-origin'});return{status:r.status,body:await r.text()};})()`,30000);
  if([401,403].includes(response.status))fail(response.status===401?'login_required':'permission_denied',`Case read HTTP ${response.status}`);
  ui.check(response.status===200,'Case read did not return HTTP 200');
  let payload;try{payload=JSON.parse(response.body);}catch{fail('case_response_unknown','Case endpoint returned non-JSON content');}
  // Convert Amazon HTML into message text in the document parser. Never execute
  // supplied HTML; DOMParser documents are detached from the browsing context.
  for(const c of payload.contactList||[]){c.message=await evaluate(page.session,String.raw`(()=>{const raw=${JSON.stringify(String(c.message||''))};if(!/<(?:br|p|div|html|body|span)\b/i.test(raw)){const e=document.createElement('textarea');e.innerHTML=raw.replace(/</g,'&lt;').replace(/>/g,'&gt;');return e.value;}const d=new DOMParser().parseFromString(raw,'text/html');for(const e of d.querySelectorAll('br'))e.replaceWith('\n');for(const e of d.querySelectorAll('p,div'))e.append('\n');return d.body.textContent;})()`);c.messageDecoded=true;}
  const result=normalizeCase(id,payload);
  for(const c of result.contacts)for(const a of c.attachments){
    if(a.url){const url=new URL(a.url,caseOrigin(account));if(url.origin!==caseOrigin(account))continue;
      const data=await evaluate(page.session,String.raw`(async()=>{const r=await fetch(${JSON.stringify(url.href)},{credentials:'same-origin'});if(!r.ok)return null;const b=new Uint8Array(await r.arrayBuffer());if(b.length>30000000)throw new Error('Attachment exceeds 30MB');const hash=await crypto.subtle.digest('SHA-256',b);return [...new Uint8Array(hash)].map(x=>x.toString(16).padStart(2,'0')).join('');})()`,60000);
      a.sha256=data;
    }
  }
  result.capability=capability(state,result.metadata);
  delete result.metadata;
  await context(page,account,homeIdentity);
  return result;
}

async function navigate(page,url) {
  await page.session.send('Page.navigate',{url});
  return ui.waitFor(()=>ui.snapshot(page.session),s=>s.url===url&&s.text.length>100||capability(s).state==='login_required');
}

export function caseListSummary(text,ids,hasNext=false) {
  const count=/Cases\s+([0-9,]+)\s+to\s+([0-9,]+)\s+of\s+([0-9,]+)/i.exec(text);
  const total=count?Number(count[3].replace(/,/g,'')):null;
  const unique=[...new Set(ids)];
  return{case_ids:unique,total_cases:total,complete:total!==null&&unique.length===total&&!hasNext};
}

export function duplicateQuery(subject,issueKey='') {
  const text=String(subject||'')+' '+String(issueKey||'');
  const identity=/\bFBA[A-Z0-9]{8,12}\b/i.exec(text)||/\bB0[A-Z0-9]{8}\b/i.exec(text);
  const query=identity?identity[0].toUpperCase():String(subject||'').trim();
  ui.check(query&&query.length<=512,'New case lookup requires its exact subject or issue identifier');
  return query;
}

export function mergeSearchPage(accumulator,payload,page) {
  ui.check(Array.isArray(payload?.caseSearchResultList)&&Number.isInteger(payload.totalNumberOfResults)&&payload.totalNumberOfResults>=0,'Case search response contract changed');
  if(page===0)accumulator.total=payload.totalNumberOfResults;
  ui.check(payload.totalNumberOfResults===accumulator.total,'Case search total changed during pagination');
  for(const row of payload.caseSearchResultList){
    const id=String(row.caseId||'');ui.check(/^\d{5,30}$/.test(id)&&!accumulator.rows.some(r=>r.caseId===id),'Case search returned a duplicate or invalid ID');
    accumulator.rows.push({...row,caseId:id});
  }
  ui.check(accumulator.rows.length<=accumulator.total,'Case search result count exceeds its total');
  ui.check(payload.caseSearchResultList.length>0||accumulator.rows.length===accumulator.total,'Case search ended before all matching cases were read');
  return accumulator.rows.length===accumulator.total;
}

async function listCases(page,account,homeIdentity,query) {
  ui.check(typeof query==='string'&&query.trim()&&query.length<=512,'Scoped case search query is required');
  await navigate(page,`${caseOrigin(account)}/cu/case-lobby`);
  const collected={total:null,rows:[]};
  // This read endpoint and exact request shape were observed from the case
  // lobby search UI. No case creation/update endpoint is called directly.
  for(let index=0;index<100;index++){
    await context(page,account,homeIdentity);
    const request={page:index,searchPageSize:10,sortBy:'CreationDate',sortByOrder:'DESC',getCountOnly:false,caseFilters:{caseOwner:'MerchantCases',searchText:query}};
    const response=await evaluate(page.session,String.raw`(async()=>{const r=await fetch('/hill/hillservice/mons-api/SearchForCases',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(${JSON.stringify(request)})});return{status:r.status,body:await r.text()};})()`,30000);
    if(response.status===403)fail('permission_denied','Case search access is denied');
    ui.check(response.status===200,'Case search did not return HTTP 200');
    const payload=JSON.parse(response.body);
    if(mergeSearchPage(collected,payload,index)){
      await context(page,account,homeIdentity);
      return{case_ids:collected.rows.map(r=>r.caseId),total_cases:collected.total,complete:true,duplicate_query:query,candidates:collected.rows.map(r=>({case_id:r.caseId,subject:r.shortDescription,status:r.status}))};
    }
  }
  fail('case_search_too_large','Scoped case search exceeds 1000 results; narrow the issue reference');
}

async function observeOnPage(input,page,homeIdentity) {
  const account=input.account,origin=caseOrigin(account);
  const common={schema_version:1,status:'collected',account,plan_hash:input.plan_hash,source_id:'amazon-case-correspondence',login_identity:{session:'grimoire',seller_id:homeIdentity.merchantId,marketplace_id:account.marketplace_id,login_name:null}};
  const id=input.case_id||input.targets?.[0]?.case_id;
  if(id){await navigate(page,caseUrl(origin,id));const data=await fetchCase(page,account,id,homeIdentity);return{...common,...data,observed_at:new Date().toISOString()};}
  const query=input.inputs?.duplicate_query||input.inputs?.baseline?.duplicate_query||duplicateQuery(input.inputs?.subject,input.targets?.[0]?.issue_key);
  const listed=await listCases(page,account,homeIdentity,query);
  const cases=[];
  // Creation readback follows only case IDs actually exposed in this account's
  // case log. It never assumes a new ID from a success banner or the issue key.
  for(const candidate of listed.case_ids){
    await navigate(page,caseUrl(origin,candidate));
    const item=await fetchCase(page,account,candidate,homeIdentity);
    cases.push(item);
  }
  return{...common,cases,case_ids:listed.case_ids,duplicate_query:query,candidates:listed.candidates,history_complete:listed.complete&&cases.every(x=>x.history_complete),capability:{state:'unknown'},observed_at:new Date().toISOString()};
}

export async function formSnapshot(session) {
  return evaluate(session,String.raw`(()=>{const inputs=[...document.querySelectorAll('input,textarea,[contenteditable="true"]')];const all=inputs.filter(e=>e.getBoundingClientRect().width>0);const label=e=>(e.getAttribute('aria-label')||e.labels?.[0]?.innerText||e.placeholder||'').replace(/\s+/g,' ').trim();return{fields:all.map(e=>({tag:e.tagName,type:e.type||'',name:e.name,id:e.id,label:label(e),value:e.value??e.innerText,required:e.required===true})),uploading:/uploading|upload failed|failed to upload/i.test(document.body.innerText)||!!document.querySelector('[role="progressbar"]'),visible_text:document.body.innerText,files:inputs.filter(e=>e.type==='file').flatMap(e=>[...e.files||[]].map(f=>({name:f.name,size:f.size})))};})()`);
}

const MESSAGE_LABELS=['Message','Your message','Describe your issue','Please describe your issue','Enter your message','Reply'];
const SUBJECT_LABELS=['Subject','Case subject'];
function fieldMatches(field,kind){return kind==='subject'?SUBJECT_LABELS.includes(field.label):field.tag==='TEXTAREA'||field.tag==='DIV'&&MESSAGE_LABELS.includes(field.label);}
export function verifyDraft(form,body,operation) {
  const messages=form.fields.filter(x=>fieldMatches(x,'message'));
  ui.check(messages.length===1&&bodyText(messages[0].value)===body.signed_body,'Exact signed case message differs from the form');
  if(operation==='case.create'){
    const subjects=form.fields.filter(x=>fieldMatches(x,'subject'));
    ui.check(subjects.length===1&&subjects[0].value===body.subject,'Exact case subject differs from the form');
  }
  ui.check(form.uploading!==true,'Case attachment upload is pending or failed');
  ui.check(body.attachments.every(a=>String(form.visible_text||'').includes(a.name)),'Attachment confirmation is not visible');
  ui.check(form.files.length===body.attachments.length&&body.attachments.every(a=>form.files.some(f=>f.name===a.name&&f.size===a.size)),'Attachment names, sizes or count differ from the plan');
  ui.check(!form.fields.some(f=>f.required&&!f.value&&f.type!=='file'),'Unfilled required case field');
}

async function fillField(session,kind,value) {
  const form=await formSnapshot(session),matches=form.fields.filter(x=>fieldMatches(x,kind));
  ui.check(matches.length===1,`Expected exactly one ${kind} field`);
  const field=matches[0];
  await evaluate(session,String.raw`(()=>{const els=[...document.querySelectorAll('input,textarea,[contenteditable="true"]')].filter(e=>e.getBoundingClientRect().width>0&&e.tagName===${JSON.stringify(field.tag)}&&e.id===${JSON.stringify(field.id)}&&e.name===${JSON.stringify(field.name)});if(els.length!==1)throw new Error('Case field became ambiguous');els[0].focus();if(els[0].select)els[0].select();else{const r=document.createRange();r.selectNodeContents(els[0]);const s=getSelection();s.removeAllRanges();s.addRange(r);}})()`);
  await session.send('Input.insertText',{text:value});
}

async function attachAll(session,files){
  if(!files.length)return;
  await session.send('DOM.enable',{});
  const {nodes}=await session.send('DOM.getFlattenedDocument',{depth:-1,pierce:true});
  const inputs=nodes.filter(n=>n.nodeName==='INPUT'&&(n.attributes||[]).some((v,i,a)=>i%2===0&&v==='type'&&a[i+1]==='file'));
  ui.check(inputs.length===1,'Expected exactly one case attachment input');
  await session.send('DOM.setFileInputFiles',{files:files.map(x=>x.path),nodeId:inputs[0].nodeId});
}

async function validateBinding(input){
  const path=join(dirname(input.receipt_path),'case-binding-input.json');
  await writeFile(path,JSON.stringify({binding:input.plan.body.case_binding,inputs:input.plan.body,account:input.plan.account,operation:input.plan.operation,targets:input.plan.targets,operation_id:input.plan.operation_id,request_hash:input.plan.request_hash}));
  const answer=spawnSync('python3',[join(HERE,'case_service.py'),'validate-binding','--request',path],{encoding:'utf8',timeout:30000});
  ui.check(answer.status===0,'Case owner or authorization changed before submission');
}

export async function submitPrepared(input,page,homeIdentity,dependencies={}) {
  const api={context,navigate,fetchCase,listCases,formSnapshot,fillField,attachAll,validateBinding,click:ui.click,receipt:ui.receipt,...dependencies};
  const plan=input.plan,body=plan.body,account=plan.account,origin=caseOrigin(account);
  let attempted=false;
  const result=x=>({schema_version:1,plan_hash:input.plan_hash,attempted,...x});
  try{
    if(plan.operation==='case.reply'){
      const id=plan.targets[0].case_id;
      await api.navigate(page,caseUrl(origin,id));
      const current=await api.fetchCase(page,account,id,homeIdentity);
      if(current.capability.state!=='reply_available')fail(current.capability.state,'Case reply capability is unavailable');
      ui.check(current.history_complete,'Case history is incomplete');
      const expected=new Set(body.baseline.contact_ids||[]);
      ui.check(current.contacts.every(x=>expected.has(x.id))&&expected.size===current.contacts.length,'Case correspondence changed since the message was prepared');
      await api.click(page.session,'Reply');
    }else{
      const query=body.duplicate_query||body.baseline.duplicate_query||duplicateQuery(body.subject,body.issue_key);
      const listed=await api.listCases(page,account,homeIdentity,query);
      ui.check(listed.complete&&listed.duplicate_query===query,'Case log is incomplete or its query differs; duplicate check unavailable');
      ui.check(!listed.candidates.some(c=>clean(c.subject)===clean(body.subject)&&!/^(?:Closed|Resolved)$/i.test(c.status)),'An active case already has this exact subject; continue that case');
      ui.check(listed.case_ids.every(id=>(body.baseline.case_ids||[]).includes(id)),'New case appeared since preparation; refresh duplicate check');
      const state=await api.context(page,account,homeIdentity);
      const create=state.controls.filter(x=>['Create case','Create a case','Get support'].includes(x.label)&&!x.disabled);
      ui.check(create.length===1,'No unique create-case control is exposed');
      await api.click(page.session,create[0].label);
      // Support routing changes frequently. Only an already exposed, uniquely
      // labeled case form is supported; unresolved topic choices stop here.
    }
    await api.fillField(page.session,'message',body.signed_body);
    if(plan.operation==='case.create')await api.fillField(page.session,'subject',body.subject);
    await api.attachAll(page.session,body.attachments);
    const form=await api.formSnapshot(page.session);verifyDraft(form,body,plan.operation);
    const state=await api.context(page,account,homeIdentity);
    const send=state.controls.filter(x=>['Send','Submit','Send message','Submit case'].includes(x.label)&&!x.disabled);
    ui.check(send.length===1,'No unique case submission control is exposed');
    await api.validateBinding(input);
    for(const a of body.attachments)ui.check(sha(await readFile(a.path))===a.sha256,'Attachment changed before submission');
    verifyDraft(await api.formSnapshot(page.session),body,plan.operation);
    await api.context(page,account,homeIdentity);
    await api.receipt(input.receipt_path,result({status:'uncertain',reason:'before_submit',attempted:true,submitted_body_sha256:body.message_sha256,baseline:body.baseline,owner:body.owner,case_binding:body.case_binding,submitted_at:new Date().toISOString()}));
    attempted=true;
    await api.click(page.session,send[0].label);
    const answer=result({status:'processing',submission_id:plan.targets[0].case_id||null,reason:'awaiting_independent_case_readback'});
    await api.receipt(input.receipt_path,answer);return answer;
  }catch(error){const answer=result({status:attempted?'uncertain':'blocked',reason:attempted?'case_submission_uncertain':error.code||'case_ui_contract_unavailable',message:error.message});await api.receipt(input.receipt_path,answer);return answer;}
}

export async function claimAdapter(path,planHash) {
  let handle;try{handle=await open(path,'wx',0o600);}catch(error){if(error.code==='EEXIST')fail('case_adapter_already_claimed','This adapter attempt already exists; reconcile its correspondence instead of replaying');throw error;}
  try{await handle.writeFile(JSON.stringify({plan_hash:planHash,claimed_at:new Date().toISOString()}));await handle.sync();}finally{await handle.close();}
}

export async function run(input){
  ui.check(input.schema_version===1&&['observe','execute'].includes(input.mode),'Case mode must be observe or execute');
  if(input.mode==='execute'){
    await ui.verifyEnvelope(input);
    ui.check(/^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$/.test(input.plan.operation_id),'Invalid case operation ID');
    const canonical=resolve(await realpath(resolve(homedir(),'.amazon-agent/cases/operations')),input.plan.operation_id);
    ui.check(await realpath(dirname(input.plan_path))===canonical,'Case adapter requires the canonical shared delivery journal');
    const journal=JSON.parse(await readFile(join(canonical,'journal.json'),'utf8'));
    ui.check(journal.operation_id===input.plan.operation_id&&journal.plan_hash===input.plan_hash&&journal.status==='uncertain'&&journal.effects_started===true,'Case adapter requires a durable uncompleted execution claim');
  }
  const plan=input.plan,account=plan?.account||input.account,operation=plan?.operation||input.operation;
  ui.check(['case.create','case.reply'].includes(operation),'Unsupported case operation');
  ui.check(Number(process.env.CDP_PORT||9223)===9223&&(!process.env.AMAZON_BROWSER_SESSION||process.env.AMAZON_BROWSER_SESSION==='grimoire'),'Cases require the Grimoire session on 9223');
  const origin=caseOrigin(account);ui.check(origin,'Unsupported marketplace');
  const unlock=acquireSessionLock(9223,'amazon-cases');let page,outcome='error',executionEntered=false,claimPath=null;
  const onSigterm=async()=>{
    if(page?._released)return;
    try{if(page)await releaseTaskPage(page,{outcome:'error'});}
    catch(error){console.error('SIGTERM browser release failed:',error.message);}
    finally{process.exit(143);}
  };
  process.once('SIGTERM',onSigterm);
  try{
    page=await acquireTaskPage({taskId:taskIdFor('amazon-operations',plan?.operation_id||input.operation_id),workflow:'amazon-communications',initialUrl:origin+'/home',exclusiveContext:true,sellerCentral:{marketplace:caseBrowserAccount(account).marketplace,origin}});
    await switchAccount(page.session,origin,{accountName:account.seller_central_name||account.seller_account,marketplaceLabel:account.marketplace_label,marketplace:caseBrowserAccount(account).marketplace,parentAccountName:account.parent_account_name},{returnTo:'/home'});
    const homeIdentity=await readIdentity(page.session);
    await context(page,account,homeIdentity);
    if(input.mode==='execute'){claimPath=join(dirname(input.plan_path),'case-adapter-claim.json');await claimAdapter(claimPath,input.plan_hash);}
    executionEntered=input.mode==='execute';
    const answer=input.mode==='observe'?await observeOnPage(input,page,homeIdentity):await submitPrepared(input,page,homeIdentity);
    if(answer.status==='collected'||answer.status==='processing')outcome='success';
    if(claimPath&&answer.attempted===false){await unlink(claimPath);claimPath=null;}
    return answer;
  }catch(error){return{schema_version:1,plan_hash:input.plan_hash,account,status:executionEntered||error.code==='case_adapter_already_claimed'?'uncertain':'blocked',attempted:executionEntered||error.code==='case_adapter_already_claimed',reason:error.code||'case_access_unknown',message:error.message,capability:{state:error.code==='login_required'?'login_required':error.code==='permission_denied'?'permission_denied':'unknown'}};}
  finally{process.removeListener('SIGTERM',onSigterm);try{if(page)await releaseTaskPage(page,{outcome});}catch{}finally{unlock();}}
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
 let input;try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');input=JSON.parse(await readFile(process.argv[3],'utf8'));console.log(JSON.stringify(await run(input)));}catch(error){console.log(JSON.stringify({schema_version:1,plan_hash:input?.plan_hash,status:'blocked',attempted:false,reason:'case_adapter_preflight',message:error.message}));process.exitCode=2;}
}
