import assert from 'node:assert/strict';
import test from 'node:test';
import {captureTaskEvidence,verifyEvidenceIdentity} from '../task-evidence.mjs';
const handle={port:9223,taskId:'capture:test',workflow:'amazon-seo',slot:'primary',targetId:'owned-target',
 session:{assertTaskControl:async()=>true,send:async()=>({data:Buffer.from('png').toString('base64')})}};
const expected={kind:'datadive',nicheId:'niche-a',heroKeyword:'iron supplement'};
test('capture records owned target and verified identity',async()=>{
 const r=await captureTaskEvidence(handle,{expected},{evaluate:async()=>({url:'https://2.datadive.tools/niche/niche-a/niche-analysis/mkl',text:'iron supplement',login:false})});
 assert.equal(r.evidence.target_id,'owned-target');assert.equal(r.evidence.session,'grimoire');
 assert.equal(r.evidence.verified_identity.nicheId,'niche-a');
});
test('wrong niche and missing login fail before capture',async()=>{
 await assert.rejects(verifyEvidenceIdentity(handle,expected,{evaluate:async()=>({url:'https://2.datadive.tools/niche/niche-b/niche-analysis/mkl',text:'iron supplement'})}),/IDENTITY_MISMATCH/);
 await assert.rejects(verifyEvidenceIdentity(handle,expected,{evaluate:async()=>({url:'https://2.datadive.tools/sign-in',login:true})}),/LOGIN_REQUIRED/);
});
test('account drift during capture discards image',async()=>{
 let calls=0;
 await assert.rejects(captureTaskEvidence(handle,{expected},{verify:async()=>({nicheId:++calls===1?'a':'b'})}),/IDENTITY_CHANGED/);
});

test('retail evidence verifies the exact product, market and delivery postcode',async()=>{
 let checked=false;
 const deps={evaluate:async()=>({url:'https://www.amazon.de/dp/B012345678',text:'Product'}),
  assertDeliveryPostcode:async(_session,market)=>{assert.equal(market,'de');checked=true;}};
 const proof=await verifyEvidenceIdentity(handle,{kind:'amazon-retail',marketplace:'DE',asin:'B012345678'},deps);
 assert.equal(proof.asin,'B012345678');assert.equal(checked,true);
 await assert.rejects(verifyEvidenceIdentity(handle,{kind:'amazon-retail',marketplace:'US',asin:'B012345678'},deps),/IDENTITY_MISMATCH/);
 await assert.rejects(verifyEvidenceIdentity(handle,{kind:'amazon-retail',marketplace:'DE',asin:'B098765432'},deps),/IDENTITY_MISMATCH/);
});

test('Seller Central proof rejects unrelated origins before reading account identity',async()=>{
 await assert.rejects(verifyEvidenceIdentity(handle,{kind:'seller-central',accountName:'Allfemme',marketplace:'US'},
  {evaluate:async()=>({url:'https://sellercentral.amazon.com.example.org/home',text:'Allfemme United States'}),
   readIdentity:async()=>{throw new Error('must not read identity');}}),/IDENTITY_REQUIRED/);
});

test('ambiguous visible screenshot selectors fail before capture',async()=>{
 let captured=false;
 const task={...handle,session:{...handle.session,send:async()=>{captured=true;}}};
 await assert.rejects(captureTaskEvidence(task,{expected,selector:'.grid'},
  {verify:async()=>({nicheId:'a'}),evaluate:async()=>{throw new Error('EVIDENCE_SELECTOR_AMBIGUOUS_OR_MISSING');}}),/SELECTOR_AMBIGUOUS/);
 assert.equal(captured,false);
});
