import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {run} from '../flatfilepro.mjs';
import {IMAGE_IDENTITY_KEYS,verifyListingIdentities} from '../image-identity.mjs';
test('final browser pre-submit check rejects changed, added and missing identity fields',()=>{
 const identity={...Object.fromEntries(IMAGE_IDENTITY_KEYS.map(key=>[key,''])),sku:'S',asin:'B012345678','model_number.0.value':'11010040','color.0.value':'Navy','size.0.value':'86'};
 for(const key of ['model_number.0.value','color.0.value','size.0.value']){
  assert.throws(()=>verifyListingIdentities({S:identity},{S:{...identity,[key]:'Changed'}},['S']),/identity changed/);
 }
 const missing={...identity};delete missing['size.0.value'];
 assert.throws(()=>verifyListingIdentities({S:identity},{S:missing},['S']),/identity changed/);
 assert.throws(()=>verifyListingIdentities({S:identity},{},['S']),/identity changed/);
 assert.doesNotThrow(()=>verifyListingIdentities({S:identity},{S:{...identity,'other_product_image_locator_1.0.media_location':'new',price:'10',observed_at:'now'}},['S']));
});

const identity={...Object.fromEntries(IMAGE_IDENTITY_KEYS.map(key=>[key,''])),sku:'S',asin:'B012345678','model_number.0.value':'11010040','color.0.value':'Navy','size.0.value':'86','part_number.0.value':''};
for(const [name,expected] of [
 ['missing map',undefined],['empty map',{}],['missing SKU',{T:{...identity,sku:'T'}}],
 ['empty identity',{S:{}}],['partial fields',{S:{sku:'S',asin:identity.asin}}],
 ['missing blank field',{S:Object.fromEntries(Object.entries(identity).filter(([field])=>field!=='part_number.0.value'))}],
])test('pre-submit identity blocks '+name,()=>{
 assert.throws(()=>verifyListingIdentities(expected,{S:identity},['S']),error=>{
  assert.equal(error.code,'IDENTITY_MAP_INCOMPLETE');
  assert.match(error.message,/SKUs: S/);
  assert.match(error.message,/re-prepare the plan/);
  if(expected===undefined)assert.match(error.message,/Plan predates identity capture/);
  return true;
 });
});
test('target coverage cannot be inferred from an incomplete fresh read',()=>{
 assert.throws(()=>verifyListingIdentities({S:identity},{S:identity},['S','T']),/IDENTITY_MAP_INCOMPLETE:.*SKUs: T/);
});
test('complete identity map passes for every target including blank attributes',()=>{
 const rows={S:identity,T:{...identity,sku:'T'}};
 assert.doesNotThrow(()=>verifyListingIdentities(rows,rows,['S','T']));
});
test('two-argument verification also blocks missing expectations',()=>{
 assert.throws(()=>verifyListingIdentities(undefined,{S:identity}),{code:'IDENTITY_MAP_INCOMPLETE'});
});
for(const missingKey of [null,'color.0.value'])test('adapter blocks legacy identity before acquiring a tab: '+missingKey,async()=>{
 const directory=await mkdtemp(join(tmpdir(),'image-identity-'));
 try{
  const plan={operation_id:'identity-test',account:{marketplace:'US'},targets:['S'],artifacts:[],
   body:{adapter:'flatfilepro.cdp',image_policy:'secondary_slots_only',image_catalog_source:'flatfilepro_listing_read'}};
  if(missingKey){plan.body.image_identity_rows={S:{...identity}};delete plan.body.image_identity_rows.S[missingKey];}
  const planPath=join(directory,'plan.json'),receiptPath=join(directory,'receipt.json');
  await writeFile(planPath,JSON.stringify(plan));
  const result=await run({schema_version:1,plan,plan_hash:'a'.repeat(64),plan_path:planPath,receipt_path:receiptPath,mode:'execute'});
  assert.equal(result.status,'blocked');
  assert.equal(result.attempted,false);
  assert.equal(result.phase,'account_selection');
  assert.match(result.message,/IDENTITY_MAP_INCOMPLETE:.*SKUs: S.*re-prepare the plan/);
  if(missingKey)assert.match(result.message,/missing fields: color\.0\.value/);
  else assert.match(result.message,/Plan predates identity capture/);
  assert.deepEqual(JSON.parse(await readFile(receiptPath,'utf8')),result);
 }finally{await rm(directory,{recursive:true,force:true});}
});

test('canonical identity keys match the Python source byte for byte',async()=>{
 const python=await readFile(new URL('../operations.py',import.meta.url),'utf8');
 const javascript=await readFile(new URL('../image-identity.mjs',import.meta.url),'utf8');
 const literal=python.match(/IMAGE_IDENTITY_KEYS = (\[[\s\S]*?\n\])/)[1];
 assert.equal(literal,javascript.match(/IMAGE_IDENTITY_KEYS=Object.freeze\((\[[\s\S]*?\n\])\)/)[1]);
 assert.deepEqual([...literal.matchAll(/'([^']+)'/g)].map(match=>match[1]),IMAGE_IDENTITY_KEYS);
});
test('simultaneous canonical omission from map and fresh row blocks',()=>{
 const incomplete={...identity};delete incomplete['color.0.value'];
 assert.throws(()=>verifyListingIdentities({S:incomplete},{S:incomplete},['S']),error=>{
  assert.equal(error.code,'IDENTITY_MAP_INCOMPLETE');
  assert.match(error.message,/S \(missing fields: color\.0\.value\).*re-prepare the plan/);return true;
 });
});
test('additional captured attribute paths must remain present and unchanged',()=>{
 const expected={S:{...identity,'color.1.value':'Red'}};
 assert.doesNotThrow(()=>verifyListingIdentities(expected,expected,['S']));
 for(const row of [identity,{...expected.S,'color.1.value':'Blue'}])
  assert.throws(()=>verifyListingIdentities(expected,{S:row},['S']),/identity changed/);
 assert.throws(()=>verifyListingIdentities({S:identity},expected,['S']),{code:'IDENTITY_MAP_INCOMPLETE'});
 const missingBlank={...identity};delete missingBlank['part_number.0.value'];
 assert.throws(()=>verifyListingIdentities({S:identity},{S:missingBlank},['S']),/identity changed/);
});
