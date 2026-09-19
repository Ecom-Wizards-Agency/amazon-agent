import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {authorizedBinding,selectCandidate,verifyBinding,discoverBinding,collect} from '../flatfilepro-account.mjs';
const account={seller_id:'SELLER',marketplace_id:'US'},url='https://app.flatfile.pro/amazon-listings-items?sellerId=SELLER&marketplaceId=US';
test('authorized marketplace IDs resolve renamed sellers and reject duplicates',()=>{
 const row={selling_partner_id:'SELLER',marketplace_id:'US',seller_name:'New Name',marketplace_name:'United States'};
 assert.deepEqual(authorizedBinding({sp_api_authorized_marketplaces:[row]},account),{seller_name:'New Name',marketplace_name:'United States'});
 assert.throws(()=>authorizedBinding({sp_api_authorized_marketplaces:[row,row]},account));
 assert.throws(()=>authorizedBinding({sp_api_authorized_marketplaces:[{...row,marketplace_id:'DE'}]},account));
});
test('same seller name in different countries selects exact grouped option',()=>{
 const options=[{index:0,label:'Seller',country:'Germany'},{index:1,label:'Seller',country:'United States'}];
 assert.equal(selectCandidate(options,{seller_name:'Seller',marketplace_name:'United States'}).index,1);
 assert.throws(()=>selectCandidate([...options,options[1]],{seller_name:'Seller',marketplace_name:'United States'}));
});
test('selector labels alone never establish account binding',()=>{
 const observed={url,display:'Seller (United States)',option:'Seller'};
 assert.equal(verifyBinding(observed,account).seller_id,'SELLER');
 for(const bad of [url.replace('SELLER','OTHER'),url.replace('=US','=DE'),url+'&sellerId=SELLER',url+'&marketplaceId=US','https://app.flatfile.pro/exports'])assert.throws(()=>verifyBinding({...observed,url:bad},account));
});

// Exercise the exported browser flow through CDP, including network event
// ordering. No browser, authentication transport, or external request is used.
function discoverySession({type='Fetch',status=200,rows,observedUrl=url,options,base64=false}={}){
 const authorized=rows||[{selling_partner_id:'SELLER',marketplace_id:'US',seller_name:'Seller',marketplace_name:'United States'}];
 const list=options||[{index:0,label:'Seller',country:'Germany'},{index:1,label:'Seller',country:'United States'}];
 const evaluations=[true,undefined,list,undefined,'Seller (United States)',undefined,{url:observedUrl,display:'Seller (United States)'}];
 const callbacks=new Map(),calls=[],expressions=[],unsubscribed=[];
 let asserts=0;
 return {
  calls,expressions,unsubscribed,get asserts(){return asserts;},
  assertTaskControl:async value=>{assert.deepEqual(value,{exclusiveContext:true});asserts++;},
  subscribe(event,callback){callbacks.set(event,callback);return()=>{callbacks.delete(event);unsubscribed.push(event);};},
  async send(method,params){
   calls.push({method,params});
   if(method==='Page.navigate'){
    assert.equal(params.url,'https://app.flatfile.pro/exports');
    const endpoint='https://api.flatfile.pro/brands/get-authorized-marketplaces';
    // A late OPTIONS completion must not replace the captured data response.
    for(const [requestId,resourceType,httpStatus,responseUrl] of [
     ['actual',type,status,endpoint],['preflight','Preflight',204,endpoint],
     ['unrelated','Fetch',401,'https://api.flatfile.pro/other-endpoint'],
     ['foreign','Fetch',200,'https://unrelated.test/brands/get-authorized-marketplaces']]){
     callbacks.get('Network.responseReceived')({requestId,type:resourceType,response:{url:responseUrl,status:httpStatus}});
     callbacks.get('Network.loadingFinished')({requestId});
    }
   }
   if(method==='Network.getResponseBody'){
    assert.equal(params.requestId,'actual','Only the actual Fetch/XHR body may be read');
    const body=JSON.stringify({sp_api_authorized_marketplaces:authorized});
    return {body:base64?Buffer.from(body).toString('base64'):body,base64Encoded:base64};
   }
   if(method==='Runtime.evaluate'){
    expressions.push(params.expression);
    assert.ok(evaluations.length,'Unexpected additional DOM interaction');
    return {result:{value:evaluations.shift()}};
   }
   return {};
  }
 };
}

