/** Read-only Activity evidence for a previously captured exact submission run. */
import {readFile} from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
import {acquireTaskPage,releaseTaskPage,taskIdFor} from '../browserctl/task-tabs.mjs';
import * as ui from './browser-ui.mjs';
import {submittedRunIdentity} from './flatfilepro-submit.mjs';

const states=new Set(['pending','in_progress','rejected','failed','reflected']);
function canonical(field) {
  return String(field).replace(/^\/(other_product_image_locator_[1-8])\/0\/media_location$/,'$1.0.media_location')
    .replace(/^(other_product_image_locator_[1-8])__1__media_location$/,'$1.0.media_location');
}

export function activityRequestMatch(url,input,cursor) {
  const parsed=new URL(url),base=`/listing-update-runs/${encodeURIComponent(input.submission_id)}/`;
  if(parsed.origin!=='https://api.flatfile.pro'||!['summary','items'].some(kind=>parsed.pathname===base+kind))return null;
  if(parsed.searchParams.getAll('seller_id').length!==1||parsed.searchParams.get('seller_id')!==input.account.seller_id||
    parsed.searchParams.getAll('marketplace_id').length!==1||parsed.searchParams.get('marketplace_id')!==input.account.marketplace_id)return null;
  const kind=parsed.pathname.slice(base.length);
  if(kind==='items'&&((parsed.searchParams.get('cursor')||null)!==cursor||parsed.searchParams.getAll('cursor').length>1||parsed.searchParams.get('pageSize')!=='25'))return null;
  return kind;
}

export async function collectActivity(input,readPage) {
  submittedRunIdentity({runId:input.submission_id});
  ui.check(input.account?.seller_id&&input.account?.marketplace_id&&input.plan_hash,'Activity requires bound account and plan');
  const expected=input.expected_rows;
  ui.check(expected&&Object.keys(expected).length>0,'Activity requires expected SKU attributes');
  const seenSkus=new Set(),seenCursors=new Set(),attributes=[];
  let cursor=null,summary;
  for(let page=0;page<200;page++) {
    const response=await readPage(cursor);
    summary=response.summary;
    for(const field of ['reflected','inProgress','rejected','failed'])ui.check(Number.isSafeInteger(summary?.[field])&&summary[field]>=0,'Activity summary counts unavailable');
    ui.check(Array.isArray(response.items)&&typeof response.hasMore==='boolean','Activity pagination metadata unavailable');
    for(const item of response.items) {
      ui.check(item.sellerId===input.account.seller_id&&item.marketplaceId===input.account.marketplace_id,'Activity item account mismatch');
      ui.check(Object.hasOwn(expected,item.sku)&&!seenSkus.has(item.sku),'Activity unexpected or duplicate SKU');
      seenSkus.add(item.sku);
      const fields=new Map(Object.keys(expected[item.sku]).map(field=>[canonical(field),field]));
      ui.check(fields.size===Object.keys(expected[item.sku]).length&&fields.size>0,'Expected fields are ambiguous');
      ui.check(Array.isArray(item.attributes)&&item.attributes.length===fields.size,'Activity attribute coverage mismatch');
      const seenFields=new Set();
      for(const attribute of item.attributes) {
        if(attribute.destinationPath!=null&&attribute.destinationAttribute!=null)
          ui.check(canonical(attribute.destinationPath)===canonical(attribute.destinationAttribute),'Activity destination identifiers disagree');
        const key=canonical(attribute.destinationPath??attribute.destinationAttribute),field=fields.get(key);
        ui.check(field&&!seenFields.has(field)&&states.has(attribute.status),'Activity field or status unavailable, unexpected or duplicated');
        seenFields.add(field);
        ui.check(attribute.submittedValue===expected[item.sku][field],'Activity submitted value differs from bound plan');
        // Reflected media may use Amazon's rewritten URL. Content identity is
        // established by the live-image verifier, never by this status alone.
        if(attribute.status==='reflected')ui.check(typeof attribute.liveValue==='string'&&attribute.liveValue.startsWith('https://'),'Reflected attribute has no HTTPS live value');
        attributes.push({sku:item.sku,field,status:attribute.status,live_value:attribute.liveValue??null,submitted_value:attribute.submittedValue});
      }
    }
    if(!response.hasMore) {
      ui.check(!response.nextCursor&&seenSkus.size===Object.keys(expected).length,'Activity coverage incomplete');
      return {schema_version:1,status:'collected',account:input.account,plan_hash:input.plan_hash,submission_id:input.submission_id,
        source_id:`https://app.flatfile.pro/activity/import/${input.submission_id}`,observed_at:new Date().toISOString(),
        summary:Object.fromEntries(['parentEventId','reflected','inProgress','rejected','failed'].filter(key=>Object.hasOwn(summary,key)).map(key=>[key,summary[key]])),attributes,complete:true};
    }
    ui.check(response.items.length>0&&typeof response.nextCursor==='string'&&response.nextCursor&&!seenCursors.has(response.nextCursor),'Activity pagination did not advance');
    seenCursors.add(response.nextCursor);cursor=response.nextCursor;
  }
  throw Error('Activity pagination exceeds supported limit');
}

