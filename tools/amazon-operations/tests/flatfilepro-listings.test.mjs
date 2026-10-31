import '../../report-fetcher/test/helpers/isolated-runtime.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {IMAGE_IDENTITY_KEYS,listingIdentity,verifyListingIdentities} from '../image-identity.mjs';
import {collect,normalizeListing,listingLocation,flattenAttributes} from '../flatfilepro-listings.mjs';
const account={seller_id:'SELLER',marketplace_id:'MARKET'},target={sku:'sku / 1',asin:'B000000001'},at='2026-09-14T10:00:00.000Z';
const data=()=>({seller_id:'SELLER',marketplace_id:'MARKET',...target,attributes:{main_product_image_locator:[{media_location:'https://example.com/main.png'}]},relationships:[],productType:'SUPPLEMENT',itemName:'Blue',lastUpdatedDate:'2026-09-10T00:00:00Z',id:123});
test('listing reader binds exact identity and distinguishes read time from Amazon update time',()=>{
 const result=normalizeListing(data(),account,target,at,listingLocation(account,target).url);
 assert.equal(result.row.listing_relationship_evidence,'standalone');assert.equal(result.row['swatch_product_image_locator.0.media_location'],'');
 assert.equal(result.row.product_type,'SUPPLEMENT');assert.equal(result.row.itemName,'Blue');assert.equal(result.observed_at,at);assert.equal(result.amazon_updated_at,'2026-09-10T00:00:00Z');
 for(const changed of [{seller_id:'OTHER'},{marketplace_id:'OTHER'},{sku:'wrong'},{asin:'B000000002'},{attributes:null}])assert.throws(()=>normalizeListing({...data(),...changed},account,target,at,'source'));
});
test('missing or nonempty relationship data never implies standalone',()=>{
 for(const relationships of [undefined,[{parentSkus:['PARENT']}],[{childSkus:['CHILD']}]])assert.equal(normalizeListing({...data(),relationships},account,target,at,'source').row.listing_relationship_evidence,'');
 const record=data();record.attributes.parentage_level=[{value:'parent'}];assert.equal(normalizeListing(record,account,target,at,'source').row.listing_relationship_evidence,'');
});
test('observed scalar related-ASIN arrays preserve variation evidence without becoming image values',()=>{
 const d=data();d.attributes.parentAsins=['B000000099'];const r=normalizeListing(d,account,target,at,'source');assert.deepEqual(r.related_asins,{parentAsins:['B000000099']});assert.equal(r.row.listing_relationship_evidence,'');
 d.attributes.parentAsins=['not-an-asin'];assert.throws(()=>normalizeListing(d,account,target,at,'source'),/related listing/);
 d.attributes.parentAsins=['B000000099','B000000099'];assert.throws(()=>normalizeListing(d,account,target,at,'source'),/related listing/);
});
test('catalog aliases come only from unambiguous exact attributes and preserve relationships',()=>{
 const d=data();d.attributes.part_number=[{value:'MPN-1',marketplace_id:'MARKET'}];d.attributes.color=[{value:'Blue'}];d.attributes.size=[{value:'92'}];d.attributes.parentage_level=[{value:'child'}];d.relationships=[{parentSkus:['PARENT']}];d.parent_sku='PARENT';
 const r=normalizeListing(d,account,target,at,'source');assert.equal(r.row.mpn,'MPN-1');assert.equal(r.row.color,'Blue');assert.equal(r.row.size,'92');assert.equal(r.row.parentage,'child');assert.deepEqual(r.relationships,d.relationships);assert.equal(r.parent_sku,'PARENT');assert.equal(r.ffp_synced_at,null);
 d.attributes.color.push({value:'Red'});assert.equal(normalizeListing(d,account,target,at,'source').row.color,'');
 d.attributes.part_number[0].marketplace_id='OTHER';assert.throws(()=>normalizeListing(d,account,target,at,'source'),/marketplace/);
});
test('same ASIN on distinct seller SKUs retains independent identity and baseline',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'ffp-listings-'));
 try{const targets=[target,{...target,sku:'second'}],input={schema_version:1,operation_id:'siblings',account,plan_hash:'b'.repeat(64),targets,output_dir:dir,minimum_after:at};
 const result=await collect(input,{acquire:async()=>({session:{}}),release:async()=>{},read:async(s,a,t)=>normalizeListing({...data(),...t},a,t,at,'source'),now:()=>Date.parse(at)});
 assert.equal(result.status,'collected');assert.equal(result.records.length,2);assert.deepEqual(Object.keys(result.rows),targets.map(x=>x.sku));
 }finally{await rm(dir,{recursive:true,force:true});}
});
test('collector records complete exact-SKU evidence with independent checksum',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'ffp-listings-'));
 try{
 const input={schema_version:1,operation_id:'trial',account,plan_hash:'a'.repeat(64),targets:[target],output_dir:dir,minimum_after:at};
 const deps={acquire:async()=>({session:{}}),release:async()=>{},read:async()=>normalizeListing(data(),account,target,at,'source'),now:()=>Date.parse(at)};
 const result=await collect(input,deps);assert.equal(result.status,'collected');assert.equal(result.complete,true);assert.deepEqual(JSON.parse(await readFile(result.path)).rows,result.rows);
 assert.equal((await collect({...input,targets:[target,target]},deps)).status,'blocked');
 assert.equal((await collect(input,{...deps,read:async()=>({...await deps.read(),observed_at:'2026-09-13T10:00:00Z'})})).status,'blocked');
 }finally{await rm(dir,{recursive:true,force:true});}
});

