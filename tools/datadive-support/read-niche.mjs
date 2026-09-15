#!/usr/bin/env node
// Read-only full-pool extraction and owned-tab evidence. MCP remains first for
// Core keywords, roots and competitors; this supplies the browser-only tail.
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {acquireTaskPage,releaseTaskPage,taskIdFor} from '../browserctl/task-tabs.mjs';
import {evaluate} from '../report-fetcher/cdp.mjs';
import {captureTaskEvidence} from '../browserctl/task-evidence.mjs';

export async function readNiche({nicheId,marketplace,heroKeyword,taskId,outDir}) {
 if(!/^[A-Za-z0-9_-]+$/.test(nicheId||'')||!marketplace||!heroKeyword||!outDir)throw new Error('DATADIVE_INPUT_REQUIRED: nicheId, marketplace, heroKeyword, outDir');
 const handle=await acquireTaskPage({taskId:taskId||taskIdFor('datadive',`${nicheId}|${outDir}`),workflow:'amazon-seo',initialUrl:`https://2.datadive.tools/niche/${nicheId}/niche-analysis/mkl`});
 let outcome='error';
 let packs,shot;
 try{
  const deadline=Date.now()+60000;
  let loaded=false;
  while(Date.now()<deadline){
   const facts=await evaluate(handle.session,`({login:!!document.querySelector('input[type="password"]')||/\\/(?:signin|sign-in|login)(?:\\/|$)/.test(location.pathname),text:document.body.innerText})`);
   if(facts.login)throw new Error('DATADIVE_LOGIN_REQUIRED: sign into the selected persistent browser');
   // Read actual keyword rows, not the selected-niche heading or loading shell.
   loaded=facts.text.toLowerCase().includes(heroKeyword.toLowerCase())&&/Search Terms\s+\d+/.test(facts.text)&&/Relev\./.test(facts.text);
   if(loaded)break;
   await new Promise(r=>setTimeout(r,500));
  }
  if(!loaded)throw new Error('DATADIVE_OPTIONS_TIMEOUT: keyword grid did not become readable');
  packs={};
  for(const [name,endpoint] of [['mkl',`mkl/${nicheId}?includeAsinCatalog=true`],['outlier',`outlier/${nicheId}`],['residue',`residue-kw-list/${nicheId}`]]){
   const result=await evaluate(handle.session,`(async()=>{const r=await fetch(${JSON.stringify('https://app.datadive.tools/'+endpoint)},{credentials:'include'});if(!r.ok)throw new Error('DATADIVE_READ_FAILED: '+r.status);return await r.json()})()`,45000);
   if(result.success!==true||!Array.isArray(result.data?.keywords))throw new Error('DATADIVE_READ_INVALID: '+name);
   if((result.data.nicheId&&result.data.nicheId!==nicheId)||(result.data.marketplace&&result.data.marketplace!==marketplace))throw new Error('DATADIVE_IDENTITY_MISMATCH');
   packs[name]=result;
  }
  if(packs.mkl.data.nicheId!==nicheId||packs.mkl.data.marketplace!==marketplace)throw new Error('DATADIVE_IDENTITY_MISMATCH');
  shot=await captureTaskEvidence(handle,{expected:{kind:'datadive',nicheId,heroKeyword}});
  shot.evidence.verified_identity.marketplace=packs.mkl.data.marketplace;
  shot.evidence.verified_identity.backendNicheId=packs.mkl.data.nicheId;
  outcome='handoff';
 }finally{await releaseTaskPage(handle,{outcome});}
 await fs.mkdir(outDir,{recursive:true});
 const artifacts=[];
 for(const [name,value] of Object.entries({...packs,'evidence':shot.evidence})){
  const bytes=Buffer.from(JSON.stringify(value,null,2)+'\n'),destination=path.join(outDir,`${name}.json`);
  await fs.writeFile(destination,bytes);artifacts.push({path:destination,sha256:createHash('sha256').update(bytes).digest('hex'),bytes:bytes.length});
 }
 const screenshot=path.join(outDir,'datadive.png');await fs.writeFile(screenshot,shot.data);
 artifacts.push({path:screenshot,sha256:createHash('sha256').update(shot.data).digest('hex'),bytes:shot.data.length});
 const result={session:handle.port===9223?'grimoire':'operator',port:handle.port,task_id:handle.taskId,target_id:handle.targetId,niche_id:nicheId,marketplace,
  counts:Object.fromEntries(Object.entries(packs).map(([k,v])=>[k,v.data.keywords.length])),artifacts};
 await fs.writeFile(path.join(outDir,'receipt.json'),JSON.stringify(result,null,2)+'\n');
 return result;
}
if(process.argv[1]===fileURLToPath(import.meta.url)){
 const [nicheId,marketplace,heroKeyword,outDir,taskId]=process.argv.slice(2);
 console.log(JSON.stringify(await readNiche({nicheId,marketplace,heroKeyword,outDir,taskId})));
}