test('discovery ignores late OPTIONS 204 and unrelated responses for Fetch and XHR',async()=>{
 for(const type of ['Fetch','XHR']){
  const session=discoverySession({type,base64:type==='XHR'});
  const result=await discoverBinding(session,account);
  assert.equal(result.seller_id,'SELLER');assert.equal(result.marketplace_id,'US');
  assert.equal(result.flatfilepro_option_name,'Seller');assert.equal(result.source_url,url);
  assert.equal(session.calls.filter(x=>x.method==='Network.getResponseBody').length,1);
  assert.equal(session.expressions.length,7);
  assert.match(session.expressions[3],/e=a\[1\]/,'Select the requested marketplace country, not the first same-name seller');
  assert.deepEqual(session.unsubscribed,['Network.responseReceived','Network.loadingFinished']);
  assert.equal(session.asserts,4);
 }
});

test('discovery rejects duplicate account IDs before clicking any selector',async()=>{
 const row={selling_partner_id:'SELLER',marketplace_id:'US',seller_name:'Seller',marketplace_name:'United States'};
 const session=discoverySession({rows:[row,row]});
 await assert.rejects(()=>discoverBinding(session,account),/binding is unavailable or ambiguous/);
 assert.equal(session.expressions.length,0);assert.equal(session.unsubscribed.length,2);
});

test('discovery verifies the selected account IDs after navigation, even with matching labels',async()=>{
 for(const observedUrl of [url.replace('SELLER','OTHER'),url.replace('=US','=DE'),url+'&sellerId=SELLER',url+'&marketplaceId=US']){
  const session=discoverySession({observedUrl});
  await assert.rejects(()=>discoverBinding(session,account),/selected seller\/marketplace IDs differ/);
  assert.equal(session.expressions.length,7);assert.equal(session.unsubscribed.length,2);
 }
});

test('discovery cannot choose duplicated same-country selector options',async()=>{
 const option={index:0,label:'Seller',country:'United States'};
 const session=discoverySession({options:[option,{...option,index:1}]});
 await assert.rejects(()=>discoverBinding(session,account),/option is unavailable or ambiguous/);
 assert.equal(session.expressions.length,3);assert.equal(session.unsubscribed.length,2);
});

test('authentication failure returns a blocked collector result and releases its task',async()=>{
 const output_dir=await mkdtemp(join(tmpdir(),'ffp-auth-failure-'));
 const session=discoverySession({status:401}),releases=[];
 const request={schema_version:1,operation_id:'auth-failure',account,plan_hash:'a'.repeat(64),minimum_after:'2026-09-16T00:00:00Z',output_dir};
 try{
  const result=await collect(request,{now:()=>Date.parse('2026-09-16T00:00:01Z'),acquire:async()=>({session}),release:async(page,options)=>{releases.push(options);}});
  assert.equal(result.status,'blocked');assert.equal(result.reason,'ffp_account_binding_unavailable');
  assert.match(result.message,/HTTP 401/);assert.equal(result.verified,undefined);assert.equal(result.path,undefined);
  assert.equal(session.calls.filter(x=>x.method==='Network.getResponseBody').length,0);
  assert.equal(session.expressions.length,0);assert.equal(session.unsubscribed.length,2);
  assert.deepEqual(releases,[{outcome:'error',closeTarget:false}]);
 }finally{await rm(output_dir,{recursive:true,force:true});}
});
test('collector receipt binds observed IDs and exact bytes and releases on failure',async()=>{
 const output_dir=await mkdtemp(join(tmpdir(),'ffp-binding-'));let releases=0;
 const deps={now:()=>Date.parse('2026-09-16T00:00:01Z'),acquire:async()=>({session:{}}),release:async()=>{releases++;},discover:async()=>({source_url:url,flatfilepro_display_name:'Seller (United States)',flatfilepro_option_name:'Seller'})};
 const request={schema_version:1,operation_id:'binding-test',account,plan_hash:'a'.repeat(64),minimum_after:'2026-09-16T00:00:00Z',output_dir};
 try{const result=await collect(request,deps);assert.equal(result.status,'collected');const {path,sha256,...receipt}=result;assert.deepEqual(JSON.parse(await readFile(path)),receipt);assert.equal(sha256.length,64);assert.equal(releases,1);
 const failed=await collect(request,{...deps,discover:async()=>({source_url:url.replace('SELLER','OTHER'),flatfilepro_display_name:'Seller',flatfilepro_option_name:'Seller'})});assert.equal(failed.status,'blocked');assert.equal(releases,2);
 }finally{await rm(output_dir,{recursive:true,force:true});}
});
