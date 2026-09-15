import test from 'node:test';
import assert from 'node:assert/strict';
import {registerHooks,syncBuiltinESMExports} from 'node:module';
import fsPromises from 'node:fs/promises';
import fs from 'node:fs';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {spawn} from 'node:child_process';
import {acquireSessionLockWithWait} from '../../browserctl/session-lock.mjs';
import {releaseTaskPage} from '../../browserctl/task-tabs.mjs';

function outputTest(name,run){
 if(process.env.WP16G_OUTPUT_CASE){
  if(process.env.WP16G_OUTPUT_CASE===name)test(name,run);
  return;
 }
 test(name,{timeout:30000},async t=>{
  const directory=await mkdtemp(join(tmpdir(),'wp16g-output-launcher-'));
  t.after(()=>rm(directory,{recursive:true,force:true}));
  const env={...process.env,WP16G_OUTPUT_CASE:name,AMAZON_BROWSER_LOCK_DIR:directory};
  for(const key of ['CDP_PORT','CDP_PROFILE','CDP_HOST','AMAZON_BROWSER_SESSION','AMAZON_BROWSER_LOCK_TOKEN','AMAZON_BROWSER_LOCK_CHAIN','AMAZON_BROWSER_LAUNCHER_PID','AMAZON_BROWSER_LAUNCHER_CONTROL','AMAZON_BROWSER_LOCK_WAIT_MS','NODE_TEST_CONTEXT'])delete env[key];
  const child=spawn(process.execPath,[new URL('../../browserctl/browserctl.mjs',import.meta.url).pathname,'run','--',process.execPath,new URL(import.meta.url).pathname],{env});
  let stdout='',stderr='';child.stdout.on('data',data=>{stdout+=data;});child.stderr.on('data',data=>{stderr+=data;});
  t.after(()=>child.kill());
  const code=await new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',resolve);});
  assert.equal(code,0,stdout+stderr);
  assert.equal(await readFile(join(directory,'output-tests-exit'),'utf8'),'0');
  assert.equal(fs.existsSync(join(directory,'cdp-9223.lock')),false);
 });
}
if(process.env.WP16G_OUTPUT_CASE)process.once('exit',code=>fs.writeFileSync(join(process.env.AMAZON_BROWSER_LOCK_DIR,'output-tests-exit'),String(code)));

// Run the real entrypoints and output code with browser-only boundaries replaced.
const state=globalThis.__wp16dOutput={held:false,events:[],evaluate:null,shot:null};
state.acquireLock=()=>acquireSessionLockWithWait(9223,'output-test');
state.releasePage=releaseTaskPage;
state.assertUnlocked=()=>assert.equal(fs.existsSync(join(process.env.AMAZON_BROWSER_LOCK_DIR,'cdp-9223.lock')),false,'launcher lock must be absent during output');
const sources={
 'node:child_process':`export const execFileSync=(...args)=>globalThis.__wp16dOutput.exec(...args);`,
 'task-tabs.mjs':`export const taskIdFor=(...v)=>v.join(':');
 export async function acquireTaskPage(spec){const s=globalThis.__wp16dOutput;s.beforeAcquire?.();const unlock=await s.acquireLock();s.held=true;s.events.push('acquire');return {port:9223,taskId:spec.taskId,targetId:'target',_unlockSession:unlock,_registry:{releaseTaskTabControl:async()=>{}},session:{close(){},send:async()=>{},assertTaskControl:async()=>{}}};}
 export const closeReleasedTaskPage=async()=>false;export const completeBrowserTask=async()=>{};
 export async function releaseTaskPage(page,options){const s=globalThis.__wp16dOutput;await s.releasePage(page,options);s.assertUnlocked();s.held=false;s.events.push('release:'+options.outcome);}`,
 'cdp.mjs':`export const ensureChrome=async()=>({});export const listPages=async()=>[];
 export const evaluate=(...args)=>globalThis.__wp16dOutput.evaluate(...args);`,
 'task-evidence.mjs':`export const captureTaskEvidence=async()=>globalThis.__wp16dOutput.shot;`,
 'lease-registry.mjs':`export const listTaskTabs=async()=>[{port:9223,taskId:'audit',targetId:'target',slot:'primary',workflow:'audit'}];`,
 'marketplace-postcode.mjs':`export const ensureDeliveryPostcode=async()=>({ok:true});`,
 'sc-account.mjs':`export const inspectPage=async()=>({pageKind:'app',authState:'authenticated',facts:{url:'https://sellercentral.amazon.com/home'}});
 export const readIdentity=async()=>({displayName:'Seller',merchantId:'SELLER',marketplace:'US'});
 export const identityFieldsConsistent=()=>({ok:true});export const accountParamsFrom=()=>null;
 export const reportAccountParams=()=>null;export const accountMatches=()=>true;
 export const trustedClick=async()=>{};export const switchAccount=async()=>{};export const probeTab=async()=>{};export const doctorVerdict=()=>{};`,
 'format-seller-reports.mjs':`export const format=doc=>{const s=globalThis.__wp16dOutput;s.assertUnlocked();s.events.push('format');return 'sku\\nfixture\\n';};`,
 'client.mjs':`export class ArtifactRun {constructor(){globalThis.__wp16dOutput.assertUnlocked();this.state='active';} register(){globalThis.__wp16dOutput.assertUnlocked();globalThis.__wp16dOutput.events.push('register');} complete(outcome){this.state=outcome;globalThis.__wp16dOutput.events.push('complete:'+outcome);}}`,
};
if(process.env.WP16G_OUTPUT_CASE)registerHooks({
 resolve(specifier,context,next){const name=specifier.split('/').at(-1);if(sources[name])return {url:'wp16d-output:'+name,shortCircuit:true};return next(specifier,context);},
 load(url,context,next){if(url.startsWith('wp16d-output:'))return {format:'module',source:sources[url.slice('wp16d-output:'.length)],shortCircuit:true};return next(url,context);},
});

