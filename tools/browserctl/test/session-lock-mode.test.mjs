import assert from 'node:assert/strict';
import test from 'node:test';
import {mkdtempSync,rmSync,statSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';

// Scheduled units run with UMask=0077. The broker reads the lock files through
// the shared group, so the root and child locks must stay 0660 regardless.
const lockModule=new URL('../session-lock.mjs',import.meta.url).href;
const keys=['AMAZON_BROWSER_LOCK_DIR','AMAZON_BROWSER_LOCK_TOKEN','AMAZON_BROWSER_LOCK_CHAIN'];

test('root and borrowed child locks are 0660 under a 0077 umask',async()=>{
 const dir=mkdtempSync(join(tmpdir(),'grimoire-lock-mode-'));
 const saved=Object.fromEntries(keys.map(k=>[k,process.env[k]]));
 const previousUmask=process.umask(0o077);
 let release;
 try{
  for(const k of keys)delete process.env[k];
  process.env.AMAZON_BROWSER_LOCK_DIR=dir;
  const {acquireSessionLock}=await import(lockModule);
  release=acquireSessionLock(9223,'test:root');
  const root=join(dir,'cdp-9223.lock');
  assert.equal(statSync(root).mode&0o777,0o660);
  const token=process.env.AMAZON_BROWSER_LOCK_TOKEN;
  assert.ok(token);
  const code=`import {statSync} from 'node:fs';
process.umask(0o077);
const {acquireSessionLock}=await import(${JSON.stringify(lockModule)});
const release=acquireSessionLock(9223,'test:child');
const path=${JSON.stringify(root)}+'.child-'+process.env.AMAZON_BROWSER_LOCK_TOKEN;
console.log((statSync(path).mode&0o777).toString(8));
release();`;
  const child=spawnSync(process.execPath,['--input-type=module','-e',code],
   {env:{...process.env,AMAZON_BROWSER_LOCK_DIR:dir,AMAZON_BROWSER_LOCK_TOKEN:token,AMAZON_BROWSER_LOCK_CHAIN:'[]'},encoding:'utf8'});
  assert.equal(child.status,0,child.stderr);
  assert.equal(child.stdout.trim(),'660');
 }finally{
  release?.();
  process.umask(previousUmask);
  for(const k of keys){if(saved[k]===undefined)delete process.env[k];else process.env[k]=saved[k];}
  rmSync(dir,{recursive:true,force:true});
 }
});
