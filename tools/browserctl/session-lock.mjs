// Shared wire contract with read_browser_lock.py. Each child process claims the
// next link: siblings serialize, while a workflow can call nested helpers.
import {mkdirSync,openSync,closeSync,readFileSync,writeFileSync,unlinkSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {homedir} from 'node:os';
import {randomUUID} from 'node:crypto';
const locks=new Map();
let launcherRelease;
const alive=pid=>{if(!Number.isInteger(Number(pid))||Number(pid)<=0)return false;try{process.kill(Number(pid),0);return true;}catch(e){return e.code==='EPERM';}};
const read=p=>{try{return JSON.parse(readFileSync(p,'utf8'));}catch{return {};}};
const rootPath=port=>resolve(process.env.AMAZON_BROWSER_LOCK_DIR||`${homedir()}/.amazon-agent/locks`,`cdp-${port}.lock`);
function chain(){const value=JSON.parse(process.env.AMAZON_BROWSER_LOCK_CHAIN||'[]');
 if(!Array.isArray(value)||value.length>32||value.some(t=>typeof t!=='string'||!/^[a-f0-9-]{16,64}$/.test(t)))throw new Error('BROWSER_SESSION_LOCK_LOST: invalid delegation');return value;}
function validate(root){let record=read(root),token=process.env.AMAZON_BROWSER_LOCK_TOKEN;
 if(!token||record.token!==token||!alive(record.pid))throw new Error('BROWSER_SESSION_LOCK_LOST: reacquire the workflow');
 for(const next of chain()){record=read(`${root}.child-${token}`);if(record.token!==next||!alive(record.pid))throw new Error('BROWSER_SESSION_LOCK_LOST: child control lost');token=next;}
 return token;}
export function assertSessionLock(port){if(Number(port)===9223)validate(rootPath(port));}
export function acquireSessionLock(port=9223,owner=`node:${process.pid}`){
 if(Number(port)!==9223)return ()=>{};
 if(launcherRelease)throw new Error('BROWSER_SESSION_BUSY: launcher release pending');
 const root=rootPath(port),local=locks.get(root);
 if(local){validate(root);local.users++;return ()=>release(root,local);}
 const previous=process.env.AMAZON_BROWSER_LOCK_TOKEN,previousChain=process.env.AMAZON_BROWSER_LOCK_CHAIN;
 let path=root,borrowed=false;
 if(previous&&read(root).token===previous&&read(root).pid!==process.pid){path=`${root}.child-${validate(root)}`;borrowed=true;}
 mkdirSync(dirname(path),{recursive:true,mode:0o700});
 let fd;try{fd=openSync(path,'wx',0o660);}catch(e){if(e.code!=='EEXIST')throw e;throw new Error('BROWSER_SESSION_BUSY: grimoire is in use; retry after its current task finishes');}
 const token=randomUUID();try{writeFileSync(fd,JSON.stringify({pid:process.pid,owner,token,created_at:Date.now()/1000}));}finally{closeSync(fd);}
 const state={path,token,users:1,previous,previousChain};locks.set(root,state);
 if(borrowed)process.env.AMAZON_BROWSER_LOCK_CHAIN=JSON.stringify([...chain(),token]);
 else {process.env.AMAZON_BROWSER_LOCK_TOKEN=token;delete process.env.AMAZON_BROWSER_LOCK_CHAIN;}
 return ()=>release(root,state);
}
export async function acquireSessionLockWithWait(port=9223,owner=`node:${process.pid}`,{
 lockWaitMs=120_000,retryIntervalMs=2000,
}={}, {acquire=acquireSessionLock,clock=Date.now,sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms))}={}){
 if(!Number.isSafeInteger(lockWaitMs)||lockWaitMs<0)throw new Error('INVALID_LOCK_WAIT_MS');
 if(!Number.isSafeInteger(retryIntervalMs)||retryIntervalMs<=0)throw new Error('INVALID_LOCK_RETRY_INTERVAL_MS');
 if(launcherRelease)await launcherRelease;
 const startedAt=clock(),deadline=startedAt+lockWaitMs;
 let busy;
 while(true){
  if(busy&&clock()>=deadline){
   busy.waitMs=clock()-startedAt;
   busy.message+=`; waited ${busy.waitMs} ms`;
   throw busy;
  }
  try{return acquire(port,owner);}catch(error){
   if(!String(error.message).startsWith('BROWSER_SESSION_BUSY'))throw error;
   busy=error;
  }
  const remaining=deadline-clock();
  if(remaining>0)await sleep(Math.min(retryIntervalMs,remaining));
 }
}
// Only a direct browserctl child with the launcher's live delegation may signal
// it. Observing removal of that delegation acknowledges release before reuse.
export async function releaseLauncherSessionLock(port=9223){
 if(launcherRelease)return launcherRelease;
 if(Number(port)!==9223||locks.has(rootPath(port))||
   process.env.AMAZON_BROWSER_LAUNCHER_CONTROL!=='sigusr1-v1'||Number(process.env.AMAZON_BROWSER_LAUNCHER_PID)!==process.ppid)return;
 const root=rootPath(port),tokens=[process.env.AMAZON_BROWSER_LOCK_TOKEN,...chain()];
 const token=validate(root),path=tokens.length===1?root:`${root}.child-${tokens.at(-2)}`;
 const parent=read(path);
 if(parent.pid!==process.ppid||parent.owner!=='browserctl:run')throw new Error('BROWSER_SESSION_LOCK_LOST: parent is not the launcher lock owner');
 launcherRelease=(async()=>{
  process.kill(process.ppid,'SIGUSR1');
  const deadline=Date.now()+10000;
  while(read(path).token===token){
   if(Date.now()>=deadline)throw new Error('BROWSER_SESSION_LOCK_LOST: launcher release timed out');
   await new Promise(resolve=>setTimeout(resolve,10));
  }
  for(const key of ['AMAZON_BROWSER_LOCK_TOKEN','AMAZON_BROWSER_LOCK_CHAIN','AMAZON_BROWSER_LAUNCHER_CONTROL','AMAZON_BROWSER_LAUNCHER_PID'])delete process.env[key];
 })();
 try{await launcherRelease;}finally{launcherRelease=undefined;}
}

export function sessionLockHasChildren(port=9223){
 const local=locks.get(rootPath(port));
 return Boolean(local&&read(`${rootPath(port)}.child-${local.token}`).token);
}
function release(root,state){if(locks.get(root)!==state||--state.users>0)return;
 if(read(state.path).token===state.token)unlinkSync(state.path);locks.delete(root);
 for(const [key,value] of [['AMAZON_BROWSER_LOCK_TOKEN',state.previous],['AMAZON_BROWSER_LOCK_CHAIN',state.previousChain]]){if(value)process.env[key]=value;else delete process.env[key];}}
process.once('exit',()=>{for(const [root,state] of locks){state.users=1;release(root,state);}});
