import test from 'node:test';
import assert from 'node:assert/strict';
import {registerHooks} from 'node:module';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {taskIdFor} from '../../browserctl/task-tabs.mjs';
import * as realUi from '../browser-ui.mjs';

// Replace browser boundaries only. Collector validation and durable journals run unchanged.
const boundary=globalThis.__collectorLifecycle={};
const sources={
 'task-tabs.mjs':`export const taskIdFor=globalThis.__collectorLifecycle.taskIdFor;
 export const acquireTaskPage=(...args)=>globalThis.__collectorLifecycle.acquire(...args);
 export const releaseTaskPage=(...args)=>globalThis.__collectorLifecycle.release(...args);
 export const closeReleasedTaskPage=(...args)=>globalThis.__collectorLifecycle.closeReleased(...args);
 export const completeBrowserTask=(...args)=>globalThis.__collectorLifecycle.complete(...args);`,
 'browser-ui.mjs':Object.keys(realUi).map(name=>typeof realUi[name]==='function'?`export const ${name}=(...args)=>globalThis.__collectorLifecycle.ui.${name}(...args);`:`export const ${name}=${JSON.stringify(realUi[name])};`).join('\n'),
 'cdp.mjs':`export const evaluate=(...args)=>globalThis.__collectorLifecycle.evaluate(...args);`,
 'sc-account.mjs':`export const switchAccount=(...args)=>globalThis.__collectorLifecycle.send(...args);export const readIdentity=async()=>({});`,
 'session-lock.mjs':`export const acquireSessionLock=()=>()=>{};`,
 'marketplace-postcode.mjs':`export const ensureDeliveryPostcode=async()=>({ok:true});export const assertDeliveryPostcode=ensureDeliveryPostcode;`,
};
boundary.taskIdFor=taskIdFor;
registerHooks({
 resolve(specifier,context,next){
  const name=specifier.split('/').at(-1);
  if(sources[name])return {url:'collector-fixture:'+name,shortCircuit:true};
  return next(specifier,context);
 },
 load(url,context,next){
  if(url.startsWith('collector-fixture:'))return {format:'module',source:sources[url.slice('collector-fixture:'.length)],shortCircuit:true};
  return next(url,context);
 },
});
const activity=await import('../flatfilepro-activity.mjs');
const images=await import('../image-evidence.mjs');
const listings=await import('../flatfilepro-listings.mjs');
const discovery=await import('../flatfilepro-discovery.mjs');
const exports=await import('../flatfilepro-export.mjs');
const flatfile=await import('../flatfilepro.mjs');
const catalog=await import('../catalog-export.mjs');
const cases=await import('../cases.mjs');
const account={seller_id:'SELLER',marketplace_id:'MARKET',marketplace:'US'};
const asin='B000000001',field='item_name.0.value',hash='a'.repeat(64);

