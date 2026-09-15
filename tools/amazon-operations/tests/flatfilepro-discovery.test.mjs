import test from 'node:test';
import assert from 'node:assert/strict';
import {validateCatalogPages,enrichCatalog,catalogRequest,normalizeCatalogPage,collect} from '../flatfilepro-discovery.mjs';
import {mkdtemp,rm,readFile} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
const account={seller_id:'SELLER',marketplace_id:'MARKET'},at='2026-09-15T10:00:00Z';
const item=(sku,asin='B000000001')=>({...account,sku,asin});
const page=(offset,items,total,has_more)=>({...account,offset,items,total,has_more,observed_at:at});
const url=(kind='items',p=0)=>{const query=new URLSearchParams({filter:JSON.stringify({brands:['brand'],archived:'NOT ARCHIVED',variation:'ALL LISTINGS',marketplaceId:'MARKET',sellerId:'SELLER'}),marketplaceId:'MARKET',sellerId:'SELLER',page:String(p),pageSize:'2','sortModel[]':JSON.stringify({field:'sku',sort:'asc'}),insertOnboardingStep:'false'});return `https://api.flatfile.pro/amazon-listings/${kind}?${query}`;};
test('observed item and count requests bind exact account, filters and page coverage',()=>{
 const items={url:url(),data:{rows:[item('one'),item('two')]},observed_at:at},count={url:url('total-count'),data:{count:3},observed_at:at};
 assert.equal(catalogRequest(url(),account).page,0);assert.equal(normalizeCatalogPage(items,count,account).has_more,true);
 assert.throws(()=>normalizeCatalogPage({...items,data:{rows:[item('one')]}},count,account),/truncated/);
 for(const value of [url().replace('sellerId=SELLER','sellerId=OTHER'),url()+'&page=0',url().replace('/items?','/fetch?'),url()+'&search=blue',url().replace('insertOnboardingStep=false','insertOnboardingStep=true')])assert.throws(()=>catalogRequest(value,account));
 const narrowed=new URL(url());const filter=JSON.parse(narrowed.searchParams.get('filter'));filter.search='blue';narrowed.searchParams.set('filter',JSON.stringify(filter));assert.throws(()=>catalogRequest(narrowed.href,account),/narrowing/);
 const scopedCount=new URL(count.url);scopedCount.searchParams.set('pageSize','40');assert.throws(()=>normalizeCatalogPage(items,{...count,url:scopedCount.href},account),/scope/);
});
test('complete catalog pages retain distinct SKUs sharing an ASIN',()=>{
 const result=validateCatalogPages([page(0,[item('one')],2,true),page(1,[item('two')],2,false)],account);
 assert.equal(result.total,2);assert.equal(result.pages,2);assert.deepEqual(result.targets.map(x=>x.sku),['one','two']);
});
test('observed next-page requests bind account through the filter without repeated top-level IDs',()=>{
 const next=new URL(url('items',1));next.searchParams.delete('sellerId');next.searchParams.delete('marketplaceId');
 assert.equal(catalogRequest(next.href,account).scope,catalogRequest(url(),account).scope);
 const normalized=normalizeCatalogPage({url:next.href,data:{rows:[item('three')]},observed_at:at},{url:url('total-count'),data:{count:3},observed_at:at},account);
 assert.equal(normalized.offset,2);assert.equal(normalized.has_more,false);
 const wrong=new URL(next);const filter=JSON.parse(wrong.searchParams.get('filter'));filter.sellerId='OTHER';wrong.searchParams.set('filter',JSON.stringify(filter));
 assert.throws(()=>catalogRequest(wrong.href,account),/account/);
 const partial=new URL(next);partial.searchParams.set('sellerId','SELLER');assert.throws(()=>catalogRequest(partial.href,account),/account/);
});
test('catalog rejects missing, repeated, incomplete or changing pages',()=>{
 const start=page(0,[item('one')],2,true),end=page(1,[item('two')],2,false);
 for(const pages of [[],[start],[start,{...end,offset:0}],[start,{...end,total:3}],[start,{...end,items:[]}],[start,{...end,has_more:true}],[{...start,has_more:false},end],[start,{...end,items:[item('one')]}]])assert.throws(()=>validateCatalogPages(pages,account));
});
test('catalog verifies account and exact row identities on every page',()=>{
 const valid=page(0,[item('one')],1,false);
 for(const patch of [{seller_id:'OTHER'},{marketplace_id:'OTHER'},{observed_at:null},{items:[item('')]},{items:[item('one','')]},{items:[{...item('one'),seller_id:'OTHER'}]},{items:[{...item('one'),marketplace_id:'OTHER'}]}])assert.throws(()=>validateCatalogPages([{...valid,...patch}],account));
 assert.equal(validateCatalogPages([page(0,[],0,false)],account).total,0);
});
test('enrichment starts after complete enumeration and checks exact item identity and timestamps',async()=>{
 const pages=[page(0,[item('one'),item('two')],2,false)],reads=[];
 const options={minimum:Date.parse(at),now:()=>Date.parse(at),read:async(s,a,t)=>{reads.push(t.sku);return {...t,row:{sku:t.sku,asin:t.asin},observed_at:at,amazon_updated_at:'2026-01-01T00:00:00Z',ffp_synced_at:null};}};
 const result=await enrichCatalog({},pages,account,options);assert.equal(result.coverage.exact_reads,2);assert.deepEqual(reads,['one','two']);assert.equal(result.records[0].amazon_updated_at,'2026-01-01T00:00:00Z');
 reads.length=0;await assert.rejects(()=>enrichCatalog({},[{...pages[0],total:3,has_more:true}],account,options));assert.deepEqual(reads,[]);
 for(const patch of [{seller_id:'OTHER'},{marketplace_id:'OTHER'},{asin:'B000000002'},{row:{sku:'other',asin:'B000000001'}},{observed_at:'2026-01-01T00:00:00Z'},{observed_at:'2027-01-01T00:00:00Z'}])await assert.rejects(()=>enrichCatalog({},pages,account,{...options,read:async(s,a,t)=>({...await options.read(s,a,t),...patch})}));
});
test('collector persists full detail coverage and distinguishes inventory-only results',async()=>{
 const dir=await mkdtemp(join(tmpdir(),'ffp-discovery-'));
 try{
 const input={schema_version:1,operation_id:'discovery',account,plan_hash:'c'.repeat(64),output_dir:dir,minimum_after:at};
 let count=0;const deps={now:()=>Date.parse(at),acquire:async()=>({session:{}}),release:async()=>{},pages:async()=>[page(0,[item('one')],1,false)],read:async(s,a,t)=>{count++;return {...t,row:{sku:t.sku,asin:t.asin},observed_at:at};}};
 const full=await collect({...input,targets:[{sku:'one',asin:'B000000001'}]},deps);assert.equal(full.status,'collected');assert.equal(full.complete,true);assert.equal(full.inventory_complete,true);assert.equal(full.detail_coverage,'complete');assert.equal(count,1);assert.equal(JSON.parse(await readFile(full.path)).records.length,1);
 const inventory=await collect({...input,inventory_only:true},deps);assert.equal(inventory.status,'collected');assert.equal(inventory.complete,false);assert.equal(inventory.inventory_complete,true);assert.equal(inventory.detail_coverage,'none');assert.equal(count,1);assert.deepEqual(inventory.rows,{});
 const bad=await collect(input,{...deps,pages:async()=>[page(0,[{...item('one'),seller_id:'OTHER'}],1,false)]});assert.equal(bad.status,'blocked');assert.equal(count,1);
 const selected=await collect({...input,targets:[{sku:'one',asin:'B000000001'}]},{...deps,pages:async()=>[page(0,[item('one'),item('two')],2,false)]});assert.equal(selected.status,'collected');assert.equal(selected.complete,false);assert.equal(selected.inventory_complete,true);assert.equal(selected.detail_coverage,'selected');assert.equal(count,2);
 const defaultInventory=await collect(input,deps);assert.equal(defaultInventory.inventory_complete,true);assert.equal(defaultInventory.detail_coverage,'none');assert.equal(count,2);
 assert.equal((await collect({...input,targets:[{sku:'absent',asin:'B000000001'}]},deps)).status,'blocked');assert.equal(count,2);
 }finally{await rm(dir,{recursive:true,force:true});}
});
