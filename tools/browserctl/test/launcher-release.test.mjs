import assert from 'node:assert/strict';
import test from 'node:test';
import { spawn } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync, existsSync, readFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const launcher=new URL('../browserctl.mjs',import.meta.url).pathname;
const preload=new URL('./fixtures/launcher-cdp.mjs',import.meta.url).pathname;
const tasks=new URL('../task-tabs.mjs',import.meta.url).href;
const locks=new URL('../session-lock.mjs',import.meta.url).href;

function start(t,command,args,env){
  const child=spawn(command,args,{env,stdio:['pipe','pipe','pipe']});
  let stderr='';child.stderr.on('data',data=>{stderr+=data;});
  child.stdout.resume();
  const done=new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',code=>resolve({code,stderr}));});
  t.after(()=>child.kill());
  return {child,done};
}

async function ready(path){
  const deadline=Date.now()+5000;
  while(!existsSync(path)){assert.ok(Date.now()<deadline,`missing checkpoint ${path}`);await new Promise(r=>setTimeout(r,10));}
  return readFileSync(path,'utf8');
}

for(const ending of ['release','detach','close'])test(`launcher releases after last ${ending}, child reacquires with BUSY and wait semantics`,{timeout:30000},async t=>{
  const directory=mkdtempSync(join(tmpdir(),'launcher-release-'));
  t.after(()=>rmSync(directory,{recursive:true,force:true}));
  const env={...process.env,AMAZON_BROWSER_LOCK_DIR:join(directory,'locks'),AMAZON_BROWSER_RUNTIME_DIR:directory,
    AMAZON_BROWSER_POLICY:join(directory,'policy.json'),CDP_ENABLE_TEST_LEASES:'1'};
  for(const key of ['CDP_PORT','CDP_PROFILE','CDP_HOST','AMAZON_BROWSER_SESSION','AMAZON_BROWSER_LOCK_TOKEN','AMAZON_BROWSER_LOCK_CHAIN','AMAZON_BROWSER_CONTROL_FD','AMAZON_BROWSER_LAUNCHER_PID','AMAZON_BROWSER_LAUNCHER_CONTROL','AMAZON_BROWSER_LOCK_WAIT_MS','NODE_TEST_CONTEXT'])delete env[key];
  const script=`import assert from 'node:assert/strict';
    import {existsSync,writeFileSync} from 'node:fs';
    import {acquireTaskPage,releaseTaskPage,detachTaskPage,closeReleasedTaskPage} from ${JSON.stringify(tasks)};
    const step=async label=>{writeFileSync(${JSON.stringify(directory)}+'/'+label+'.ready','');while(!existsSync(${JSON.stringify(directory)}+'/'+label))await new Promise(r=>setTimeout(r,10));};
    const spec={taskId:'launcher:first',workflow:'fixture'};
    const lockPath=process.env.AMAZON_BROWSER_LOCK_DIR+'/cdp-9223.lock';
    const kill=process.kill.bind(process);let signals=0;
    const first=await acquireTaskPage(spec),second=await acquireTaskPage({...spec,taskId:'launcher:second'});
    process.kill=(pid,signal)=>{if(signal==='SIGUSR1'){assert.equal(first._released,true);assert.equal(second._released,true);signals++;}return kill(pid,signal);};
    await releaseTaskPage(first);assert.equal(signals,0);kill(process.ppid,'SIGUSR1');await step('one-held');
    if(${JSON.stringify(ending)}==='detach')await detachTaskPage(second);
    else await releaseTaskPage(second,{closeTarget:${ending==='close'}});
    assert.equal(process.env.AMAZON_BROWSER_LOCK_TOKEN,undefined);
    assert.equal(signals,1);assert.equal(existsSync(lockPath),false,'lock absent while the child processes local output');
    await step('released');
    await assert.rejects(acquireTaskPage({...spec,lockWaitMs:0}),/BROWSER_SESSION_BUSY/);
    const started=Date.now();
    await assert.rejects(acquireTaskPage(spec),error=>{assert.match(error.message,/BROWSER_SESSION_BUSY/);assert.ok(error.waitMs>=2500);return true;});
    assert.ok(Date.now()-started>=2500,'child uses launcher --lock-wait-ms');await step('busy');
    writeFileSync(${JSON.stringify(directory)}+'/waiting.ready','');
    const again=await acquireTaskPage(spec);await step('reacquired');
    await releaseTaskPage(again);
    if(${JSON.stringify(ending)}==='close')assert.equal(await closeReleasedTaskPage(again),true);
    assert.equal(existsSync(lockPath),false,'lock absent during final local processing');
    assert.equal(signals,1,'a reacquired child owns and releases its own lock');
    await step('output');writeFileSync(${JSON.stringify(directory)}+'/done.ready','');`;
  const run=start(t,'node',[launcher,'run','--lock-wait-ms','2500','--','node','--import',preload,'--input-type=module','-e',script],env);
  await ready(join(directory,'one-held.ready'));
  const claim=`import {existsSync,writeFileSync} from 'node:fs';import {acquireSessionLock} from ${JSON.stringify(locks)};let release;try{release=acquireSessionLock(9223);writeFileSync(process.env.RELEASE_FILE+'.ready','owned');}catch(e){writeFileSync(process.env.RELEASE_FILE+'.ready',e.message);process.exit(2);}while(!existsSync(process.env.RELEASE_FILE))await new Promise(r=>setTimeout(r,10));release();`;
  const claimant=name=>start(t,'node',['--input-type=module','-e',claim],{...env,RELEASE_FILE:join(directory,name)});
  const blocked=claimant('blocked');
  assert.match(await ready(join(directory,'blocked.ready')),/^BROWSER_SESSION_BUSY/);assert.equal((await blocked.done).code,2);
  writeFileSync(join(directory,'one-held'),'');await ready(join(directory,'released.ready'));
  assert.equal(run.child.exitCode,null,'launcher child is still running');
  assert.equal(existsSync(join(directory,'locks','cdp-9223.lock')),false,'parent observes no lock during child local processing');
  const independent=claimant('independent');
  assert.equal(await ready(join(directory,'independent.ready')),'owned');
  writeFileSync(join(directory,'released'),'');await ready(join(directory,'busy.ready'));
  writeFileSync(join(directory,'busy'),'');
  await ready(join(directory,'waiting.ready'));
  await new Promise(r=>setTimeout(r,50));
  assert.equal(existsSync(join(directory,'reacquired.ready')),false,'reacquisition waits for the independent claimant');
  writeFileSync(join(directory,'independent'),'');assert.equal((await independent.done).code,0);
  await ready(join(directory,'reacquired.ready'));
  const blockedAgain=claimant('blocked-again');
  assert.match(await ready(join(directory,'blocked-again.ready')),/^BROWSER_SESSION_BUSY/);await blockedAgain.done;
  writeFileSync(join(directory,'reacquired'),'');await ready(join(directory,'output.ready'));
  assert.equal(existsSync(join(directory,'locks','cdp-9223.lock')),false);
  const after=claimant('after');
  assert.equal(await ready(join(directory,'after.ready')),'owned');
  const held=readFileSync(join(directory,'locks','cdp-9223.lock'),'utf8');
  writeFileSync(join(directory,'output'),'');await ready(join(directory,'done.ready'));
  assert.deepEqual(await run.done,{code:0,stderr:''});
  assert.equal(readFileSync(join(directory,'locks','cdp-9223.lock'),'utf8'),held,'launcher exit must preserve the new owner');
  writeFileSync(join(directory,'after'),'');assert.equal((await after.done).code,0);
});