async function fixture(t) {
 const directory=await mkdtemp(join(tmpdir(),'collector-lifecycle-'));
 t.after(()=>rm(directory,{recursive:true,force:true}));
 const events=[],specs=[],releases=[],subscribers=new Map();
 let submitted=false;
 const state=()=>({url:'https://app.flatfile.pro/import?importId=exact',text:'Page 1 of 1',rows:[['sku',field],['sku-one','New']],controls:submitted?[]:[{label:'UPLOAD EXCEL FILE'},{label:'UPDATE LISTINGS'}]});
 boundary.acquire=async spec=>{specs.push(spec);return {taskId:spec.taskId,targetId:'target-'+specs.length,session:{assertTaskControl:async()=>{},send:(...args)=>boundary.send(...args),subscribe:(event,fn)=>subscribers.set(event,fn)}};};
 boundary.release=async(page,options)=>{if(page._released)return;page._released=true;releases.push(options);events.push(['release',options.outcome]);};
 boundary.closeReleased=async page=>events.push(['close-released',page.targetId]);
 boundary.complete=async spec=>events.push(['complete',spec]);
 boundary.ui={...realUi,selectFlatFileProAccount:async()=>state(),context:async()=>state(),snapshot:async()=>state(),
  waitFor:async(read,predicate)=>{const value=await read();assert.ok(predicate(value));return value;},
  screenshot:async()=>{},attach:async()=>{},contextMatches:()=>true,clickFlatFilePro:async()=>{submitted=true;}};
 boundary.send=async(method,args)=>{
  if(method==='Page.navigate'&&args.url.includes('/activity/import/')){
   for(const kind of ['summary','items']){
    subscribers.get('Network.responseReceived')?.({type:'XHR',requestId:kind,response:{status:200,url:`https://api.flatfile.pro/listing-update-runs/exact/${kind}?seller_id=SELLER&marketplace_id=MARKET&pageSize=25`}});
    subscribers.get('Network.loadingFinished')?.({requestId:kind});
   }
  }
  if(method==='Network.getResponseBody')return {body:JSON.stringify(args.requestId==='summary'?{reflected:0,inProgress:1,rejected:0,failed:0}:{items:[{sku:'sku-one',sellerId:'SELLER',marketplaceId:'MARKET',attributes:[{destinationPath:field,submittedValue:'New',status:'pending'}]}],hasMore:false})};
  return {};
 };
 boundary.evaluate=async(_session,source)=>{
  if(source.includes('file_labels:'))return {file_labels:[`SELLER-MARKET/123-ffp-${hash}.xlsx (SKU)`],radios:[{value:'sku',checked:true}],inputs:[{label:'Search attribute headings'}],options:[]};
  if(source.includes('[role="grid"]'))return [];
  if(source.includes('import-status'))return ['Processing'];
  if(source.includes('const record='))return {title:'Product',resolved_asin:asin,images:[{variant:'PT01',url:'https://images.example/live'}],source_id:`https://www.amazon.com/dp/${asin}`};
  return true;
 };
 const upload=join(directory,'upload.xlsx');await writeFile(upload,'fixture');
 const plan={operation_id:'revision-1',account,body:{adapter:'flatfilepro.cdp',upload,mapping:[field],expected_rows:{'sku-one':{[field]:'New'}}}};
 const planPath=join(directory,'plan.json');await writeFile(planPath,JSON.stringify(plan));
 const input={schema_version:1,operation_id:'revision-1',account,plan_hash:hash,submission_id:'exact',expected_rows:{'sku-one':{[field]:'New'}},targets:[{sku:'sku-one',asin}],minimum_after:'2026-01-01T00:00:00Z',output_dir:directory};
 const envelope={schema_version:1,plan,plan_hash:hash,plan_path:planPath,receipt_path:join(directory,'receipt.json')};
 return {events,specs,releases,input,envelope,directory};
}

test('Activity releases completed reads as success and blocked reads as error',async t=>{
 const f=await fixture(t);
 assert.equal((await activity.run(f.input)).status,'collected');
 assert.deepEqual(f.events,[['release','success']]);
 boundary.ui.context=async()=>{throw Error('Wrong account');};
 assert.equal((await activity.run(f.input)).status,'blocked');
 assert.deepEqual(f.events,[['release','success'],['release','error']]);
});

test('image input abort releases without retention; navigated failures retain inspection',async t=>{
 const f=await fixture(t);let navigations=0;
 boundary.send=async()=>{navigations++;throw Error('Read failed');};
 assert.equal((await images.collect({...f.input,targets:{'sku-one':{asin:'invalid',slots:['PT01']}}})).status,'blocked');
 assert.equal(navigations,0);assert.deepEqual(f.events,[['release','success']]);
 assert.equal((await images.collect({...f.input,targets:{'sku-one':{asin,slots:['PT01']}}})).status,'blocked');
 assert.equal(navigations,1);assert.deepEqual(f.events,[['release','success'],['release','error']]);
});

for(const name of ['activity','images','listings','discovery','exports','flatfile']){
 test(`${name} keeps a stable task key across revisions and falls back to operation_id`,async t=>{
  const f=await fixture(t);
  boundary.ui.selectFlatFileProAccount=async()=>{throw Error('Stop after acquisition');};
  for(const [operationId,key] of [['revision-1','job-1'],['revision-2','job-1'],['revision-3',undefined],['revision-4','']]){
   const input={...f.input,operation_id:operationId,task_key:key};
   if(name==='activity')await activity.run(input);
   if(name==='images')await images.collect({...input,targets:{'sku-one':{asin:'invalid',slots:['PT01']}}});
   if(name==='listings')await listings.collect(input);
   if(name==='discovery')await discovery.collect(input);
   if(name==='exports')await exports.collect(input);
   if(name==='flatfile'){
    const envelope={...f.envelope,task_key:key,plan:{...f.envelope.plan,operation_id:operationId}};
    await writeFile(envelope.plan_path,JSON.stringify(envelope.plan));await flatfile.run(envelope);
   }
   assert.equal(f.specs.at(-1).taskId,taskIdFor('amazon-operations',key||operationId));
   assert.equal(f.specs.at(-1).slot,({images:'public-images',listings:'ffp-listing-read',discovery:'ffp-catalog-discovery',exports:'ffp-export'})[name]);
  }
  assert.equal(f.specs.length,4);
 });
}

