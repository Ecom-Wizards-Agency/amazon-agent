import test from 'node:test';
import assert from 'node:assert/strict';
import {readCatalogPages} from '../flatfilepro-discovery.mjs';

function fixture({cachedPage=false,wrongPage=false}={}){
 const account={seller_id:'SELLER',marketplace_id:'MARKET',marketplace_label:'Germany',flatfilepro_display_name:'Test (Germany)',context_binding:{seller_id:'SELLER',marketplace_id:'MARKET',unique_label_mapping:true}};
 const listeners=new Map(),bodies=new Map(),reads=new Map();let current=0,reloads=0;
 function emit(page){
  current=page;bodies.clear();
  for(const kind of ['items','total-count']){
   const query=new URLSearchParams({filter:JSON.stringify({brands:['test'],archived:'NOT ARCHIVED',variation:'ALL LISTINGS',sellerId:'SELLER',marketplaceId:'MARKET'}),page:String(page),pageSize:'2','sortModel[]':JSON.stringify({field:'sku',sort:'asc'}),insertOnboardingStep:'false'});
   const id=kind+'-'+page;
   const data=kind==='items'?{rows:[0,1].map(n=>({seller_id:'SELLER',marketplace_id:'MARKET',sku:'SKU'+(2*page+n),asin:'B000000001'}))}:{count:6};
   bodies.set(id,JSON.stringify(data));
   listeners.get('Network.responseReceived')({type:'XHR',requestId:id,response:{url:'https://api.flatfile.pro/amazon-listings/'+kind+'?'+query,status:200}});
   listeners.get('Network.loadingFinished')({requestId:id});
  }
 }
 const session={assertTaskControl:async()=>{},subscribe:(name,fn)=>{listeners.set(name,fn);return()=>listeners.delete(name);},send:async(method,args)=>{
  if(method==='Page.reload'){reloads++;emit(current);return {};}
  if(method==='Network.getResponseBody'){
   assert.ok(bodies.has(args.requestId),'attempted to reread expired response '+args.requestId);
   reads.set(args.requestId,(reads.get(args.requestId)||0)+1);
   return {body:bodies.get(args.requestId),base64Encoded:false};
  }
  if(method==='Runtime.evaluate'){
   let value;
   if(args.expression.includes('buttons[0].click()')){if(cachedPage&&current===0)current=1;else emit(current+1);}
   else if(args.expression.includes('return buttons.map'))value=[{disabled:current===2},{disabled:current===2}];
   else if(args.expression.includes('contextTokens'))value={url:'https://app.flatfile.pro/amazon-listings-items?sellerId=SELLER&marketplaceId=MARKET&page='+(wrongPage&&current===1?99:current),contexts:['Seller & Marketplace Test (Germany)'],contextTokens:[]};
   else if(args.expression.includes('Expected one enabled FlatFilePro control'))emit(0);
   else throw new Error('Unexpected browser expression');
   return {result:{value}};
  }
  assert.ok(['Network.enable','Runtime.enable'].includes(method),method);return {};
 }};
 return {session,account,reads,reloads:()=>reloads};
}
test('catalog pagination retains captured counts when Chrome drops earlier response bodies',async()=>{
 const f=fixture(),pages=await readCatalogPages(f.session,f.account);
 assert.equal(pages.length,3);assert.equal(pages.flatMap(p=>p.items).length,6);
 assert.ok([...f.reads.values()].every(n=>n===1));assert.equal(f.reads.size,6);
});
test('a cached page is reloaded once and still requires complete observed coverage',async t=>{
 let clock=0;t.mock.method(Date,'now',()=>clock+=16000);
 const f=fixture({cachedPage:true}),pages=await readCatalogPages(f.session,f.account);
 assert.equal(f.reloads(),1);assert.equal(pages.length,3);assert.equal(f.reads.size,6);
});
test('a missing page response cannot reload a different page',async t=>{
 let clock=0;t.mock.method(Date,'now',()=>clock+=16000);
 const f=fixture({cachedPage:true,wrongPage:true});
 await assert.rejects(()=>readCatalogPages(f.session,f.account),/retry no longer owns the expected page/);
 assert.equal(f.reloads(),0);
});
