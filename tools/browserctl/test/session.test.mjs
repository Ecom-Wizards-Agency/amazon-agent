import assert from 'node:assert/strict';
import test from 'node:test';
import {mkdtempSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawn,spawnSync} from 'node:child_process';
const dir=mkdtempSync(join(tmpdir(),'grimoire-session-'));
// Fixture policies: no test reads the machine's live browser policy or profiles.
const fixturePolicy=(name,routing)=>{const path=join(dir,name);writeFileSync(path,JSON.stringify({schema_version:1,
 ...(routing?{routing:{wizards_ai_cdp_port:9223,in_app_browser_priority:'explicit-only',allow_silent_in_app_fallback:false,...routing}}:{}),
 ports:{9222:{profile:join(dir,'operator-profile')},9223:{profile:join(dir,'grimoire-profile')}}}));return path;};
process.env.AMAZON_BROWSER_RUNTIME_DIR=join(dir,'runtime');
process.env.AMAZON_BROWSER_POLICY=fixturePolicy('policy.json');
const operatorPolicyPath=fixturePolicy('policy-9222.json',{attended_cdp_port:9222});
// Bootstrap once rendered default_cdp_port 9222 while main ignored it; such a policy keeps grimoire.
const legacyPolicyPath=fixturePolicy('policy-legacy.json',{default_cdp_port:9222});
const {sessionEnvironment,sessionForPort,wizardsAiMode}=await import('../session.mjs');
const {loadBrowserPolicy}=await import('../policy.mjs');
const {acquireSessionLock,acquireSessionLockWithWait,assertSessionLock}=await import('../session-lock.mjs');
const env={...process.env,AMAZON_BROWSER_LOCK_DIR:dir};
for(const k of ['CDP_PORT','CDP_PROFILE','CDP_HOST','AMAZON_BROWSER_SESSION','AMAZON_BROWSER_LOCK_TOKEN','WIZARDS_AI_MODE']) delete env[k];
const controller=new URL('../browserctl.mjs',import.meta.url).pathname;
const lockModule=new URL('../session-lock.mjs',import.meta.url).href;
test.after(()=>rmSync(dir,{recursive:true,force:true}));
test('Amazon defaults to grimoire; mismatched overrides fail',()=>{
 assert.equal(sessionEnvironment(undefined,{}).CDP_PORT,'9223');
 assert.equal(sessionEnvironment('operator',{}).CDP_PORT,'9222');
 for(const overrides of [{CDP_PORT:'9222'},{CDP_PROFILE:'/tmp/wrong-profile'},{AMAZON_BROWSER_SESSION:'operator'}])
  assert.throws(()=>sessionEnvironment('grimoire',overrides),/CONFLICT/);
});
test('attended port is 9223 without its key, honours 9222 and rejects anything else',()=>{
 assert.equal(loadBrowserPolicy().routing.attended_cdp_port,9223);
 assert.equal(loadBrowserPolicy(operatorPolicyPath).routing.attended_cdp_port,9222);
 for(const path of [undefined,operatorPolicyPath,legacyPolicyPath]){
  assert.equal(loadBrowserPolicy(path).routing.default_cdp_port,9223);
  assert.equal(loadBrowserPolicy(path).routing.wizards_ai_cdp_port,9223);
 }
 for(const value of [9224,'operator',0])
  assert.throws(()=>loadBrowserPolicy(fixturePolicy('policy-bad.json',{attended_cdp_port:value})),/attended_cdp_port must be 9222 or 9223/);
});
test('review F4: a legacy policy with default_cdp_port 9222 still resolves to grimoire',()=>{
 const legacy=loadBrowserPolicy(legacyPolicyPath);
 assert.equal(legacy.routing.attended_cdp_port,9223);
 assert.equal(sessionEnvironment(undefined,{},legacy).AMAZON_BROWSER_SESSION,'grimoire');
 assert.equal(sessionEnvironment(undefined,{},legacy).CDP_PORT,'9223');
 // main ignored the key whatever its value; so does the branch.
 assert.equal(loadBrowserPolicy(fixturePolicy('policy-legacy-odd.json',{default_cdp_port:'operator'})).routing.attended_cdp_port,9223);
 const legacyEnv={...env,AMAZON_BROWSER_POLICY:legacyPolicyPath};
 const cli=spawnSync(process.execPath,[controller,'session'],{env:legacyEnv,encoding:'utf8'});
 assert.equal(JSON.parse(cli.stdout).AMAZON_BROWSER_SESSION,'grimoire',cli.stderr);
 const python=spawnSync('python3',['-c',`import json,sys;sys.path.insert(0,${JSON.stringify(new URL('..',import.meta.url).pathname)});import browser_session as b;print(json.dumps(b.session_environment()))`],
  {env:legacyEnv,encoding:'utf8'});
 assert.equal(JSON.parse(python.stdout).AMAZON_BROWSER_SESSION,'grimoire',python.stderr);
});
test('resolution order is --session, AMAZON_BROWSER_SESSION, CDP_PORT, then the policy default',()=>{
 const operatorDefault=loadBrowserPolicy(operatorPolicyPath),grimoireDefault=loadBrowserPolicy();
 const name=(selected,environment,policy)=>sessionEnvironment(selected,environment,policy).AMAZON_BROWSER_SESSION;
 assert.equal(name(undefined,{},operatorDefault),'operator');
 assert.equal(name(undefined,{},grimoireDefault),'grimoire');
 for(const policy of [operatorDefault,grimoireDefault]){
  assert.equal(name('grimoire',{},policy),'grimoire');assert.equal(name('operator',{},policy),'operator');
  assert.equal(name(undefined,{AMAZON_BROWSER_SESSION:'grimoire'},policy),'grimoire');
  assert.equal(name(undefined,{AMAZON_BROWSER_SESSION:'operator'},policy),'operator');
  assert.equal(name(undefined,{CDP_PORT:'9223'},policy),'grimoire');
  assert.equal(name(undefined,{CDP_PORT:'9222'},policy),'operator');
 }
 // A later source never silently overrides an earlier one; disagreement fails.
 assert.throws(()=>name('grimoire',{AMAZON_BROWSER_SESSION:'operator'},operatorDefault),/CONFLICT/);
 assert.throws(()=>name(undefined,{AMAZON_BROWSER_SESSION:'grimoire',CDP_PORT:'9222'},operatorDefault),/CONFLICT/);
 assert.equal(sessionEnvironment(undefined,{},operatorDefault).CDP_PROFILE,join(dir,'operator-profile'));
});
test('WIZARDS_AI_MODE defaults to grimoire and refuses every operator or 9222 selection',()=>{
 const operatorDefault=loadBrowserPolicy(operatorPolicyPath);
 for(const value of ['1','true','YES','on']) assert.equal(wizardsAiMode({WIZARDS_AI_MODE:value}),true);
 for(const value of [undefined,'','0','no']) assert.equal(wizardsAiMode({WIZARDS_AI_MODE:value}),false);
 const wizards={WIZARDS_AI_MODE:'1'};
 assert.equal(sessionEnvironment(undefined,wizards,operatorDefault).AMAZON_BROWSER_SESSION,'grimoire');
 assert.equal(sessionEnvironment('grimoire',{...wizards,CDP_PORT:'9223'},operatorDefault).CDP_PORT,'9223');
 for(const [selected,environment] of [['operator',{}],[undefined,{AMAZON_BROWSER_SESSION:'operator'}],[undefined,{CDP_PORT:'9222'}],['grimoire',{CDP_PORT:'9222'}]])
  assert.throws(()=>sessionEnvironment(selected,{...wizards,...environment},operatorDefault),/BROWSER_SESSION_REFUSED/);
 assert.equal(sessionForPort(9223,wizards),'grimoire');
 assert.throws(()=>sessionForPort(9222,wizards),/BROWSER_SESSION_REFUSED/);
 assert.equal(sessionForPort(9222,{}),'operator');
});
test('browserctl session and the Python adapter follow the same order and refusal',()=>{
 const operatorEnv={...env,AMAZON_BROWSER_POLICY:operatorPolicyPath};
 const cli=(args,extra={})=>spawnSync(process.execPath,[controller,'session',...args],{env:{...operatorEnv,...extra},encoding:'utf8'});
 assert.equal(JSON.parse(cli([]).stdout).AMAZON_BROWSER_SESSION,'operator');
 assert.equal(JSON.parse(cli([],{CDP_PORT:'9223'}).stdout).AMAZON_BROWSER_SESSION,'grimoire');
 assert.equal(JSON.parse(cli([],{WIZARDS_AI_MODE:'1'}).stdout).AMAZON_BROWSER_SESSION,'grimoire');
 for(const [args,extra] of [[['--session','operator'],{WIZARDS_AI_MODE:'1'}],[[],{WIZARDS_AI_MODE:'1',CDP_PORT:'9222'}]]){
  const refused=cli(args,extra);
  assert.equal(refused.status,1);assert.match(JSON.parse(refused.stdout).error,/^BROWSER_SESSION_REFUSED/);
 }
 const python=(code,extra={})=>spawnSync('python3',['-c',`import json,sys;sys.path.insert(0,${JSON.stringify(new URL('..',import.meta.url).pathname)});import browser_session as b\n${code}`],
  {env:{...operatorEnv,...extra},encoding:'utf8'});
 const resolved=(extra)=>{const r=python('print(json.dumps(b.session_environment()))',extra);assert.equal(r.status,0,r.stderr);return JSON.parse(r.stdout).AMAZON_BROWSER_SESSION;};
 assert.equal(resolved(),'operator');
 assert.equal(resolved({WIZARDS_AI_MODE:'1'}),'grimoire');
 const bound=python("b.bind_process_session();import os;print(os.environ['AMAZON_BROWSER_SESSION'])",{CDP_PORT:'9223'});
 assert.equal(bound.stdout.trim(),'grimoire',bound.stderr);
 for(const code of ["b.session_environment('operator')","b.session_environment(overrides={'CDP_PORT':'9222'})","b.bind_process_session()"]){
  const refused=python(code,{WIZARDS_AI_MODE:'1',...(code.includes('bind')?{CDP_PORT:'9222'}:{})});
  assert.notEqual(refused.status,0);assert.match(refused.stderr,/BROWSER_SESSION_REFUSED/);
 }
});
test('WIZARDS_AI_MODE refuses port 9222 however CDP_PORT spells it',()=>{
 const operatorEnv={...env,AMAZON_BROWSER_POLICY:operatorPolicyPath,WIZARDS_AI_MODE:'1'};
 const spellings=['09222',' 9222','9222.0','0x2406'];
 for(const CDP_PORT of spellings){
  assert.throws(()=>sessionEnvironment(undefined,{WIZARDS_AI_MODE:'1',CDP_PORT},loadBrowserPolicy(operatorPolicyPath)),/BROWSER_SESSION_REFUSED/);
  // Outside Grimoire a non-canonical spelling still never binds silently.
  assert.throws(()=>sessionEnvironment(undefined,{CDP_PORT},loadBrowserPolicy(operatorPolicyPath)),/BROWSER_SESSION_CONFLICT/);
  const imported=spawnSync(process.execPath,['--input-type=module','-e',`import ${JSON.stringify(new URL('../../report-fetcher/cdp.mjs',import.meta.url).href)};`],
   {env:{...operatorEnv,CDP_PORT,CDP_AUTOSTART:'0'},encoding:'utf8'});
  assert.notEqual(imported.status,0);assert.match(imported.stderr,/BROWSER_SESSION_REFUSED/);
 }
 for(const CDP_PORT of ['09222',' 9222 ']){
  const python=spawnSync('python3',['-c',`import sys;sys.path.insert(0,${JSON.stringify(new URL('..',import.meta.url).pathname)});import browser_session as b;b.bind_process_session()`],
   {env:{...operatorEnv,CDP_PORT},encoding:'utf8'});
  assert.notEqual(python.status,0);assert.match(python.stderr,/BROWSER_SESSION_REFUSED/);
  // --help would exit before any launch, so a missed refusal cannot start Chrome.
  const launcher=spawnSync('python3',[new URL('../../report-fetcher/launch-chrome-debug.py',import.meta.url).pathname,'--help'],
   {env:{...operatorEnv,CDP_PORT,AMAZON_BROWSER_LOCK_DIR:dir},encoding:'utf8'});
  assert.notEqual(launcher.status,0);assert.match(launcher.stderr,/BROWSER_SESSION_REFUSED/);
 }
 // Fixture ports that are not managed sessions stay unbound, as before.
 const fixture=spawnSync(process.execPath,['--input-type=module','-e',`import ${JSON.stringify(new URL('../../report-fetcher/cdp.mjs',import.meta.url).href)};console.log(process.env.CDP_PORT+' '+(process.env.AMAZON_BROWSER_SESSION||'none'))`],
  {env:{...operatorEnv,CDP_PORT:'19222',CDP_AUTOSTART:'0'},encoding:'utf8'});
 assert.equal(fixture.stdout.trim(),'19222 none',fixture.stderr);
});
test('launcher grandchildren inherit the session before CDP import',()=>{
 const inner=`import ${JSON.stringify(new URL('../../report-fetcher/cdp.mjs',import.meta.url).href)};
 console.log(JSON.stringify({session:process.env.AMAZON_BROWSER_SESSION,port:process.env.CDP_PORT,locked:Boolean(process.env.AMAZON_BROWSER_LOCK_TOKEN)}));`;
 const script=`import {spawnSync} from 'node:child_process';
 const r=spawnSync(process.execPath,['--input-type=module','-e',${JSON.stringify(inner)}],{encoding:'utf8'});
 process.stdout.write(r.stdout);process.stderr.write(r.stderr);process.exitCode=r.status;`;
 const r=spawnSync(process.execPath,[controller,'run','--session','grimoire','--',process.execPath,'--input-type=module','-e',script],{env,encoding:'utf8'});
 assert.equal(r.status,0,r.stdout+r.stderr);
 assert.deepEqual(JSON.parse(r.stdout),{session:'grimoire',port:'9223',locked:true});
});
test('independent workers cannot take the lock; children can inherit',()=>{
 const old=process.env.AMAZON_BROWSER_LOCK_DIR;
 process.env.AMAZON_BROWSER_LOCK_DIR=dir;
 const unlock=acquireSessionLock(9223,'test-parent');
 try {
  const code=`import {acquireSessionLock,assertSessionLock} from ${JSON.stringify(lockModule)};
  const release=acquireSessionLock(9223);assertSessionLock(9223);release();`;
  const blocked=spawnSync(process.execPath,['--input-type=module','-e',code],{env,encoding:'utf8'});
  assert.notEqual(blocked.status,0);assert.match(blocked.stderr,/BROWSER_SESSION_BUSY/);
  const restart=spawnSync(process.execPath,[controller,'restart','--port','9223','--mode','headed','--reason','busy regression'],{env,encoding:'utf8'});
  assert.notEqual(restart.status,0);assert.match(restart.stdout+restart.stderr,/BROWSER_SESSION_BUSY/);
  const child=spawnSync(process.execPath,['--input-type=module','-e',code],{env:{...env,AMAZON_BROWSER_LOCK_TOKEN:process.env.AMAZON_BROWSER_LOCK_TOKEN},encoding:'utf8'});
  assert.equal(child.status,0,child.stderr);assertSessionLock(9223);
 }finally{unlock();if(old)process.env.AMAZON_BROWSER_LOCK_DIR=old;else delete process.env.AMAZON_BROWSER_LOCK_DIR;}
});