for(const name of ['activity','images','flatfile']){
 test(`${name} completes once after release only for boolean true and logs completion failure`,async t=>{
  for(const completeTask of [undefined,false,'true',true]){
   const f=await fixture(t);
   const input={...(name==='flatfile'?f.envelope:f.input),task_key:'terminal-job',complete_task:completeTask};
   if(name==='images')input.targets={'sku-one':{asin,slots:['PT01']}};
   const run=name==='activity'?activity.run:name==='images'?images.collect:flatfile.run;
   const before=JSON.stringify(input.plan);
   const result=await run(input);
   assert.equal(result.status,name==='flatfile'?'processing':'collected',JSON.stringify(result));
   assert.equal(JSON.stringify(input.plan),before);
   assert.deepEqual(f.events,completeTask===true?[['release','success'],['complete',{taskId:taskIdFor('amazon-operations','terminal-job')}]]:[['release','success']]);
  }
  const f=await fixture(t),logged=[];
  t.mock.method(console,'error',(...args)=>logged.push(args.join(' ')));
  boundary.complete=async spec=>{f.events.push(['complete',spec]);throw Error('Completion unavailable');};
  const input={...(name==='flatfile'?f.envelope:f.input),complete_task:true};
  if(name==='images')input.targets={'sku-one':{asin,slots:['PT01']}};
  const result=await(name==='activity'?activity.run:name==='images'?images.collect:flatfile.run)(input);
  assert.equal(result.status,name==='flatfile'?'processing':'collected',JSON.stringify(result));
  assert.equal(f.events.filter(event=>event[0]==='complete').length,1);
  assert.match(logged.join('\n'),/Browser task completion failed: Completion unavailable/);
 });
}

test('reconciliation uses task_key and terminal completion also covers durable early returns',async t=>{
 const f=await fixture(t),input={...f.envelope,task_key:'reconcile-job',complete_task:true,mode:'reconcile'};
 const attempt={submission_intent:true,import_url:'https://app.flatfile.pro/import?importId=exact',import_id:'exact'};
 assert.equal((await flatfile.reconcileImport(input,attempt)).status,'collected');
 assert.equal(f.specs[0].taskId,taskIdFor('amazon-operations','reconcile-job'));
 assert.deepEqual(f.events,[['release','success']]);
 assert.equal((await flatfile.run(input)).reason,'no_durable_import_identity');
 assert.equal(f.events.filter(event=>event[0]==='complete').length,1);
});

for(const name of ['activity','images','listings','discovery','exports','flatfile']){
 test(`${name} SIGTERM releases the active page as error before exit`,async t=>{
  const f=await fixture(t),before=process.listeners('SIGTERM');
  let entered,rejectRead;const ready=new Promise(resolve=>entered=resolve);
  boundary.send=()=>{entered();return new Promise((_resolve,reject)=>rejectRead=reject);};
  if(name==='flatfile')boundary.ui.selectFlatFileProAccount=()=>boundary.send();
  boundary.ui.context=async()=>{throw Error('Read interrupted');};
  const exit=t.mock.method(process,'exit',()=>{});
  const input=name==='flatfile'?f.envelope:name==='images'?{...f.input,targets:{'sku-one':{asin,slots:['PT01']}}}:f.input;
  input.close_tab_after=true;
  const running=({activity:activity.run,images:images.collect,listings:listings.collect,discovery:discovery.collect,exports:exports.collect,flatfile:flatfile.run})[name](input);
  await ready;
  const handlers=process.listeners('SIGTERM').filter(listener=>!before.includes(listener));
  assert.equal(handlers.length,1);
  await handlers[0]();
  assert.deepEqual(f.releases,[{outcome:'error',closeTarget:true}]);
  assert.deepEqual(f.events,[['release','error']]);
  assert.equal(exit.mock.calls.length,1);assert.deepEqual(exit.mock.calls[0].arguments,[143]);
  rejectRead(Error('Interrupted'));await running;
  assert.deepEqual(process.listeners('SIGTERM'),before);
 });
}

