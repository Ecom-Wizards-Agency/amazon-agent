import test from 'node:test';
import assert from 'node:assert/strict';
import { verifyPreview } from '../flatfilepro.mjs';
import { verifyCatalogPreview } from '../catalog.mjs';
import { contextMatches } from '../browser-ui.mjs';

test('FFP verifies each SKU-field full-grid cell, not a filename',()=>{
 const body={expected_rows:{a:{'item_name.0.value':'New A'},b:{'item_name.0.value':'Keep B'}}};
 const state={text:'Preview',rows:[['sku','Title (item_name.0.value)'],['a','New A'],['b','Keep B']]};
 assert.equal(verifyPreview(state,body),true);
 assert.throws(()=>verifyPreview({...state,rows:[state.rows[0],state.rows[1],['b','New A']]},body),/mismatch/);
 assert.throws(()=>verifyPreview({...state,rows:[...state.rows,state.rows[1]]},body),/count/);
 assert.throws(()=>verifyPreview({...state,rows:[...state.rows,['unrequested','Other']]},body),/unrequested/);
});
test('technical header mismatch and validation errors stop FFP',()=>{
 const body={expected_rows:{a:{'title_differentiation.0.value':'Highlight'}}};
 assert.throws(()=>verifyPreview({text:'Preview',rows:[['sku','bullet_point.0.value'],['a','Highlight']]},body),/mismatch/);
 assert.throws(()=>verifyPreview({text:'Validation error',rows:[['sku','title_differentiation.0.value'],['a','Highlight']]},body),/validation/);
});
test('account context cannot be established from product body text',()=>{
 const acct={marketplace:'US',seller_central_name:'Example Seller',marketplace_label:'United States',seller_id:'SELLER',marketplace_id:'MARKET',context_binding:{seller_id:'SELLER',marketplace_id:'MARKET',unique_label_mapping:true}};
 assert.equal(contextMatches({url:'https://sellercentral.amazon.com/home',contexts:[],text:'Example Seller United States'},acct,'catalog'),false);
 assert.equal(contextMatches({url:'https://sellercentral.amazon.com/home',contexts:['Example Seller United States']},acct,'catalog'),true);
 assert.equal(contextMatches({url:'https://sellercentral.amazon.com/home',contexts:['Example Seller Plus United States']},acct,'catalog'),false);
 assert.equal(contextMatches({url:'https://sellercentral.amazon.com/home',contexts:['Example Seller United States'],identity:{merchantId:'OTHER'}},acct,'catalog'),false);
 assert.equal(contextMatches({url:'https://sellercentral.amazon.de/home',contexts:['Example Seller United States']},acct,'catalog'),false);
});
test('catalog requires zero errors and exact preview SKU coverage',()=>{
 const state={text:'Preview file and fix errors Ready to submit 2 Action required 0',rows:[['a','Parent'],['b','Child']],aiEnabled:false};
 verifyCatalogPreview(state,{skus:['a','b']});
 assert.throws(()=>verifyCatalogPreview({...state,text:state.text.replace('required 0','required 1')},{skus:['a','b']}),/counts/);
 assert.throws(()=>verifyCatalogPreview(state,{skus:['a','other']}),/SKU/);
 assert.throws(()=>verifyCatalogPreview({...state,aiEnabled:true},{skus:['a','b']}),/AI-generated/);
});

test('account verification requires nonempty stable IDs or a complete bound label mapping',()=>{
 const base={marketplace:'US',seller_central_name:'Example Seller',flatfilepro_display_name:'Example Seller',marketplace_label:'United States',seller_id:'SELLER',marketplace_id:'MARKET'};
 const binding={seller_id:'SELLER',marketplace_id:'MARKET',unique_label_mapping:true};
 for(const site of ['catalog','ffp']) {
  const state={url:site==='ffp'?'https://app.flatfile.pro':'https://sellercentral.amazon.com/home',contexts:['Example Seller United States']};
  for(const missing of [undefined,null,'','   ']) {
   for(const key of ['seller_id','marketplace_id']) {
    const account={...base,[key]:missing};
    assert.equal(contextMatches(state,account,site),false);
    assert.equal(contextMatches(state,{...account,context_binding:{...binding,[key]:missing}},site),false);
   }
  }
  assert.equal(contextMatches(state,{...base,seller_id:undefined,marketplace_id:undefined},site),false);
  assert.equal(contextMatches(state,base,site),false);
  for(const incomplete of [{unique_label_mapping:true},{...binding,seller_id:undefined},{...binding,marketplace_id:''},{...binding,marketplace_id:'   '}])
   assert.equal(contextMatches(state,{...base,context_binding:incomplete},site),false);
  assert.equal(contextMatches(state,{...base,context_binding:binding},site),true);
  assert.equal(contextMatches({...state,identity:{merchantId:'SELLER',marketplace:'MARKET'}},base,site),true);
  assert.equal(contextMatches({...state,identity:{merchantId:'SELLER',marketplace:{marketplaceId:'MARKET'}}},base,site),true);
  for(const identity of [{merchantId:'SELLER'},{marketplace:'MARKET'},{merchantId:'',marketplace:'MARKET'},{merchantId:'SELLER',marketplace:' '}])
   assert.equal(contextMatches({...state,identity},base,site),false);
  for(const identity of [{merchantId:'OTHER'},{marketplace:'OTHER'},{merchantId:''},{marketplace:' '},{marketplace:{marketplaceId:'OTHER'}}])
   assert.equal(contextMatches({...state,identity},{...base,context_binding:binding},site),false);
 }
});

test('fresh report collector rejects stale, wrong-type and unfinished reports',async()=>{
 const {matchingCompletedReports}=await import('../catalog-export.mjs');
 const marker={requested_at:'2026-09-06T10:00:00Z',report_value:'category',report_label:'Category Listings Report'};
 const done={reportType:{translationStringId:'category'},processingState:{name:'DONE'},submissionDate:'2026-09-06T10:01:00Z'};
 assert.equal(matchingCompletedReports([done],marker,marker.requested_at).length,1);
 assert.equal(matchingCompletedReports([{...done,submissionDate:'2026-09-06T09:59:00Z'}],marker,marker.requested_at).length,0);
 assert.equal(matchingCompletedReports([{...done,reportType:{translationStringId:'inventory'}}],marker,marker.requested_at).length,0);
});
test('image collector uses variant identity and rejects redirected products',async()=>{
 const {selectExactSlots}=await import('../image-evidence.mjs');
 const record={resolved_asin:'B000000001',title:'Example',images:[{variant:'MAIN',url:'https://example.com/a.jpg'},{variant:'PT02',url:'https://example.com/b.jpg'}]};
 assert.deepEqual(selectExactSlots(record,'B000000001',['PT01','PT02']),[{slot:'PT02',live_url:'https://example.com/b.jpg'}]);
 assert.throws(()=>selectExactSlots(record,'B000000002',['MAIN']),/another product/);
});
