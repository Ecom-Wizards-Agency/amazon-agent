import { mkdtemp, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import assert from 'node:assert/strict';
import { capability, normalizeCase, verifyDraft, submitPrepared, decodeMessageEntities, caseListSummary, duplicateQuery, mergeSearchPage, caseBrowserAccount, claimAdapter, waitForCaseContext } from '../cases.mjs';

const account={marketplace:'US'};
const body={signed_body:'Please confirm the fee.\n\nBest,\nDanica',subject:'Shipment defect',attachments:[],baseline:{contact_ids:['old'],case_ids:['12345678']},owner:{member_id:'D',signature_name:'Danica',revision:1},case_binding:{owner_revision:1}};
const form={fields:[{tag:'TEXTAREA',label:'Message',value:body.signed_body,required:true}],files:[]};

// Redacted shape observed 2026-09-09: Amazon sends outbound=true; seller email
// may itself begin with "amazon", so sender-name heuristics are unsafe.
const realShape={appointmentMetadata:null,currentToken:null,liveConversation:null,totalNumberOfContacts:4,
 viewCaseMetaData:{canEditCase:false,caseStatus:'PendingAmazonAction',caseSupportType:'Expert',caseTags:null,caseTitle:'Redacted defect',ccList:[],creationDate:1788541015.867,crmType:'CASE',escalateMotivationId:null,escalated:false,primaryEmail:'amazon@example.invalid',transfer:false},
 contactList:[false,true,true,false].map((outbound,i)=>({attachments:null,channelType:'EMAIL',contactId:`ekko:us-east-1:redacted-${i}`,expired:false,hmdContact:false,hmdMetaData:null,message:`Message ${i}\nExact next line`,messageList:null,messageTruncated:false,outbound,parentContact:null,sender:outbound?'Amazon':'amazon@example.invalid',timestamp:1788962046.794-i*3600}))};

test('observed schema preserves seller direction and complete contact count',()=>{
 const normalized=normalizeCase('12345678',realShape);
 assert.equal(normalized.history_complete,true);
 assert.deepEqual(normalized.contacts.map(x=>x.is_amazon),[false,true,true,false]);
 assert.equal(normalized.contacts[0].message,'Message 0\nExact next line');
 assert.equal(normalized.contacts[0].timestamp,'2026-09-09T13:54:06.794Z');
 assert.deepEqual(normalized.contacts[0].attachments,[]);
});
test('truncated, paged, or missing total history is never complete',()=>{
 for(const changed of [{totalNumberOfContacts:5},{currentToken:'next'},{totalNumberOfContacts:undefined},{contactList:realShape.contactList.map((x,i)=>({...x,messageTruncated:i===0}))}])assert.equal(normalizeCase('12345678',{...realShape,...changed}).history_complete,false);
});
test('capability distinguishes denied, closed, login, missing control and reply',()=>{
 const base={url:'https://sellercentral.amazon.com/cu/case-dashboard/view-case',text:'Case',controls:[]};
 assert.equal(capability(base,{canEditCase:false,caseStatus:'PendingAmazonAction'}).state,'permission_denied');
 assert.equal(capability(base,{caseStatus:'Closed'}).state,'closed');
 assert.equal(capability(base,{canEditCase:true}).state,'unknown');
 assert.equal(capability({...base,url:'https://sellercentral.amazon.com/ap/signin'}).state,'login_required');
 assert.equal(capability({...base,controls:[{label:'Reply',disabled:false}]}).state,'reply_available');
});
test('draft verification rejects wrong signature, attachment and ambiguous textarea',()=>{
 verifyDraft(form,body,'case.reply');
 assert.throws(()=>verifyDraft({...form,fields:[{...form.fields[0],value:body.signed_body.replace('Danica','Victor')}]},body,'case.reply'),/signed/);
 assert.throws(()=>verifyDraft({...form,files:[{name:'unknown.txt',size:2}]},body,'case.reply'),/Attachment/);
 assert.throws(()=>verifyDraft({...form,fields:[...form.fields,...form.fields]},body,'case.reply'),/signed/);
});
function fixture(overrides={}){
 const events=[];
 const input={plan_hash:'a'.repeat(64),receipt_path:'/not-written-test-receipt',plan:{operation:'case.reply',account,targets:[{case_id:'12345678'}],body}};
 const deps={navigate:async()=>{},fetchCase:async()=>({capability:{state:'reply_available'},history_complete:true,contacts:[{id:'old'}]}),
 context:async()=>({controls:[{label:'Send',disabled:false}]}),fillField:async()=>events.push('fill'),attachAll:async()=>{},formSnapshot:async()=>form,
 validateBinding:async()=>events.push('owner-validated'),click:async(_s,label)=>events.push(label),receipt:async(_p,data)=>events.push(`receipt:${data.status}:${data.attempted}`),...overrides};
 return{input,deps,events};
}
test('send writes uncertain receipt after owner validation and before final click',async()=>{
 const {input,deps,events}=fixture();const result=await submitPrepared(input,{session:{}},{},deps);
 assert.equal(result.status,'processing');assert.equal(result.attempted,true);
 assert.ok(events.indexOf('owner-validated')<events.indexOf('receipt:uncertain:true'));
 assert.ok(events.indexOf('receipt:uncertain:true')<events.indexOf('Send'));
});
test('timeout after final click remains uncertain and never clicks a second time',async()=>{
 let sends=0;const {input,deps}=fixture({click:async(_s,label)=>{if(label==='Send'){sends++;throw new Error('lost transport');}}});
 const result=await submitPrepared(input,{session:{}},{},deps);
 assert.equal(result.status,'uncertain');assert.equal(result.attempted,true);assert.equal(sends,1);
});
test('missing permissions and changed correspondence stop before filling or send',async()=>{
 for(const state of [{capability:{state:'permission_denied'},history_complete:true,contacts:[]},{capability:{state:'reply_available'},history_complete:true,contacts:[{id:'new'}]}]){
  const {input,deps,events}=fixture({fetchCase:async()=>state});const result=await submitPrepared(input,{session:{}},{},deps);
  assert.equal(result.status,'blocked');assert.equal(result.attempted,false);assert.ok(!events.includes('fill'));assert.ok(!events.includes('Send'));
 }
});
test('owner changed during form preparation stops before submission',async()=>{
 const {input,deps,events}=fixture({validateBinding:async()=>{throw new Error('owner changed');}});
 const result=await submitPrepared(input,{session:{}},{},deps);
 assert.equal(result.attempted,false);assert.equal(result.status,'blocked');assert.ok(!events.includes('Send'));
});

test('message entities decode once while literal angle words survive',()=>{
 assert.equal(decodeMessageEntities('&#34;fee&#34; &#39;reply&#39; &amp; <literal>'), '"fee" \'reply\' & <literal>');
 assert.equal(decodeMessageEntities('&amp;quot;'), '&quot;');
 assert.equal(decodeMessageEntities('&#x1F642;'), '\u{1F642}');
});
test('first page of 556 cases cannot become a complete duplicate baseline',()=>{
 const ids=Array.from({length:10},(_,i)=>String(12345678+i));
 assert.equal(caseListSummary('Cases 1 to 10 of 556',ids).complete,false);
 assert.equal(caseListSummary('Cases 1 to 10 of 10',ids).complete,true);
 assert.equal(caseListSummary('Case log without known total',ids).complete,false);
});

test('scoped duplicate query and paging bind the full filtered result',()=>{
 assert.equal(duplicateQuery('Missing units FBA19BHQR9VJ'),'FBA19BHQR9VJ');
 assert.equal(duplicateQuery('Listing B012345678 issue'),'B012345678');
 assert.equal(duplicateQuery('Exact unrelated issue'),'Exact unrelated issue');
 const state={rows:[],total:null};
 assert.equal(mergeSearchPage(state,{caseSearchResultList:[{caseId:'12345678'}],totalNumberOfResults:2},0),false);
 assert.equal(mergeSearchPage(state,{caseSearchResultList:[{caseId:'87654321'}],totalNumberOfResults:2},1),true);
 assert.throws(()=>mergeSearchPage(state,{caseSearchResultList:[],totalNumberOfResults:3},2),/changed/);
 const duplicate={rows:[{caseId:'12345678'}],total:2};
 assert.throws(()=>mergeSearchPage(duplicate,{caseSearchResultList:[{caseId:'12345678'}],totalNumberOfResults:2},1),/duplicate/);
 assert.equal(mergeSearchPage({rows:[],total:null},{caseSearchResultList:[],totalNumberOfResults:0},0),true);
});
test('AUS alias only changes the browser marketplace',()=>{
 const original={marketplace:'AUS',profile_key:'brand-aus',seller_id:'seller'};
 assert.deepEqual(caseBrowserAccount(original),{...original,marketplace:'AU'});
 assert.equal(original.marketplace,'AUS');
});
test('direct adapter replay cannot acquire a second submission claim',async()=>{
 const directory=await mkdtemp(join(tmpdir(),'case-claim-'));
 try{const path=join(directory,'claim.json');await claimAdapter(path,'a'.repeat(64));await assert.rejects(()=>claimAdapter(path,'a'.repeat(64)),/reconcile/);}finally{await rm(directory,{recursive:true});}
});

test('case SPA waits for exact header and rechecks its claim each sample',async()=>{
 const account={marketplace:'US',seller_central_name:'Example',marketplace_label:'United States',seller_id:'SELLER',marketplace_id:'MARKET'};
 let samples=0,claims=0;
 const result=await waitForCaseContext(async()=>({url:'https://sellercentral.amazon.com/cu/case-lobby',contexts:++samples===1?[]:['Example United States']}),async()=>{claims++;},account,{merchantId:'SELLER',marketplace:'MARKET'},1000);
 assert.equal(samples,2);assert.equal(claims,2);assert.deepEqual(result.contexts,['Example United States']);
});
test('header wait never accepts another account or a lost browser claim',async()=>{
 const account={marketplace:'US',seller_central_name:'Example',marketplace_label:'United States',seller_id:'SELLER',marketplace_id:'MARKET'};
 await assert.rejects(()=>waitForCaseContext(async()=>({url:'https://sellercentral.amazon.com/cu/case-lobby',contexts:['Other United States']}),async()=>{},account,{merchantId:'SELLER',marketplace:'MARKET'},1),/did not become verifiable/);
 let sampled=false;
 await assert.rejects(()=>waitForCaseContext(async()=>{sampled=true;return{};},async()=>{throw Object.assign(new Error('claim lost'),{code:'TASK_TAB_CONTROL_LOST'});},account,{},1),/claim lost/);
 assert.equal(sampled,false);
});