for(const name of ['listings','catalog']){
 test(`${name} completes exactly once after release and logs completion failure`,async t=>{
  for(const completeTask of [undefined,false,'true',true]){
   const f=await fixture(t),input={...f.input,task_key:'bulk-images:terminal',complete_task:completeTask};
   boundary.ui.snapshot=async()=>({url:'https://sellercentral.amazon.com/listing/reports',text:'Reports'});
   boundary.ui.click=async()=>{};
   boundary.evaluate=async(_session,source)=>{
    if(source.includes('data.statuses'))return [{reportType:{value:'catalog'},processingState:{name:'DONE'},submissionDate:new Date().toISOString(),actions:[{link:'/listing/download'}]}];
    if(source.includes('arrayBuffer'))return {base64:Buffer.from('sku\tasin\na\tB000000001').toString('base64')};
    return {report_value:'catalog',report_label:'Category Listings Report'};
   };
   const read=async()=>({sku:'sku-one',asin,observed_at:new Date().toISOString(),row:{asin}});
   const run=name==='listings'?input=>listings.collect(input,{read}):catalog.collect;
   assert.equal((await run(input)).status,'collected');
   assert.equal(f.specs[0].taskId,taskIdFor('amazon-operations','bulk-images:terminal'));
   assert.deepEqual(f.events,completeTask===true?[['release','success'],['complete',{taskId:taskIdFor('amazon-operations','bulk-images:terminal')}]]:[['release','success']]);
   if(completeTask===true){
    const logged=[];
    const logger=t.mock.method(console,'error',(...args)=>logged.push(args.join(' ')));
    boundary.complete=async spec=>{f.events.push(['complete',spec]);throw Error('Completion unavailable');};
    const before=f.events.length;
    assert.equal((await run(input)).status,'collected');
    assert.deepEqual(f.events.slice(before).map(event=>event[0]),['release','complete']);
    assert.match(logged.join('\n'),/Browser task completion failed: Completion unavailable/);
    logger.mock.restore();
   }
  }
 });
}

test('catalog pending report polls release as success and genuine failures release as error',async t=>{
 const f=await fixture(t);
 boundary.ui.snapshot=async()=>({url:'https://sellercentral.amazon.com/listing/reports',text:'Reports'});
 boundary.ui.click=async()=>{};
 boundary.evaluate=async(_session,source)=>source.includes('data.statuses')?[]:{report_value:'catalog',report_label:'Category Listings Report'};
 assert.equal((await catalog.collect(f.input)).status,'processing');
 assert.deepEqual(f.events,[['release','success']]);
 boundary.evaluate=async()=>{throw Error('Report status unavailable');};
 assert.equal((await catalog.collect(f.input)).status,'blocked');
 assert.deepEqual(f.events,[['release','success'],['release','error']]);
});

for(const name of ['catalog','cases']){
 test(`${name} SIGTERM releases as error before exit and removes handler`,async t=>{
  const f=await fixture(t),before=process.listeners('SIGTERM');
  let entered,rejectRead;const ready=new Promise(resolve=>entered=resolve);
  boundary.send=()=>{entered();return new Promise((_resolve,reject)=>rejectRead=reject);};
  boundary.ui.context=()=>boundary.send();
  const exit=t.mock.method(process,'exit',()=>{});
  const input=name==='cases'?{...f.input,mode:'observe',operation:'case.create'}:f.input;
  input.close_tab_after=true;
  const running=(name==='cases'?cases.run:catalog.collect)(input);
  await ready;
  const handlers=process.listeners('SIGTERM').filter(listener=>!before.includes(listener));
  assert.equal(handlers.length,1);
  await handlers[0]();
  assert.deepEqual(f.releases,[{outcome:'error',closeTarget:true}]);
  assert.deepEqual(f.events,[['release','error']]);
  assert.deepEqual(exit.mock.calls.map(call=>call.arguments),[[143]]);
  rejectRead(Error('Interrupted'));await running;
  assert.deepEqual(process.listeners('SIGTERM'),before);
 });
}

