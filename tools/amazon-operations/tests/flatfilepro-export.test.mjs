import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, readFile, writeFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import fsPromises from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import { collect, exportDate, selectCompletedExport, validateExportLink } from '../flatfilepro-export.mjs';

const account={seller_id:'SELLER1',marketplace_id:'MARKET1',marketplace:'DE'};
const OLD='all-2026-09-12-01-02-03-000.xlsx',FRESH='all-2026-09-13-12-55-22-631.xlsx';
const link=name=>({name,href:`https://ffp-export.s3.us-east-2.amazonaws.com/${account.seller_id}-${account.marketplace_id}/${name}`});
const notice=`Export of listings complete for ${account.seller_id} on marketplace ${account.marketplace_id}, download it now.`;
const complete={text:notice,links:[link(OLD),link(FRESH)],controls:[{label:'EXPORT ALL LISTINGS',disabled:false}]};
const marker={requested_at:'2026-09-13T12:55:00.000Z',before_names:[OLD]};

test('observed UTC filename is parsed exactly and overflow dates are rejected',()=>{
  assert.equal(exportDate(FRESH),'2026-09-13T12:55:22.631Z');
  for(const name of ['all-2026-02-30-12-55-22-631.xlsx','all-2026-09-13-25-55-22-631.xlsx','../'+FRESH,'latest.xlsx'])
    assert.throws(()=>exportDate(name));
});

test('request and completion receipts are written outside every page claim',async t=>{
  const {input,facts,dependencies}=await fixture(t),open=fsPromises.open;
  let writes=0;
  const mocked=t.mock.method(fsPromises,'open',async(path,flags,...args)=>{
    if(String(path).includes('ffp-export-request.json')&&['wx','w'].includes(flags)){
      assert.equal(facts.acquires,facts.releases,'receipt write must follow release');writes++;
    }
    return open(path,flags,...args);
  });
  syncBuiltinESMExports();
  t.after(()=>{mocked.mock.restore();syncBuiltinESMExports();});
  assert.equal((await collect(input,dependencies)).status,'collected');
  assert.equal(writes,3);
});

test('changed reservation or account after receipt release prevents the export click',async t=>{
  for(const change of ['reservation','account']){
    const {directory,input,facts,dependencies}=await fixture(t),acquire=dependencies.acquire,read=dependencies.read;
    dependencies.acquire=async spec=>{
      const page=await acquire(spec);
      if(facts.acquires===2&&change==='reservation')await writeFile(join(directory,'ffp-export-request.json'),'{}');
      return page;
    };
    dependencies.read=async(...args)=>{if(facts.acquires===2&&change==='account')throw Error('Account changed');return read(...args);};
    const result=await collect(input,dependencies);
    assert.equal(result.status,'blocked');assert.match(result.message,/reservation changed|Account changed/);
    assert.equal(facts.clicks,0);assert.equal(facts.acquires,facts.releases);
  }
});

test('download link binds the exact public bucket, seller, marketplace and filename',()=>{
  validateExportLink(link(FRESH),account);
  for(const href of [link(FRESH).href+'?token=unused',link(FRESH).href.replace(account.seller_id,'OTHER'),link(FRESH).href.replace('ffp-export.s3.us-east-2.amazonaws.com','evil.example'),link(FRESH).href.replace(FRESH,OLD)])
    assert.throws(()=>validateExportLink({name:FRESH,href},account),/exact seller\/marketplace path/);
});

test('old files cannot substitute for this completed export',()=>{
  const at=Date.parse('2026-09-13T12:56:00Z');
  assert.equal(selectCompletedExport(complete,marker,account,marker.requested_at,at).name,FRESH);
  assert.equal(selectCompletedExport({...complete,links:[link(OLD)]},marker,account,marker.requested_at,at),null);
  assert.equal(selectCompletedExport(complete,{...marker,before_names:[OLD,FRESH]},account,marker.requested_at,at),null);
  assert.throws(()=>selectCompletedExport({...complete,text:notice.replace(account.marketplace_id,'OTHER')},marker,account,marker.requested_at,at),/completion/);
  assert.throws(()=>selectCompletedExport({...complete,links:[...complete.links,link('all-2026-09-13-12-55-23-000.xlsx')]},marker,account,marker.requested_at,at),/More than one/);
});

async function fixture(t) {
  const directory=await mkdtemp(join(tmpdir(),'ffp-export-'));t.after(()=>rm(directory,{recursive:true,force:true}));
  const input={schema_version:1,operation_id:'export-test',account,plan_hash:'a'.repeat(64),minimum_after:'2026-09-13T12:54:00Z',output_dir:directory};
  const facts={time:Date.parse(marker.requested_at),clicks:0,downloads:0,acquires:0,releases:0,pending:false,lostClick:false,changeAccount:false,reads:0,outcomes:[],specs:[],navigations:[]};
  const dependencies={
    now:()=>facts.time,
    acquire:async spec=>{facts.acquires++;facts.specs.push(spec);return {session:{send:async(method,args)=>facts.navigations.push({method,...args})}};},release:async(page,{outcome})=>{facts.releases++;facts.outcomes.push(outcome);},
    read:async()=>{
      facts.reads++;
      if(facts.changeAccount&&facts.downloads)throw new Error('Exact selected account changed');
      return facts.clicks&&!facts.pending?complete:{text:'Export',links:[link(OLD)],controls:[{label:'EXPORT ALL LISTINGS',disabled:false}]};
    },
    click:async(_session,label)=>{
      assert.equal(label,'EXPORT ALL LISTINGS');
      assert.equal(JSON.parse(await readFile(join(directory,'ffp-export-request.json'),'utf8')).state,'request_outcome_unknown');
      facts.clicks++;facts.time=Date.parse('2026-09-13T12:55:23Z');
      if(facts.lostClick)throw new Error('Lost export click response');
    },
    download:async url=>{assert.equal(url,link(FRESH).href);assert.equal(facts.acquires,facts.releases,'public download must run after release');facts.downloads++;return {bytes:Buffer.from('PK\x03\x04fixture-workbook'),content_type:'application/octet-stream'};},
  };
  return {directory,input,facts,dependencies};
}

