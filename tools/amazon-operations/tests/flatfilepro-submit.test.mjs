import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,readFile,rm} from 'node:fs/promises';
import {join} from 'node:path';
import {tmpdir} from 'node:os';
import {submitAttended,submittedRunIdentity} from '../flatfilepro-submit.mjs';

const attempt={identity_kind:'uploaded_file',upload_key:'SELLER-MARKET/1077-ffp-a.xlsx',submission_intent:true};
function fake(body={runId:'run-123'}) {
  const handlers={};
  return {subscribe:(name,fn)=>{handlers[name]=fn;},send:async name=>name==='Network.getResponseBody'?{body:JSON.stringify(body)}:{},
    emit:(path='/api/v2/imports/excel/1077/update',type='XHR')=>{handlers['Network.responseReceived']({requestId:type==='Preflight'?'preflight':'response1',type,response:{url:'https://api.flatfile.pro'+path,status:type==='Preflight'?204:200}});handlers['Network.loadingFinished']({requestId:type==='Preflight'?'preflight':'response1'});}};
}
test('CORS preflight is not mistaken for the submission response',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'ffp-submit-')),path=join(dir,'attempt.json'),session=fake();
  try{const result=await submitAttended({session,attemptPath:path,attempt,click:async()=>{session.emit(undefined,'Preflight');session.emit();}});assert.equal(result.submission_id,'run-123');}
  finally{await rm(dir,{recursive:true,force:true});}
});
test('exact update response persists runId after durable pre-click intent and never replays',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'ffp-submit-')),path=join(dir,'attempt.json'),session=fake();let clicks=0;
  const click=async()=>{clicks++;assert.equal(JSON.parse(await readFile(path)).submission_intent,true);session.emit();};
  try {
    const result=await submitAttended({session,click,attemptPath:path,attempt});
    assert.equal(result.submission_id,'run-123');
    assert.equal(JSON.parse(await readFile(path)).submission_url,'https://app.flatfile.pro/activity/import/run-123');
    await assert.rejects(submitAttended({session,click,attemptPath:path,attempt}),/EEXIST/);
    assert.equal(clicks,1);
  }finally{await rm(dir,{recursive:true,force:true});}
});
test('missing, wrong-config, malformed and duplicate responses preserve uncertain intent',async()=>{
  for(const mode of ['missing','wrong','malformed','duplicate','lost-click']) {
    const dir=await mkdtemp(join(tmpdir(),'ffp-submit-')),path=join(dir,'attempt.json'),session=fake(mode==='malformed'?{}:undefined);
    try{
      await assert.rejects(submitAttended({session,attemptPath:path,attempt,timeoutMs:1,click:async()=>{
        if(mode==='lost-click')throw Error('connection lost');
        if(mode==='missing')return;
        session.emit(mode==='wrong'?'/api/v2/imports/excel/9999/update':undefined);
        if(mode==='duplicate')session.emit();
      }}));
      const receipt=JSON.parse(await readFile(path));
      assert.equal(receipt.submission_intent,true);assert.equal(receipt.submission_id,undefined);
    }finally{await rm(dir,{recursive:true,force:true});}
  }
});
test('runId cannot inject an origin, path or query',()=>{
  for(const runId of [undefined,'','https://other.example','../99','123?other=x',{},true])
    assert.throws(()=>submittedRunIdentity({runId}));
});