for(const name of ['flatfile','reconcile','catalog','cases']){
 test(`${name} installs SIGTERM before acquisition and removes it on acquisition failure`,async t=>{
  const f=await fixture(t),before=process.listeners('SIGTERM');
  boundary.acquire=async()=>{
   assert.equal(process.listeners('SIGTERM').filter(listener=>!before.includes(listener)).length,1);
   throw Error('Acquisition failed');
  };
  const result=name==='flatfile'?await flatfile.run(f.envelope):name==='reconcile'?await flatfile.reconcileImport(f.envelope,{submission_intent:true,import_url:'https://app.flatfile.pro/import?importId=exact',import_id:'exact'}):name==='catalog'?await catalog.collect(f.input):await cases.run({...f.input,mode:'observe',operation:'case.create'});
  assert.equal(result.status,'blocked');
  assert.deepEqual(process.listeners('SIGTERM'),before);
  assert.deepEqual(f.events,[]);
 });
}

for(const name of ['activity','images','listings','discovery','exports','flatfile','reconcile','catalog','cases']){
 test(`${name} forwards boolean close_tab_after on success and error`,async t=>{
  for(const flag of [undefined,false,'true',true]){
   const f=await fixture(t);
   const input={...(name==='flatfile'||name==='reconcile'?f.envelope:f.input),close_tab_after:flag};
   if(name==='images')input.targets={'sku-one':{asin,slots:['PT01']}};
   if(name==='cases')Object.assign(input,{mode:'observe',operation:'case.create',inputs:{subject:'Exact issue'}});
   if(name==='discovery')delete input.targets;
   let failRead=false;
   const read=async()=>{if(failRead)throw Error('Read failed');return {sku:'sku-one',asin,observed_at:new Date().toISOString(),row:{asin}};};
   const run=()=>({
    activity:()=>activity.run(input),images:()=>images.collect(input),listings:()=>listings.collect(input,{read}),
    discovery:()=>discovery.collect(input,{pages:async()=>{if(failRead)throw Error('Read failed');return [{...account,offset:0,total:0,has_more:false,items:[],observed_at:new Date().toISOString()}];}}),
    exports:()=>exports.collect(input,{read:async()=>({controls:[{label:'EXPORT ALL LISTINGS'}],links:[]}),click:async()=>{}}),
    flatfile:()=>flatfile.run(input),reconcile:()=>flatfile.reconcileImport(input,{submission_intent:true,import_url:'https://app.flatfile.pro/import?importId=exact',import_id:'exact'}),
    catalog:()=>catalog.collect(input),cases:()=>cases.run(input),
   })[name]();
   if(name==='catalog'){
    boundary.ui.snapshot=async()=>({url:'https://sellercentral.amazon.com/listing/reports',text:'Reports'});
    boundary.ui.click=async()=>{};
    boundary.evaluate=async(_session,source)=>source.includes('data.statuses')?[]:{report_value:'catalog',report_label:'Category Listings Report'};
   }
   if(name==='cases'){
    boundary.ui.context=async()=>({url:'https://sellercentral.amazon.com/home',text:'Home'});
    boundary.ui.snapshot=async()=>({url:'https://sellercentral.amazon.com/cu/case-lobby',text:'Case search results '.repeat(10)});
    boundary.evaluate=async()=>({status:200,body:JSON.stringify({caseSearchResultList:[],totalNumberOfResults:0})});
   }
   const result=await run();
   assert.equal(f.releases.length,1,JSON.stringify(result));
   assert.equal(f.specs[0].closeOnFailure,flag===true);
   assert.equal(f.releases[0].closeTarget,flag===true);
   assert.equal(f.releases[0].outcome,'success',JSON.stringify(result));
   failRead=true;
   if(name==='flatfile')await rm(join(f.directory,'flatfilepro-attempt.json'));
   boundary.send=async()=>{throw Error('Read failed');};
   boundary.ui.context=()=>boundary.send();
   boundary.ui.selectFlatFileProAccount=()=>boundary.send();
   await run();
   assert.equal(f.releases.at(-1).closeTarget,flag===true);
   assert.equal(f.releases.at(-1).outcome,'error');
  }
 });
}

