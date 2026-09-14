import assert from 'node:assert/strict';
import test from 'node:test';
import {mkdtempSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {sessionEnvironment} from '../session.mjs';
import {acquireSessionLock,assertSessionLock} from '../session-lock.mjs';
const dir=mkdtempSync(join(tmpdir(),'grimoire-session-'));
const env={...process.env,AMAZON_BROWSER_LOCK_DIR:dir};
for(const k of ['CDP_PORT','CDP_PROFILE','CDP_HOST','AMAZON_BROWSER_SESSION','AMAZON_BROWSER_LOCK_TOKEN']) delete env[k];
const controller=new URL('../browserctl.mjs',import.meta.url).pathname;
const lockModule=new URL('../session-lock.mjs',import.meta.url).href;
test.after(()=>rmSync(dir,{recursive:true,force:true}));
test('Amazon defaults to grimoire; mismatched overrides fail',()=>{
 assert.equal(sessionEnvironment(undefined,{}).CDP_PORT,'9223');
 assert.equal(sessionEnvironment('operator',{}).CDP_PORT,'9222');
 for(const overrides of [{CDP_PORT:'9222'},{CDP_PROFILE:'/tmp/wrong-profile'},{AMAZON_BROWSER_SESSION:'operator'}])
  assert.throws(()=>sessionEnvironment('grimoire',overrides),/CONFLICT/);
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