export async function run(input) {
  let page;
  try {
    ui.check(input.schema_version===1&&input.operation_id,'Invalid Activity request');
    const identity=submittedRunIdentity({runId:input.submission_id});
    page=await acquireTaskPage({taskId:taskIdFor('amazon-operations',input.operation_id),workflow:'amazon-flatfilepro',initialUrl:identity.submission_url,exclusiveContext:true});
    await page.session.send('Page.navigate',{url:'https://app.flatfile.pro/exports'});
    await ui.selectFlatFileProAccount(page.session,input.account);
    await page.session.send('Network.enable',{});
    let pending=null;
    page.session.subscribe('Network.responseReceived',event=>{
      if(!pending||!['XHR','Fetch'].includes(event.type))return;
      const kind=activityRequestMatch(event.response.url,input,pending.cursor);
      if(kind)pending.responses.push({kind,id:event.requestId,status:event.response.status});
    });
    page.session.subscribe('Network.loadingFinished',event=>{if(pending)pending.finished.add(event.requestId);});
    return await collectActivity(input,async cursor=>{
      pending={cursor,responses:[],finished:new Set()};
      const url=new URL(identity.submission_url);
      if(cursor) {
        url.searchParams.set('itemCursor',cursor);
        url.searchParams.set('previousItemCursor','');
        url.searchParams.set('itemPaginationRunId',String(input.submission_id));
        url.searchParams.set('itemPaginationSellerId',input.account.seller_id);
        url.searchParams.set('itemPaginationMarketplaceId',input.account.marketplace_id);
      }
      await page.session.send('Page.navigate',{url:url.href});
      const deadline=Date.now()+15000;
      const complete=()=>['summary','items'].every(kind=>pending.responses.some(response=>response.kind===kind&&pending.finished.has(response.id)));
      while(Date.now()<deadline&&!complete())await new Promise(resolve=>setTimeout(resolve,100));
      ui.check(complete(),'Exact Activity response coverage unavailable');
      await ui.context(page.session,input.account,'ffp');
      const data={};
      for(const kind of ['summary','items']) {
        const matches=pending.responses.filter(response=>response.kind===kind);
        ui.check(matches.length===1&&matches[0].status===200,'Activity response ambiguous or unsuccessful');
        const response=await page.session.send('Network.getResponseBody',{requestId:matches[0].id});
        ui.check(!response.base64Encoded&&response.body.length<=5000000,'Activity response exceeds supported format');
        data[kind]=JSON.parse(response.body);
      }
      pending=null;
      return {summary:data.summary,...data.items};
    });
  }catch(error){return {schema_version:1,status:'blocked',account:input.account,plan_hash:input.plan_hash,submission_id:input.submission_id,reason:'ffp_activity_unverified',message:error.message,complete:false};}
  finally{if(page)await releaseTaskPage(page,{outcome:'handoff'});}
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href) {
  try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');console.log(JSON.stringify(await run(JSON.parse(await readFile(process.argv[3],'utf8')))));}
  catch(error){console.log(JSON.stringify({status:'blocked',reason:'ffp_activity_request_invalid',message:error.message,complete:false}));process.exitCode=2;}
}