test('complete listing responses emit every canonical identity key with explicit blanks',()=>{
 const record=data();record.attributes.color=[{value:'Blue'}];record.attributes.model_number=[{value:'M1'}];
 const row=normalizeListing(record,account,target,at,'source').row;
 for(const key of IMAGE_IDENTITY_KEYS)assert.ok(Object.hasOwn(row,key),key);
 assert.equal(row['color.0.value'],'Blue');assert.equal(row['model_number.0.value'],'M1');
 assert.equal(row['size.0.value'],'');assert.equal(row.model_name,'');
 assert.equal(row['other_product_image_locator_9.0.media_location'],'');
});

// Golden rows were produced by normalizeListing before the nested option existed (commit 493061b).
const fixtures=join(import.meta.dirname,'fixtures','ffp-mcp');
const golden=JSON.parse(await readFile(join(fixtures,'normalize-default-golden.json'),'utf8'));
const exportRecords=(await readFile(join(fixtures,'export-records.jsonl'),'utf8')).trim().split('\n').map(line=>JSON.parse(line));
const mcpAccount={seller_id:'A1TESTSELLER01',marketplace_id:'ATVPDKIKX0DER'},goldenAt='2026-10-28T09:00:00.000Z';
const asData=r=>({seller_id:r.sellerId,marketplace_id:r.marketplaceId,sku:r.sku,asin:r.asin,attributes:r.attributes,productType:r.productType,versionId:r.versionId,archived:r.archived});
test('default normalizeListing output is byte-identical to the pre-change golden rows',()=>{
 for(const r of exportRecords){
  const target={sku:r.sku,asin:r.asin};
  assert.equal(JSON.stringify(normalizeListing(asData(r),mcpAccount,target,goldenAt,'golden')),JSON.stringify(golden.outputs[r.sku]),r.sku);
  assert.equal(JSON.stringify(normalizeListing(asData(r),mcpAccount,target,goldenAt,'golden',{})),JSON.stringify(golden.outputs[r.sku]),r.sku);
 }
 const cdp=golden.cdp_input;
 assert.equal(JSON.stringify(normalizeListing(cdp,{seller_id:'SELLER',marketplace_id:'MARKET'},{sku:cdp.sku,asin:cdp.asin},goldenAt,'golden')),JSON.stringify(golden.outputs['cdp-item-detail']));
 assert.ok(!Object.keys(golden.outputs['TEST-CHILD-BLUE'].row).includes('unit_count.0.type_value'));
});
test('nested option adds canonical nested keys and leaves every default key unchanged',()=>{
 const r=exportRecords.find(x=>x.sku==='TEST-CHILD-BLUE'),target={sku:r.sku,asin:r.asin};
 const plain=normalizeListing(asData(r),mcpAccount,target,goldenAt,'golden').row,nested=normalizeListing(asData(r),mcpAccount,target,goldenAt,'golden',{nested:true}).row;
 for(const [key,value] of Object.entries(plain))assert.equal(nested[key],value,key);
 const added=Object.keys(nested).filter(key=>!Object.hasOwn(plain,key));
 assert.deepEqual(added.sort(),['color.0.standardized_values.0.','item_dimensions.0.height_unit','item_dimensions.0.height_value','item_dimensions.0.length_unit','item_dimensions.0.width_unit','item_dimensions.0.width_value','item_weight.0.normalized_value_unit','item_weight.0.normalized_value_value','outer.0.material.0.value','outer.0.material.1.value','purchasable_offer.0.end_at_value','purchasable_offer.0.our_price.0.schedule.0.value_with_tax','unit_count.0.type_language_tag','unit_count.0.type_value']);
 // Every flattened attribute appears in the nested row with the same value.
 for(const [key,value] of Object.entries(flattenAttributes(r.attributes)))assert.equal(nested[key],value,key);
 assert.equal(nested.itemName,'');
});
test('nested flattened keys never enter listing identity',()=>{
 const r=exportRecords.find(x=>x.sku==='TEST-CHILD-BLUE'),target={sku:r.sku,asin:r.asin};
 const plain=normalizeListing(asData(r),mcpAccount,target,goldenAt,'golden').row,nested=normalizeListing(asData(r),mcpAccount,target,goldenAt,'golden',{nested:true}).row;
 assert.deepEqual(listingIdentity(nested),listingIdentity(plain));
 const extra={...plain,'color.0.standardized_values.0.':'Blau','item_name.0.value.0.':'x','part_number.0.nested.0.value':'y'};
 assert.deepEqual(listingIdentity(extra),listingIdentity(plain));
 assert.ok(Object.hasOwn(listingIdentity(plain),'color.0.value')&&Object.hasOwn(listingIdentity(plain),'color.0.language_tag'));
 // A plan captured without nested keys still verifies against a nested fresh read, and vice versa.
 assert.doesNotThrow(()=>verifyListingIdentities({[r.sku]:listingIdentity(plain)},{[r.sku]:nested},[r.sku]));
 assert.doesNotThrow(()=>verifyListingIdentities({[r.sku]:listingIdentity(nested)},{[r.sku]:plain},[r.sku]));
});
