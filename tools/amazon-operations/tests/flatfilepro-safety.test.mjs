import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, writeFile, rm } from 'node:fs/promises';
import { join } from 'node:path';
import { tmpdir } from 'node:os';
import { createHash } from 'node:crypto';
import { collectPreview, destinationSearchField, durableReceipt, exactDestination, importIdentity, readAttempt, recoveryStatus, reserveSubmission, sameUploadedFile, uploadedFileIdentity, verifyImagePreflight, verifySelectedDestination } from '../flatfilepro-contracts.mjs';
import { run, verifyPreview, reconcileImport } from '../flatfilepro.mjs';

const field='other_product_image_locator_1.0.media_location';
const page=(number,rows,next)=>({text:`Preview Page ${number} of 2`, rows:[['sku',field],...rows],controls:[{label:'Next page',disabled:!next}]});

test('captured run receipt recovers after a lost adapter response without any browser write',async()=>{
  const input={plan:{account:{seller_id:'S',marketplace_id:'M'}},plan_hash:'a'};
  const attempt={identity_kind:'uploaded_file',submission_intent:true,submission_id:'run-1',
    submission_url:'https://app.flatfile.pro/activity/import/run-1',submission_response_at:new Date().toISOString()};
  const result=await reconcileImport(input,attempt);
  assert.equal(result.status,'collected');assert.equal(result.submission_id,'run-1');
  assert.equal(result.processing_status,'processing');
  assert.equal((await reconcileImport(input,{identity_kind:'uploaded_file',submission_intent:true})).status,'blocked');
  await assert.rejects(reconcileImport(input,{...attempt,submission_url:'https://other.example/run-1'}),/receipt/);
});

test('v2 secondary search requires exact input, one candidate and selected technical readback',()=>{
  const raw='other_product_image_locator_1__1__media_location';
  const label='Locator für andere Produktbilder > Andere Bild-URL';
  const candidate={label};
  assert.equal(destinationSearchField(field),raw);
  assert.equal(destinationSearchField(raw),raw);
  assert.equal(exactDestination([candidate],raw,raw),candidate);
  assert.equal(verifySelectedDestination(`${label} (${raw})`,raw),true);
  for(const options of [[],[candidate,candidate]])assert.throws(()=>exactDestination(options,raw,raw),/unverifiable/);
  assert.throws(()=>exactDestination([candidate],raw,field),/unverifiable/);
  for(const selected of [label,`${label} (other_product_image_locator_2__1__media_location)`,`${label} (${raw}) suffix`])
    assert.throws(()=>verifySelectedDestination(selected,raw),/unverifiable/);
});

test('secondary normalization never expands to unsupported slots or other image families',()=>{
  for(const name of ['other_product_image_locator_9.0.media_location','other_product_image_locator_1.1.media_location','main_product_image_locator.0.media_location','swatch_product_image_locator.0.media_location','other_offer_image_locator_1.0.media_location']){
    assert.equal(destinationSearchField(name),name);
    assert.throws(()=>exactDestination([{label:'Other image'}],name,name),/unverifiable/);
  }
});

test('observed server workbook key binds seller, marketplace, filename and SKU identifier',()=>{
  const account={seller_id:'SELLER',marketplace_id:'MARKET'};
  const label='SELLER-MARKET/1077-ffp-a.xlsx (SKU)';
  const value=uploadedFileIdentity('https://app.flatfile.pro/import',[label],account,'ffp-a.xlsx');
  assert.equal(value.upload_key,'SELLER-MARKET/1077-ffp-a.xlsx');
  assert.equal(value.identity_kind,'uploaded_file');
  assert.equal(value.import_id,undefined);
  for(const labels of [[label,label],[label.replace('(SKU)','(ASIN)')],[label.replace('SELLER','OTHER')],[label.replace('1077-','')],[label.replace('ffp-a','ffp-b')]])
    assert.throws(()=>uploadedFileIdentity('https://app.flatfile.pro/import',labels,account,'ffp-a.xlsx'));
  assert.throws(()=>sameUploadedFile(value,{...value,upload_key:'SELLER-MARKET/1078-ffp-a.xlsx'}),/changed/);
});

test('localized duplicate image labels and no technical search result cannot identify a slot',()=>{
  assert.throws(()=>exactDestination(Array.from({length:5},()=>({label:'Andere Produktabbildung'})),field),/ffp_image_slot_unverifiable/);
  assert.throws(()=>exactDestination([],field),/ffp_image_slot_unverifiable/);
  assert.throws(()=>exactDestination([{label:field},{label:`Bild (${field})`}],field),/ffp_image_slot_unverifiable/);
  assert.equal(exactDestination([{label:`Bild (${field})`}],field).label,`Bild (${field})`);
  assert.throws(()=>exactDestination([{label:'Andere Produktabbildung',id:field,index:0}],field),/ffp_image_slot_unverifiable/);
});

test('preview aggregates every page and validates full SKU and field coverage',async()=>{
  const pages=[page(1,[['a','one']],true),page(2,[['b','two']],false)];let index=0;
  const result=await collectPreview(async()=>pages[index],async()=>index++);
  assert.equal(result.page_count,2);
  verifyPreview(result,{expected_rows:{a:{[field]:'one'},b:{[field]:'two'}}});
  assert.throws(()=>verifyPreview(result,{expected_rows:{a:{[field]:'one'}}}),/unrequested/);
});