async function fixture(t){
 const directory=await mkdtemp(join(tmpdir(),'wp16d-output-'));
 t.after(()=>rm(directory,{recursive:true,force:true}));
 Object.assign(state,{held:false,events:[]});
 t.mock.method(globalThis,'setTimeout',fn=>{queueMicrotask(fn);return 0;});
 t.mock.method(console,'log',()=>{});t.mock.method(console,'error',()=>{});
 const argv=process.argv; t.after(()=>{process.argv=argv;});
 state.shot={get data(){state.assertUnlocked();return Buffer.from('png');},evidence:{verified_identity:{accountName:'Seller',marketplace:'US',url:'https://example.test'},toJSON(){state.assertUnlocked();return {verified_identity:this.verified_identity};}}};
 return directory;
}

outputTest('S13 DataDive writes and hashes its packs, screenshot and receipt after release',async t=>{
 const directory=await fixture(t);
 state.evaluate=async(_session,source)=>source.includes('document.body.innerText')?{text:'widget Search Terms 1 Relev.'}:{success:true,data:{nicheId:'niche',marketplace:'US',keywords:[{toJSON(){state.assertUnlocked();return {keyword:'widget'};}}]}};
 const {readNiche}=await import('../../datadive-support/read-niche.mjs');
 const result=await readNiche({nicheId:'niche',marketplace:'US',heroKeyword:'widget',outDir:directory});
 assert.equal(result.artifacts.length,5);assert.equal(result.counts.mkl,1);
 assert.deepEqual(JSON.parse(await readFile(join(directory,'receipt.json'),'utf8')),result);
 assert.deepEqual(state.events,['acquire','release:handoff']);
});

outputTest('S14 listing copy serializes its result after release',async t=>{
 const directory=await fixture(t),out=join(directory,'listings.json');
 state.evaluate=async()=>({asin:'B000000001',title:'Widget',status:'ok',toJSON(){state.assertUnlocked();return {asin:this.asin,title:this.title,status:this.status};}});
 process.argv=['node','capture-cdp.mjs','B000000001',out];
 await import('../../listing-capture/capture-cdp.mjs');
 assert.equal(JSON.parse(await readFile(out,'utf8')).listings[0].title,'Widget');
 assert.deepEqual(state.events,['acquire','release:success']);
});

for(const output of [true,false])outputTest(`S15 listing images serialize after release, --out=${output}`,async t=>{
 const directory=await fixture(t),out=join(directory,'images.json');
 state.evaluate=async()=>({asin:'B000000001',title:'Widget',images:[],aplus:{present:false},toJSON(){state.assertUnlocked();return {asin:this.asin};}});
 process.argv=['node','extract-amazon-listing-images.mjs','B000000001',...(output?['--out',out]:[])];
 await import(`../../listing-capture/extract-amazon-listing-images.mjs?output=${output}`);
 if(output)assert.equal(JSON.parse(await readFile(out,'utf8')).asin,'B000000001');
 assert.deepEqual(state.events,['acquire','release:success']);
});

