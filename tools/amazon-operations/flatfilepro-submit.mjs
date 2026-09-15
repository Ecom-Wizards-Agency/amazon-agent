/** Attended first-canary response capture. No request/header/auth inspection. */
import { durableReceipt, reserveSubmission } from './flatfilepro-contracts.mjs';
import { check } from './browser-ui.mjs';

export function submittedRunIdentity(data) {
  check(typeof data?.runId==='string'||(Number.isSafeInteger(data?.runId)&&data.runId>0),'Missing or malformed FlatFilePro submission runId');
  const id=String(data?.runId??'');
  check(/^[A-Za-z0-9-]{1,100}$/.test(id),'Missing or malformed FlatFilePro submission runId');
  return {submission_id:id,submission_url:`https://app.flatfile.pro/activity/import/${id}`};
}

export async function submitAttended({session,click,attemptPath,attempt,timeoutMs=15000}) {
  check(attempt.identity_kind==='uploaded_file','Attended submission requires exact uploaded workbook identity');
  const config=/\/([0-9]+)-[^/]+\.xlsx$/.exec(attempt.upload_key)?.[1];
  check(config,'Uploaded config ID is unavailable');
  const endpoint=`https://api.flatfile.pro/api/v2/imports/excel/${config}/update`;
  const responses=[],finished=new Set();let armed=false;
  await session.send('Network.enable',{});
  session.subscribe('Network.responseReceived',event=>{
    if(armed&&['XHR','Fetch'].includes(event.type)&&event.response.url===endpoint)responses.push({id:event.requestId,status:event.response.status});
  });
  session.subscribe('Network.loadingFinished',event=>{if(armed)finished.add(event.requestId);});
  try {
    await reserveSubmission(attemptPath,attempt);
    armed=true;
    await click();
    const until=Date.now()+timeoutMs;
    while(Date.now()<until&&!responses.some(response=>finished.has(response.id)))await new Promise(resolve=>setTimeout(resolve,50));
    check(responses.length===1&&finished.has(responses[0].id)&&responses[0].status>=200&&responses[0].status<300,'Submission response unavailable or ambiguous; reconcile without another click');
    const response=await session.send('Network.getResponseBody',{requestId:responses[0].id});
    check(!response.base64Encoded&&response.body.length<=100000,'Unexpected submission response encoding or size');
    const identity=submittedRunIdentity(JSON.parse(response.body));
    await durableReceipt(attemptPath,{...attempt,...identity,submission_response_at:new Date().toISOString()});
    return identity;
  } finally {armed=false;}
}
