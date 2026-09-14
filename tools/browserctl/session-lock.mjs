// Shared wire contract with read_browser_lock.py. Each child process claims the
// next link: siblings serialize, while a workflow can call nested helpers.
import {mkdirSync,openSync,closeSync,readFileSync,writeFileSync,unlinkSync} from 'node:fs';
import {dirname,resolve} from 'node:path';
import {homedir} from 'node:os';
import {randomUUID} from 'node:crypto';
const locks=new Map();
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
function release(root,state){if(locks.get(root)!==state||--state.users>0)return;
 if(read(state.path).token===state.token)unlinkSync(state.path);locks.delete(root);
 for(const [key,value] of [['AMAZON_BROWSER_LOCK_TOKEN',state.previous],['AMAZON_BROWSER_LOCK_CHAIN',state.previousChain]]){if(value)process.env[key]=value;else delete process.env[key];}}
process.once('exit',()=>{for(const [root,state] of locks){state.users=1;release(root,state);}});