outputTest('S16 audit captures write their screenshots after each release',async t=>{
 const directory=await fixture(t),spec=join(directory,'spec.json');
 fs.writeFileSync(spec,JSON.stringify({output_dir:directory,task:{taskId:'audit',workflow:'audit',targetId:'target'},captures:[{id:'first'},{id:'second'}]}));
 process.argv=['node','capture_audit_evidence.mjs',spec];
 await import('../../amazon-ad-audit/capture_audit_evidence.mjs');
 assert.equal(JSON.parse(await readFile(join(directory,'evidence_candidates.json'),'utf8')).candidates.length,2);
 assert.deepEqual(state.events,['acquire','release:handoff','acquire','release:handoff']);
});

outputTest('S24 surveillance writes screenshot bytes and evidence after release',async t=>{
 const directory=await fixture(t),out=join(directory,'capture.png');
 const {captureScreenshot}=await import('../../amazon-brand-surveillance/browser.mjs');
 assert.equal(await captureScreenshot('https://www.amazon.com/dp/B000000001',out),out);
 assert.equal(await readFile(out,'utf8'),'png');
 assert.equal(JSON.parse(await readFile(out+'.json','utf8')).verified_identity.accountName,'Seller');
 assert.deepEqual(state.events,['acquire','release:success']);
});

for(const report of ['business','sqp','split'])outputTest(`S12 ${report} formats and registers artifacts only after release`,async t=>{
 const directory=await fixture(t),out=join(directory,'report.csv');
 state.evaluate=async(_session,source)=>source.includes('return await fetch')?{batches:[{asin:'B000000001',rows:[]}],toJSON(){state.assertUnlocked();return {batches:this.batches};}}:true;
 process.argv=['node','run.mjs',report==='business'?'business':'sqp','--out',out,'--verbose',...(report==='business'?['--start','2026-09-01','--end','2026-09-07']:['--asins','B000000001','--weeks','2026-09-05',...(report==='split'?['--split']:[])])];
 const exits=process.listeners('exit');
 await import(`../../report-fetcher/run.mjs?report=${report}`);
 for(let i=0;i<100&&!state.events.some(e=>e.startsWith('complete:'));i++)await new Promise(resolve=>setImmediate(resolve));
 for(const listener of process.listeners('exit'))if(!exits.includes(listener))process.removeListener('exit',listener);
 const file=report==='split'?out.replace('.csv','_B000000001.csv'):out;
 assert.equal(await readFile(file,'utf8'),'sku\nfixture\n');
 assert.ok(state.events.indexOf('release:success')<state.events.indexOf('format'));
 assert.equal(state.events.at(-1),'complete:success');
});

outputTest('S21 initial workbook staging runs with no launcher lock',async t=>{
 const directory=await fixture(t),upload=join(directory,'upload.xlsx'),planPath=join(directory,'plan.json');
 const plan={operation_id:'staging',account:{},body:{adapter:'flatfilepro.cdp',upload}};
 fs.writeFileSync(upload,'immutable workbook');fs.writeFileSync(planPath,JSON.stringify(plan));
 const input={schema_version:1,plan,plan_hash:'a'.repeat(64),plan_path:planPath,receipt_path:join(directory,'receipt.json')};
 const staged=join(directory,'ffp-'+input.plan_hash+'.xlsx');
 const read=fsPromises.readFile,write=fsPromises.writeFile;let reads=0,writes=0;
 const readMock=t.mock.method(fsPromises,'readFile',async(path,...args)=>{
  if(path===upload){state.assertUnlocked();reads++;}return read(path,...args);
 });
 const writeMock=t.mock.method(fsPromises,'writeFile',async(path,...args)=>{
  if(path===staged){state.assertUnlocked();writes++;}return write(path,...args);
 });
 syncBuiltinESMExports();t.after(()=>{readMock.mock.restore();writeMock.mock.restore();syncBuiltinESMExports();});
 state.beforeAcquire=()=>{
  state.assertUnlocked();assert.equal(fs.readFileSync(staged,'utf8'),'immutable workbook');
  throw Error('staging checked before browser acquisition');
 };
 const {run}=await import('../flatfilepro.mjs');
 const result=await run(input);
 assert.equal(result.status,'blocked');assert.equal(result.message,'staging checked before browser acquisition');
 assert.equal(reads,1);assert.equal(writes,1);assert.deepEqual(state.events,[]);
 assert.deepEqual(JSON.parse(await readFile(input.receipt_path,'utf8')),result);
});