test('lock waiting uses two-second retries and preserves the release function',async()=>{
 let now=1000,attempts=0;
 const sleeps=[],release=()=>{};
 const result=await acquireSessionLockWithWait(9223,'wait-test',{}, {
  acquire:(port,owner)=>{
   assert.equal(port,9223);assert.equal(owner,'wait-test');
   if(++attempts<3)throw new Error('BROWSER_SESSION_BUSY: fixture');
   return release;
  },
  clock:()=>now,sleep:async ms=>{sleeps.push(ms);now+=ms;},
 });
 assert.equal(result,release);assert.equal(attempts,3);assert.deepEqual(sleeps,[2000,2000]);
});

test('lock waiting stops at the deadline, including zero wait and delayed timers',async()=>{
 for(const [lockWaitMs,delay,expectedSleeps,expectedWait] of [[4500,0,[2000,2000,500],4500],[0,0,[],0],[1000,500,[1000],1500]]){
  let now=0,attempts=0;
  const sleeps=[],busy=new Error('BROWSER_SESSION_BUSY: fixture');
  await assert.rejects(acquireSessionLockWithWait(9223,'deadline',{lockWaitMs},{
   acquire:()=>{attempts++;throw busy;},clock:()=>now,
   sleep:async ms=>{sleeps.push(ms);now+=ms+delay;},
  }),error=>{
   assert.equal(error,busy);assert.equal(error.waitMs,expectedWait);
   assert.equal(error.message,`BROWSER_SESSION_BUSY: fixture; waited ${expectedWait} ms`);return true;
  });
  assert.deepEqual(sleeps,expectedSleeps);assert.equal(attempts,Math.max(1,expectedSleeps.length));
 }
});

