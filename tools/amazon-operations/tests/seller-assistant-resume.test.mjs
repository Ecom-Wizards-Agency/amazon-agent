import test from 'node:test';
import assert from 'node:assert/strict';
import {restoreCaseChat, readCaseChatResume} from '../seller-assistant.mjs';
const origin='https://sellercentral.amazon.com';
const saved={caseId:'23137591191',targetId:'chat-1',openerId:'opener-1'};
function fixture(change={}){
 const calls=[];
 const target={type:'page',targetId:'chat-1',openerId:'opener-1',url:origin+'/hill/website/chat?formType=reply&caseID=23137591191',...change};
 const handle={session:{send:async()=>{}},targetId:'chat-1'};
 const B={tabs:{acquireTaskPage:async spec=>{calls.push(spec);return handle},releaseTaskPage:async(h,o)=>{calls.push(o);assert.equal(h,handle)}},cdp:{listPages:async()=>[]}};
 const page={targetId:'opener-1',taskId:'run-task',session:{send:async(method,args)=>{assert.equal(method,'Target.getTargetInfo');assert.deepEqual(args,{targetId:'chat-1'});return{targetInfo:target}}}};
 const rt={config:{registry_id:'registered'},origin,counts:new Map([['already-sent',1]]),browser:{},caseId:null,chat:null};
 return{B,page,rt,calls};
}
test('resume uses only the existing exact chat slot without navigation or replay',async()=>{
 const f=fixture();await restoreCaseChat(f.rt,{B:f.B,page:f.page,policy:{},saved});
 assert.equal(f.calls.length,1);assert.equal(f.calls[0].expectedTargetId,'chat-1');assert.equal(f.calls[0].allowOperatorActivity,true);assert.equal(f.calls[0].exclusiveContext,false);assert.equal(f.calls[0].slot,'case-chat');
 assert.equal(f.rt.caseId,saved.caseId);assert.equal(f.rt.chat.targetId,'chat-1');assert.equal(f.rt.browser,f.rt.chat.browser);assert.equal(f.rt.counts.get('already-sent'),1);
 await f.rt.chat.release('handoff');assert.deepEqual(f.calls[1],{outcome:'handoff'});
});
test('resume refuses changed chat identity before acquiring any target',async()=>{
 for(const change of [{targetId:'other'},{openerId:'other'},{url:origin+'/hill/website/chat?formType=reply&caseID=111'},{url:'https://example.com/hill/website/chat?formType=reply&caseID=23137591191'}]){
  const f=fixture(change);await assert.rejects(restoreCaseChat(f.rt,{B:f.B,page:f.page,policy:{},saved}));assert.equal(f.calls.length,0);
 }
 const f=fixture();f.page.targetId='other';await assert.rejects(restoreCaseChat(f.rt,{B:f.B,page:f.page,policy:{},saved}),e=>e.code==='chat_resume_opener_mismatch');assert.equal(f.calls.length,0);
});
test('resume proof rejects unsafe result paths before reading them',async()=>{
 await assert.rejects(readCaseChatResume('/unused',{resultId:'../004',openerId:'opener-1'}),e=>e.code==='chat_resume_invalid');
});
