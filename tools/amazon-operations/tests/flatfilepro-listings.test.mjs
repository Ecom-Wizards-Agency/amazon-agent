import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {collect,normalizeListing,listingLocation} from '../flatfilepro-listings.mjs';
const account={seller_id:'SELLER',marketplace_id:'MARKET'},target={sku:'sku / 1',asin:'B000000001'},at='2026-09-14T10:00:00.000Z';
const data=()=>({seller_id:'SELLER',marketplace_id:'MARKET',...target,attributes:{main_product_image_locator:[{media_location:'https://example.com/main.png'}]},relationships:[],productType:'SUPPLEMENT',itemName:'Blue',lastUpdatedDate:'2026-09-10T00:00:00Z',id:123});
test('listing reader binds exact identity and distinguishes read time from Amazon update time',()=>{
 const result=normalizeListing(data(),account,target,at,listingLocation(account,target).url);
 assert.equal(result.row.listing_relationship_evidence,'standalone');assert.equal(result.row['swatch_product_image_locator.0.media_location'],'');
 assert.equal(result.row.product_type,'SUPPLEMENT');assert.equal(result.row.itemName,'Blue');assert.equal(result.observed_at,at);assert.equal(result.amazon_updated_at,'2026-09-10T00:00:00Z');
 for(const changed of [{seller_id:'OTHER'},{marketplace_id:'OTHER'},{sku:'wrong'},{asin:'B000000002'},{attributes:null}])assert.throws(()=>normalizeListing({...data(),...changed},account,target,at,'source'));
});
test('missing or nonempty relationship data never implies standalone',()=>{
 for(const relationships of [undefined,[{parentSkus:['PARENT']}],[{childSkus:['CHILD']}]])assert.equal(normalizeListing({...data(),relationships},account,target,at,'source').row.listing_relationship_evidence,undefined);
 const record=data();record.attributes.parentage_level=[{value:'parent'}];assert.equal(normalizeListing(record,account,target,at,'source').row.listing_relationship_evidence,undefined);
});
test('observed scalar related-ASIN arrays preserve variation evidence without becoming image values',()=>{
 const d=data();d.attributes.parentAsins=['B000000099'];const r=normalizeListing(d,account,target,at,'source');assert.deepEqual(r.related_asins,{parentAsins:['B000000099']});assert.equal(r.row.listing_relationship_evidence,undefined);
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