test('default lock deadline is 120 seconds and other errors fail immediately',async()=>{
 let now=0,attempts=0;
 await assert.rejects(acquireSessionLockWithWait(9223,'default',{}, {
  acquire:()=>{attempts++;throw new Error('BROWSER_SESSION_BUSY: fixture');},
  clock:()=>now,sleep:async ms=>{now+=ms;},
 }),/waited 120000 ms/);
 assert.equal(now,120000);assert.equal(attempts,60);
 const failure=new Error('BROWSER_SESSION_LOCK_LOST: fixture');
 await assert.rejects(acquireSessionLockWithWait(9223,'failure',{}, {
  acquire:()=>{throw failure;},sleep:async()=>assert.fail('must not sleep'),
 }),error=>error===failure);
 for(const lockWaitMs of [-1,1.5,NaN,Infinity])
  await assert.rejects(acquireSessionLockWithWait(9223,'invalid',{lockWaitMs}),/INVALID_LOCK_WAIT_MS/);
 await assert.rejects(acquireSessionLockWithWait(9223,'invalid',{retryIntervalMs:0}),/INVALID_LOCK_RETRY_INTERVAL_MS/);
});

test('run waits for a real independent lock and launches the child after release',async()=>{
 const old=process.env.AMAZON_BROWSER_LOCK_DIR;process.env.AMAZON_BROWSER_LOCK_DIR=dir;
 const unlock=acquireSessionLock(9223,'run-blocker');
 let child,timer;
 try{
  child=spawn(process.execPath,[controller,'run','--session','grimoire','--',process.execPath,'--input-type=module','-e',
   `import {acquireSessionLock,assertSessionLock} from ${JSON.stringify(lockModule)}; const release=acquireSessionLock(9223);assertSessionLock(9223);release();console.log('child-owned');`],{env});
  let stdout='',stderr='';
  child.stdout.on('data',data=>{stdout+=data;});child.stderr.on('data',data=>{stderr+=data;});
  const finished=new Promise((resolve,reject)=>{child.once('error',reject);child.once('exit',code=>resolve(code));});
  timer=setTimeout(unlock,500);
  assert.equal(await finished,0,stdout+stderr);assert.equal(stdout.trim(),'child-owned');
  const release=acquireSessionLock(9223,'after-run');release();
 }finally{clearTimeout(timer);child?.kill();unlock();if(old)process.env.AMAZON_BROWSER_LOCK_DIR=old;else delete process.env.AMAZON_BROWSER_LOCK_DIR;}
});