test('collector records request before click, downloads the new file and reuses immutable result',async t=>{
  const {input,facts,dependencies}=await fixture(t);
  const result=await collect(input,dependencies);
  assert.equal(result.status,'collected');assert.equal(result.complete_report,true);
  assert.equal(result.report_generated_at,'2026-09-13T12:55:22.631Z');
  assert.equal(facts.clicks,1);assert.equal(facts.downloads,1);
  const again=await collect(input,dependencies);
  assert.equal(again.sha256,result.sha256);
  assert.equal(facts.clicks,1);assert.equal(facts.downloads,1);assert.equal(facts.acquires,4);
  assert.deepEqual(facts.specs[0],facts.specs[3]);
});

test('pending export is resumed without generating a second export',async t=>{
  const {input,facts,dependencies}=await fixture(t);facts.pending=true;
  assert.equal((await collect(input,dependencies)).status,'processing');
  assert.equal((await collect(input,dependencies)).status,'processing');
  assert.equal(facts.clicks,1);
  assert.deepEqual(facts.outcomes,['success','success','success','success']);
  assert.deepEqual(facts.navigations,Array(2).fill({method:'Page.navigate',url:'https://app.flatfile.pro/exports'}));
  facts.pending=false;
  assert.equal((await collect(input,dependencies)).status,'collected');
  assert.equal(facts.clicks,1);
});

test('lost export click response recovers the finished file without another click',async t=>{
  const {input,facts,dependencies}=await fixture(t);facts.lostClick=true;
  const unknown=await collect(input,dependencies);
  assert.equal(unknown.status,'processing');assert.equal(unknown.reason,'ffp_export_request_outcome_unknown');
  assert.deepEqual(facts.outcomes,['success','success']);
  facts.lostClick=false;
  assert.equal((await collect(input,dependencies)).status,'collected');
  assert.equal(facts.clicks,1);
});

test('account changes during download cannot produce a collected export',async t=>{
  const {input,facts,dependencies}=await fixture(t);facts.changeAccount=true;
  const result=await collect(input,dependencies);
  assert.equal(result.status,'blocked');assert.match(result.message,/account changed/);
  assert.equal(facts.releases,4);assert.deepEqual(facts.outcomes,['success','success','success','error']);
});

test('changed cached bytes and a reused marker with another plan fail closed',async t=>{
  const {input,dependencies}=await fixture(t);
  const first=await collect(input,dependencies);
  await writeFile(first.path,'changed');
  assert.match((await collect(input,dependencies)).message,/export changed/);
  assert.match((await collect({...input,plan_hash:'b'.repeat(64)},dependencies)).message,/another account or operation/);
});

test('a downloaded file left before the final receipt is verified without overwriting',async t=>{
  const {input,directory,dependencies}=await fixture(t);
  await writeFile(join(directory,FRESH),Buffer.from('PK\x03\x04fixture-workbook'));
  assert.equal((await collect(input,dependencies)).status,'collected');
});

for(const lostClick of [false,true])test(`S4 unmatched export expires at 24 hours, unknown click=${lostClick}`,async t=>{
  const {input,facts,dependencies}=await fixture(t);
  facts.pending=true;facts.lostClick=lostClick;
  assert.equal((await collect(input,dependencies)).status,'processing');
  const saved=JSON.parse(await readFile(join(input.output_dir,'ffp-export-request.json'),'utf8'));
  facts.time=Date.parse(saved.requested_at)+24*60*60*1000-1;
  assert.equal((await collect(input,dependencies)).status,'processing');
  facts.time++;
  const expired=await collect(input,dependencies);
  assert.equal(expired.status,'blocked');assert.equal(expired.reason,'marker_expired');
  assert.equal(facts.clicks,1);assert.equal(facts.downloads,0);
  assert.equal((await collect(input,dependencies)).reason,'marker_expired');
  facts.pending=false;facts.lostClick=false;
  assert.equal((await collect(input,dependencies)).status,'collected');
  assert.equal(facts.clicks,1);
});

test('S18 download failure keeps all claims released and never reacquires or writes an export',async t=>{
  const {input,facts,dependencies}=await fixture(t);
  dependencies.download=async()=>{assert.equal(facts.acquires,facts.releases);throw Error('S3 unavailable');};
  const result=await collect({...input,close_tab_after:true},dependencies);
  assert.equal(result.status,'blocked');assert.match(result.message,/S3 unavailable/);
  assert.equal(facts.acquires,3);assert.equal(facts.releases,3);
});