test('import recovery forwards close_tab_after on SIGTERM',async t=>{
 const f=await fixture(t),before=process.listeners('SIGTERM');
 let entered,rejectRead;const ready=new Promise(resolve=>entered=resolve);
 boundary.send=()=>{entered();return new Promise((_resolve,reject)=>rejectRead=reject);};
 const exit=t.mock.method(process,'exit',()=>{});
 const running=flatfile.reconcileImport({...f.envelope,close_tab_after:true},
  {submission_intent:true,import_url:'https://app.flatfile.pro/import?importId=exact',import_id:'exact'});
 await ready;
 const handlers=process.listeners('SIGTERM').filter(listener=>!before.includes(listener));
 assert.equal(handlers.length,1);
 await handlers[0]();
 assert.deepEqual(f.releases,[{outcome:'error',closeTarget:true}]);
 assert.deepEqual(exit.mock.calls.map(call=>call.arguments),[[143]]);
 rejectRead(Error('Interrupted'));await running;
 assert.deepEqual(process.listeners('SIGTERM'),before);
});

test('pre-submit handoff keeps the exact import target and forwards close_tab_after to the listing read',async t=>{
 const f=await fixture(t),page={targetId:'exact-import'},resumed={targetId:'exact-import'},events=[];
 const input={...f.envelope,close_tab_after:true,plan:{...f.envelope.plan,body:{
  sku_asins:{'sku-one':asin},image_before_rows:{'sku-one':{}},
 }}};
 const fresh={status:'collected'};
 const result=await flatfile.refreshImagePreflight(input,page,{
  release:async(target,options)=>{assert.equal(target,page);assert.equal(options.closeTarget===true,false);events.push('release');},
  collect:async envelope=>{assert.equal(envelope.close_tab_after,true);assert.equal(envelope.plan,undefined);events.push('collect');return fresh;},
  acquire:async spec=>{assert.equal(spec.expectedTargetId,page.targetId);assert.equal(spec.closeOnFailure,true);events.push('acquire');return resumed;},
 });
 assert.deepEqual(events,['release','collect','acquire']);
 assert.deepEqual(result,{page:resumed,fresh});
});

for(const step of ['collect','reacquire'])for(const flag of [undefined,false,true]){
 test(`pre-submit ${step} failure closes retained target only when close_tab_after=${flag}`,async t=>{
  const f=await fixture(t),page={targetId:'exact-import'},events=[];
  const input={...f.envelope,close_tab_after:flag,plan:{...f.envelope.plan,body:{sku_asins:{'sku-one':asin},image_before_rows:{'sku-one':{}}}}};
  await assert.rejects(flatfile.refreshImagePreflight(input,page,{
   release:async(target,options)=>{assert.equal(target,page);assert.deepEqual(options,{outcome:'handoff'});page._released=true;},
   collect:async()=>{if(step==='collect')throw Error('nested failed');return {status:'collected'};},
   acquire:async()=>{throw Error('reacquire failed');},
   closeReleased:async target=>{assert.equal(target,page);events.push(target.targetId);},
  }),/failed/);
  assert.deepEqual(events,flag===true?['exact-import']:[]);
 });
}

for(const flag of [undefined,true]){
 test(`SIGTERM during nested pre-submit read cleans both tabs before exit, close_tab_after=${flag}`,async t=>{
  const f=await fixture(t),before=process.listeners('SIGTERM');
  const input={...f.envelope,close_tab_after:flag,plan:{...f.envelope.plan,body:{sku_asins:{'sku-one':asin},image_before_rows:{'sku-one':{}}}}};
  const page=await boundary.acquire({taskId:'import'});
  let entered,rejectRead,finishClose;
  const ready=new Promise(resolve=>entered=resolve);
  const closeDone=new Promise(resolve=>finishClose=resolve);
  boundary.ui.selectFlatFileProAccount=()=>{entered();return new Promise((_resolve,reject)=>rejectRead=reject);};
  boundary.closeReleased=async target=>{await closeDone;f.events.push(['close-released',target.targetId]);};
  const exit=t.mock.method(process,'exit',()=>{
   assert.deepEqual(f.events,flag===true?[['release','handoff'],['release','error'],['close-released',page.targetId]]:[['release','handoff'],['release','error']]);
  });
  const running=flatfile.refreshImagePreflight(input,page);
  const rejected=assert.rejects(running,/interrupted/);
  await ready;
  const handlers=process.listeners('SIGTERM').filter(listener=>!before.includes(listener));
  assert.equal(handlers.length,2);
  const stopping=Promise.all(handlers.map(handler=>handler()));
  await new Promise(resolve=>setImmediate(resolve));
  if(flag===true)assert.equal(exit.mock.calls.length,0);
  finishClose();await stopping;
  assert.deepEqual(exit.mock.calls.map(call=>call.arguments),[[143]]);
  assert.equal(f.releases[1].closeTarget,flag===true);
  rejectRead(Error('Interrupted'));await rejected;
  assert.equal(f.specs.length,2,'SIGTERM must not reacquire the import target');
  assert.deepEqual(process.listeners('SIGTERM'),before);
 });
}