test('run rejects expired waits without launching and validates lock-wait-ms',()=>{
 const old=process.env.AMAZON_BROWSER_LOCK_DIR;process.env.AMAZON_BROWSER_LOCK_DIR=dir;
 const unlock=acquireSessionLock(9223,'run-deadline');
 try{
  for(const value of ['0','80']){
   const r=spawnSync(process.execPath,[controller,'run','--session','grimoire','--lock-wait-ms',value,'--',process.execPath,'-e',"console.log('must-not-launch')"],{env,encoding:'utf8',timeout:5000});
   assert.equal(r.status,1,r.stdout+r.stderr);assert.doesNotMatch(r.stdout,/must-not-launch/);
   const result=JSON.parse(r.stdout);assert.equal(result.ok,false);
   assert.match(result.error,/^BROWSER_SESSION_BUSY:.*waited \d+ ms$/);
   assert.ok(Number(result.error.match(/waited (\d+) ms/)[1])>=Number(value));
  }
 }finally{unlock();if(old)process.env.AMAZON_BROWSER_LOCK_DIR=old;else delete process.env.AMAZON_BROWSER_LOCK_DIR;}
 for(const value of ['-1','bad','1.5',null]){
  const r=spawnSync(process.execPath,[controller,'run','--lock-wait-ms',...(value===null?[]:[value]),'--',process.execPath,'-e',''],{env,encoding:'utf8'});
  assert.equal(r.status,1);assert.match(r.stdout,/INVALID_LOCK_WAIT_MS/);
 }
});