test('preview stops on repeated pages, missing next control and skipped pages',async()=>{
  await assert.rejects(collectPreview(async()=>page(1,[['a','one']],true),async()=>{}),/repeated/);
  await assert.rejects(collectPreview(async()=>page(1,[['a','one']],false),async()=>{}),/more pages/);
  await assert.rejects(collectPreview(async()=>page(2,[['a','one']],false),async()=>{}),/skipped/);
  await assert.rejects(collectPreview(async()=>({text:'Preview',rows:[['sku',field],['a','one']],controls:[]}),async()=>{}),/completeness/);
});

test('hidden extra field or duplicate SKU across pages prevents submission',async()=>{
  const pages=[page(1,[['a','one']],true),page(2,[['a','two']],false)];let index=0;
  const result=await collectPreview(async()=>pages[index],async()=>index++);
  assert.throws(()=>verifyPreview(result,{expected_rows:{a:{[field]:'one'}}}),/count/);
  assert.throws(()=>verifyPreview({text:'Preview',rows:[['sku',field,'main_product_image_locator.0.media_location'],['a','one','unapproved']]},{expected_rows:{a:{[field]:'one'}}}),/attribute mismatch/);
});

test('import identity is exact, public and unambiguous',()=>{
  assert.equal(importIdentity('https://app.flatfile.pro/imports/abc').import_id,'abc');
  assert.throws(()=>importIdentity('https://app.flatfile.pro/imports/abc?importId=other'),/ambiguous/);
  assert.throws(()=>importIdentity('https://evil.example/imports/abc'),/FlatFilePro/);
  assert.throws(()=>importIdentity('https://app.flatfile.pro/dashboard'),/missing/);
});

test('durable submit intent survives receipt loss and binds upload bytes',async()=>{
  const directory=await mkdtemp(join(tmpdir(),'ffp-safety-'));
  try {
    const upload=join(directory,'upload.xlsx'),path=join(directory,'attempt.json');
    await writeFile(upload,'exact-workbook');
    const account={seller_id:'SELLER',marketplace_id:'MARKET'};
    const plan={operation_id:'test',account,body:{upload,adapter:'flatfilepro.cdp'},artifacts:[]};
    const input={schema_version:1,plan_hash:'a'.repeat(64),plan,plan_path:join(directory,'plan.json'),receipt_path:join(directory,'adapter-receipt.json'),mode:'execute'};
    await writeFile(input.plan_path,JSON.stringify(plan));
    const record={plan_hash:input.plan_hash,account,import_id:'abc',import_url:'https://app.flatfile.pro/imports/abc',submission_intent:true,upload_sha256:createHash('sha256').update('exact-workbook').digest('hex')};
    await durableReceipt(path,record);
    assert.equal((await readAttempt(path,input)).submission_intent,true);
    await durableReceipt(join(directory,'flatfilepro-attempt.json'),record);
    assert.equal((await run(input)).reason,'prior_submit_requires_reconciliation');
    await assert.rejects(readAttempt(path,{...input,plan_hash:'b'.repeat(64)}),/bound account or plan/);
    await writeFile(upload,'different-workbook');
    await assert.rejects(readAttempt(path,input),/upload hash mismatch/);
  } finally {await rm(directory,{recursive:true,force:true});}
});

test('pre-click image preflight rejects old, future or changed reports',async()=>{
  const directory=await mkdtemp(join(tmpdir(),'ffp-preflight-'));
  try {
    const path=join(directory,'report.csv');await writeFile(path,'fresh');
    const at=Date.now(),receipt={path,sha256:createHash('sha256').update('fresh').digest('hex'),report_generated_at:new Date(at).toISOString()};
    const input={plan:{body:{image_policy:'secondary_slots_only'}},image_preflight:receipt};
    await verifyImagePreflight(input,at);
    await assert.rejects(verifyImagePreflight(input,at+300001),/expired/);
    await assert.rejects(verifyImagePreflight(input,at-1),/expired/);
    await writeFile(path,'changed');
    await assert.rejects(verifyImagePreflight(input,at),/changed/);
  } finally {await rm(directory,{recursive:true,force:true});}
});

test('concurrent direct adapters cannot reserve the same submission twice',async()=>{
  const directory=await mkdtemp(join(tmpdir(),'ffp-claim-'));
  try {
    const path=join(directory,'attempt.json');
    const outcomes=await Promise.allSettled([reserveSubmission(path,{id:'a'}),reserveSubmission(path,{id:'b'})]);
    assert.equal(outcomes.filter(x=>x.status==='fulfilled').length,1);
    assert.equal(outcomes.find(x=>x.status==='rejected').reason.code,'EEXIST');
    await assert.rejects(reserveSubmission(path,{id:'retry'}),{code:'EEXIST'});
  }finally{await rm(directory,{recursive:true,force:true});}
});

test('recovery requires one exact status and never treats import acceptance as image verification',()=>{
  assert.equal(recoveryStatus(['Processing']),'processing');
  assert.equal(recoveryStatus(['Completed']),'complete');
  assert.throws(()=>recoveryStatus(['Processing','Completed']),/contradictory/);
  assert.throws(()=>recoveryStatus([]),/unavailable/);
  assert.throws(()=>recoveryStatus(['Product completed previously']),/unavailable/);
});