outputTest('S22 PDF tool preflight runs before acquiring a shipment page',async t=>{
 await fixture(t);
 const {StaBrowser}=await import('../shipments.mjs');
 const browser=new StaBrowser({receipt_path:'/tmp/receipt.json'});
 state.exec=(command,args)=>{state.assertUnlocked();assert.deepEqual(args,['-v']);state.events.push(command);};
 await browser.open({plan:{operation_id:'shipment',account:{marketplace:'US',seller_central_name:'Seller'}}});
 await browser.close();
 assert.deepEqual(state.events,['pdfinfo','pdftotext','acquire','release:inspection']);
 state.exec=()=>{throw Error('PDF tools missing');};
 state.events=[];
 await assert.rejects(browser.open({}),/PDF tools missing/);
 assert.deepEqual(state.events,[]);
});

outputTest('S23 label hashing and all PDF subprocesses run after both claims release',async t=>{
 const directory=await fixture(t),file=join(directory,'labels.pdf');
 fs.mkdirSync(join(directory,'shipment-labels'));fs.writeFileSync(file,'%PDF-fixture');
 const {StaBrowser}=await import('../shipments.mjs');
 const browser=new StaBrowser({receipt_path:join(directory,'receipt.json')});
 const unlock=await state.acquireLock();state.held=true;
 browser.session={close(){},assertTaskControl:async()=>{},send:async()=>{}};
 browser.page={port:9223,session:browser.session,_unlockSession:unlock,_registry:{releaseTaskTabControl:async()=>{},acquireTaskDownloads:async()=>({}),releaseTaskDownloads:async()=>state.events.push('download-release')}};
 browser.release=async page=>{await state.releasePage(page);state.assertUnlocked();state.held=false;state.events.push('page-release');};
 browser.assertIdentity=async()=>assert.equal(state.held,true);
 browser.ev=async()=>'PackageLabel_Thermal_NonPCP';browser.clickAt=async()=>{};
 browser.wait=async()=>file;
 state.exec=(command,args)=>{
  state.assertUnlocked();
  assert.equal(state.held,false);assert.deepEqual(state.events.slice(0,2),['download-release','page-release']);
  state.events.push(command);
  if(command==='pdftotext')return 'FBAEXAMPLE01U000001\nSingle SKU\nWIDGET\nQty 10\f';
  return args.length===1?'Pages: 1\n':'Page 1 size: 288 x 432 pts\n';
 };
 const labels=await browser.downloadLabels({shipment:{cartons:[{id:'BOX1',contents:{WIDGET:10}}]}},{shipment_ids:['FBAEXAMPLE01']});
 assert.equal(labels[0].carton_id,'BOX1');assert.match(labels[0].sha256,/^[a-f0-9]{64}$/);
 assert.deepEqual(state.events,['download-release','page-release','pdfinfo','pdfinfo','pdftotext']);
 await browser.close();assert.equal(state.events.length,5);
});

outputTest('S12 report errors release as error before writing the verbose response',async t=>{
 const directory=await fixture(t),out=join(directory,'failed.csv');
 state.evaluate=async(_session,source)=>source.includes('return await fetch')?{error:'Report unavailable',toJSON(){state.assertUnlocked();return {error:this.error};}}:true;
 process.argv=['node','run.mjs','business','--out',out,'--verbose','--start','2026-09-01','--end','2026-09-07'];
 const exitCode=process.exitCode,exits=process.listeners('exit');
 t.after(()=>{process.exitCode=exitCode;for(const listener of process.listeners('exit'))if(!exits.includes(listener))process.removeListener('exit',listener);});
 await import('../../report-fetcher/run.mjs?report=error');
 for(let i=0;i<100&&process.exitCode!==1;i++)await new Promise(resolve=>setImmediate(resolve));
 assert.equal(process.exitCode,1);
 assert.equal(JSON.parse(await readFile(out.replace('.csv','.raw.json'),'utf8')).error,'Report unavailable');
 assert.equal(fs.existsSync(out),false);
 assert.deepEqual(state.events,['acquire','release:error','register']);
});