test('sibling Python workers cannot borrow the same parent workflow concurrently', async()=>{
 const {spawn}=await import('node:child_process');
 const old=process.env.AMAZON_BROWSER_LOCK_DIR;process.env.AMAZON_BROWSER_LOCK_DIR=dir;
 const unlock=acquireSessionLock(9223,'parent');
 const childEnv={...env,AMAZON_BROWSER_LOCK_TOKEN:process.env.AMAZON_BROWSER_LOCK_TOKEN,AMAZON_BROWSER_LOCK_CHAIN:'[]'};
 const code=`import sys,time; sys.path.insert(0,${JSON.stringify(new URL('../../../../wizards-ai',import.meta.url).pathname)}); from read_browser_lock import read_browser_lock\nwith read_browser_lock('sibling'):\n print('owned',flush=True); time.sleep(0.5)`;
 const child=spawn('python3',['-c',code],{env:childEnv,stdio:['ignore','pipe','pipe']});
 try{
  await new Promise((resolve,reject)=>{child.stdout.once('data',resolve);child.once('error',reject);child.once('exit',code=>{if(code)reject(new Error('first worker failed'));});});
  const sibling=spawnSync('python3',['-c',code],{env:childEnv,encoding:'utf8'});
  assert.notEqual(sibling.status,0);assert.match(sibling.stderr,/busy/);
  await new Promise(resolve=>child.once('exit',resolve));
 }finally{child.kill();unlock();if(old)process.env.AMAZON_BROWSER_LOCK_DIR=old;else delete process.env.AMAZON_BROWSER_LOCK_DIR;}
});

test('command results are discarded when the session lock disappears',async()=>{
 const {Session}=await import('../../report-fetcher/cdp.mjs');
 const {unlinkSync}=await import('node:fs');
 const old=process.env.AMAZON_BROWSER_LOCK_DIR;process.env.AMAZON_BROWSER_LOCK_DIR=dir;
 const unlock=acquireSessionLock(9223,'lost-lock');
 let s;
 const ws={send(raw){const {id}=JSON.parse(raw);unlinkSync(join(dir,'cdp-9223.lock'));queueMicrotask(()=>s.pending.get(id).resolve({accepted:true}));},close(){}};
 s=new Session(ws);s._unlockSession=unlock;
 try{await assert.rejects(s.send('Runtime.evaluate'),/LOCK_LOST/);}
 finally{s.close();unlock();if(old)process.env.AMAZON_BROWSER_LOCK_DIR=old;else delete process.env.AMAZON_BROWSER_LOCK_DIR;}
});