for(const flag of [undefined,true]){
 test(`SIGTERM during pre-submit reacquisition releases resumed handle, close_tab_after=${flag}`,async t=>{
  const f=await fixture(t),before=process.listeners('SIGTERM'),page={targetId:'exact-import'},resumed={targetId:'exact-import'},releases=[];
  const input={...f.envelope,close_tab_after:flag,plan:{...f.envelope.plan,body:{sku_asins:{'sku-one':asin},image_before_rows:{'sku-one':{}}}}};
  let entered,finishAcquire;const ready=new Promise(resolve=>entered=resolve);
  const exit=t.mock.method(process,'exit',()=>{});
  const running=flatfile.refreshImagePreflight(input,page,{
   release:async(target,options)=>{target._released=true;releases.push(options);},
   collect:async()=>({status:'collected'}),
   acquire:()=>{entered();return new Promise(resolve=>finishAcquire=resolve);},
   closeReleased:async()=>{assert.fail('Resumed handle owns the target');},
  });
  const rejected=assert.rejects(running,/interrupted/);
  await ready;
  const handlers=process.listeners('SIGTERM').filter(listener=>!before.includes(listener));
  assert.equal(handlers.length,1);
  const stopping=handlers[0]();finishAcquire(resumed);await stopping;await rejected;
  assert.deepEqual(releases,[{outcome:'handoff'},{outcome:'error',closeTarget:flag===true}]);
  assert.deepEqual(exit.mock.calls.map(call=>call.arguments),[[143]]);
  assert.deepEqual(process.listeners('SIGTERM'),before);
 });
}

test('SIGTERM during import handoff release waits for release before closing',async t=>{
  const f=await fixture(t),before=process.listeners('SIGTERM'),page={targetId:'exact-import'},events=[];
  const input={...f.envelope,close_tab_after:true,plan:{...f.envelope.plan,body:{sku_asins:{'sku-one':asin},image_before_rows:{'sku-one':{}}}}};
  let finishRelease;
  const exit=t.mock.method(process,'exit',()=>events.push('exit'));
  const running=flatfile.refreshImagePreflight(input,page,{
   release:async()=>{page._released=true;await new Promise(resolve=>finishRelease=resolve);events.push('released');},
   collect:async()=>{assert.fail('Interrupted handoff must not start a listing read');},
   closeReleased:async target=>{assert.equal(target,page);events.push('closed');},
  });
  const rejected=assert.rejects(running,/interrupted/);
  const handlers=process.listeners('SIGTERM').filter(listener=>!before.includes(listener));
  const stopping=handlers[0]();
  assert.deepEqual(events,[]);finishRelease();await stopping;await rejected;
  assert.deepEqual(events,['released','closed','exit']);
  assert.deepEqual(exit.mock.calls.map(call=>call.arguments),[[143]]);
  assert.deepEqual(process.listeners('SIGTERM'),before);
 });

test('nested listing SIGTERM waits for an in-progress release and handoff cleanup',async t=>{
  const f=await fixture(t),before=process.listeners('SIGTERM'),events=[];
  let entered,finishRelease;const ready=new Promise(resolve=>entered=resolve);
  const exit=t.mock.method(process,'exit',()=>events.push('exit'));
  const running=listings.collect({...f.input,close_tab_after:true},{
   read:async()=>({sku:'sku-one',asin,observed_at:new Date().toISOString(),row:{asin}}),
   release:async page=>{page._released=true;entered();await new Promise(resolve=>finishRelease=resolve);events.push('released');},
   beforeSigtermExit:async()=>events.push('handoff-cleaned'),
  });
  await ready;
  const handlers=process.listeners('SIGTERM').filter(listener=>!before.includes(listener));
  assert.equal(handlers.length,1);
  const stopping=handlers[0]();assert.deepEqual(events,[]);
  finishRelease();await stopping;await running;
  assert.deepEqual(events,['released','handoff-cleaned','exit']);
  assert.deepEqual(exit.mock.calls.map(call=>call.arguments),[[143]]);
  assert.deepEqual(process.listeners('SIGTERM'),before);
 });
