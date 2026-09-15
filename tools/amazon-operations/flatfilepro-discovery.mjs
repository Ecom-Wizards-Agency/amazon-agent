/** Complete account-scoped catalog discovery. Grid coverage precedes exact item reads. */
import * as ui from './browser-ui.mjs';
import {readListing} from './flatfilepro-listings.mjs';
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {acquireTaskPage,releaseTaskPage,taskIdFor} from '../browserctl/task-tabs.mjs';
import {evaluate} from '../report-fetcher/cdp.mjs';

// Observed September 14 in ffp-refresh-20260914/1789362693325-responses.json.
// Capture only normal UI reads; this collector never calls the fetch/refetch route.
export function catalogRequest(url,account){
 const parsed=new URL(url);ui.check(parsed.origin==='https://api.flatfile.pro'&&['/amazon-listings/items','/amazon-listings/total-count'].includes(parsed.pathname),'Unexpected catalog endpoint');
 for(const key of ['filter','page','pageSize'])ui.check(parsed.searchParams.getAll(key).length===1,'Catalog request parameter missing or duplicated');
 ui.check([...parsed.searchParams.keys()].every(key=>['filter','marketplaceId','sellerId','page','pageSize','sortModel[]','insertOnboardingStep'].includes(key)),'Unexpected catalog query filter');
 ui.check(parsed.searchParams.getAll('sortModel[]').length===1&&JSON.stringify(JSON.parse(parsed.searchParams.get('sortModel[]')))===JSON.stringify({field:'sku',sort:'asc'}),'Catalog requires observed stable SKU ordering');
 ui.check(parsed.searchParams.get('insertOnboardingStep')==='false','Catalog request must not insert onboarding state');
 const hasTopLevelAccount=parsed.searchParams.has('sellerId')||parsed.searchParams.has('marketplaceId');
 if(hasTopLevelAccount)ui.check(parsed.searchParams.getAll('sellerId').length===1&&parsed.searchParams.getAll('marketplaceId').length===1&&parsed.searchParams.get('sellerId')===account.seller_id&&parsed.searchParams.get('marketplaceId')===account.marketplace_id,'Catalog request account mismatch');
 const filter=JSON.parse(parsed.searchParams.get('filter'));
 ui.check(filter&&filter.sellerId===account.seller_id&&filter.marketplaceId===account.marketplace_id,'Catalog filter account mismatch');
 ui.check(Object.keys(filter).every(key=>['brands','archived','variation','marketplaceId','sellerId'].includes(key)),'Catalog has a narrowing filter');
 ui.check(Array.isArray(filter.brands)&&filter.brands.length===1&&typeof filter.brands[0]==='string'&&filter.brands[0].length>0,'Catalog brand binding unavailable');
 ui.check(filter.archived==='NOT ARCHIVED'&&filter.variation==='ALL LISTINGS','Catalog must include all nonarchived variations');
 const page=Number(parsed.searchParams.get('page')),size=Number(parsed.searchParams.get('pageSize'));
 ui.check(Number.isSafeInteger(page)&&page>=0&&Number.isSafeInteger(size)&&size>0,'Catalog pagination invalid');
 const scope=JSON.stringify({sellerId:filter.sellerId,marketplaceId:filter.marketplaceId,brands:filter.brands,archived:filter.archived,variation:filter.variation,pageSize:size,sort:'sku:asc'});
 return {kind:parsed.pathname.endsWith('/items')?'items':'count',page,size,scope,filter};
}

export function normalizeCatalogPage(itemResponse,countResponse,account){
 const request=catalogRequest(itemResponse.url,account),countRequest=catalogRequest(countResponse.url,account);
 ui.check(request.kind==='items'&&countRequest.kind==='count'&&request.scope===countRequest.scope,'Catalog total scope mismatch');
 ui.check(Array.isArray(itemResponse.data?.rows)&&Number.isSafeInteger(countResponse.data?.count)&&countResponse.data.count>=0,'Catalog response coverage unavailable');
 const offset=request.page*request.size,total=countResponse.data.count,items=itemResponse.data.rows;
 ui.check(items.length===Math.min(request.size,Math.max(0,total-offset)),'Catalog page is truncated');
 return {...account,offset,total,items,has_more:offset+items.length<total,observed_at:itemResponse.observed_at,
  source_id:itemResponse.url,count_source_id:countResponse.url,count_observed_at:countResponse.observed_at,filter:request.filter};
}

export async function readCatalogPages(session,account){
 await session.assertTaskControl({exclusiveContext:true});
 await session.send('Network.enable',{});
 const responses=[],finished=new Set();let active=true;
 const stops=[session.subscribe('Network.responseReceived',event=>{
  if(!active||!['XHR','Fetch'].includes(event.type))return;
  const url=new URL(event.response.url);
  if(url.origin==='https://api.flatfile.pro'&&['/amazon-listings/items','/amazon-listings/total-count'].includes(url.pathname))responses.push({id:event.requestId,url:event.response.url,status:event.response.status});
 }),session.subscribe('Network.loadingFinished',event=>finished.add(event.requestId))];
 const readResponse=async response=>{ui.check(response.status===200,'Catalog request failed');const body=await session.send('Network.getResponseBody',{requestId:response.id});ui.check(!body.base64Encoded,'Unexpected catalog response encoding');return {...response,data:JSON.parse(body.body),observed_at:new Date().toISOString()};};
 try{
  await ui.clickFlatFilePro(session,'Listings');
  const pages=[];let count=null,scope=null;
  for(let page=0;;page++){
   ui.check(page<10000,'Catalog pagination exceeded bounded coverage');
   await ui.waitFor(async()=>responses,list=>list.some(response=>{try{return catalogRequest(response.url,account).kind==='items'&&catalogRequest(response.url,account).page===page&&finished.has(response.id);}catch{return false;}}),60000);
   if(!count){
    await ui.waitFor(async()=>responses,list=>list.some(response=>{try{return catalogRequest(response.url,account).kind==='count'&&finished.has(response.id);}catch{return false;}}),60000);
    const candidates=responses.filter(response=>catalogRequest(response.url,account).kind==='count'&&finished.has(response.id));
    const counts=await Promise.all(candidates.map(readResponse));count=counts.at(-1);
    ui.check(counts.every(value=>value.data?.count===count.data?.count),'Catalog total changed during initial read');
   }
   const candidates=responses.filter(response=>{const request=catalogRequest(response.url,account);return request.kind==='items'&&request.page===page&&finished.has(response.id);});
   const reads=await Promise.all(candidates.map(readResponse)),current=reads.at(-1);
   ui.check(reads.every(value=>JSON.stringify(value.data)===JSON.stringify(current.data)),'Catalog page changed during read');
   const request=catalogRequest(current.url,account);scope??=request.scope;ui.check(request.scope===scope,'Catalog scope changed between pages');
   for(const response of responses.filter(response=>catalogRequest(response.url,account).kind==='count'&&finished.has(response.id))){const latest=await readResponse(response);ui.check(catalogRequest(latest.url,account).scope===scope&&latest.data?.count===count.data.count,'Catalog total or scope changed during pagination');}
   const normalized=normalizeCatalogPage(current,count,account);pages.push(normalized);
   await ui.context(session,account,'ffp');
   // The grid has identical top/bottom pagination controls. Require agreement.
   await ui.waitFor(()=>evaluate(session,`(()=>{const buttons=[...document.querySelectorAll('button[aria-label="Go to next page"]')].filter(e=>e.getBoundingClientRect().width>0);return buttons.map(e=>({disabled:e.disabled}))})()`),controls=>controls.length>0&&controls.every(control=>control.disabled===!normalized.has_more),15000);
   if(!normalized.has_more)break;
   await evaluate(session,`(()=>{const buttons=[...document.querySelectorAll('button[aria-label="Go to next page"]')].filter(e=>e.getBoundingClientRect().width>0);if(!buttons.length||buttons.some(e=>e.disabled))throw Error('Catalog next page unavailable');buttons[0].click()})()`);
  }
  validateCatalogPages(pages,account);return pages;
 }finally{active=false;for(const stop of stops)if(typeof stop==='function')stop();}
}

export async function collect(input,deps={}){
 const common={schema_version:1,account:input.account,plan_hash:input.plan_hash,source_kind:'flatfilepro_catalog_discovery'};
 let page,outcome='error';const now=deps.now||(()=>Date.now());
 try{
  ui.check(input.schema_version===1&&input.operation_id&&/^[a-f0-9]{64}$/.test(input.plan_hash||''),'Invalid catalog discovery request');
  const minimum=input.minimum_after?Date.parse(input.minimum_after):0;ui.check(Number.isFinite(minimum)&&minimum<=now(),'Invalid catalog read boundary');
  ui.check(input.inventory_only===undefined||typeof input.inventory_only==='boolean','Invalid inventory-only selection');
  const directory=resolve(input.output_dir);await mkdir(directory,{recursive:true});
  page=await(deps.acquire||acquireTaskPage)({taskId:taskIdFor('amazon-operations',input.operation_id),slot:'ffp-catalog-discovery',workflow:'amazon-flatfilepro',initialUrl:'https://app.flatfile.pro/exports',exclusiveContext:true});
  if(!deps.pages){await page.session.send('Page.navigate',{url:'https://app.flatfile.pro/exports'});await ui.selectFlatFileProAccount(page.session,input.account);}
  const pages=await(deps.pages||readCatalogPages)(page.session,input.account),inventory=validateCatalogPages(pages,input.account);
  ui.check(pages.every(value=>Date.parse(value.observed_at)>=minimum&&Date.parse(value.observed_at)<=now()),'Catalog read timestamp mismatch');
  ui.check(!input.inventory_only||input.targets===undefined,'Inventory-only discovery cannot request item details');
  ui.check(input.inventory_only!==false||input.targets!==undefined,'Exact detail targets are required');
  const inventoryOnly=input.targets===undefined;
  const detail=inventoryOnly?{inventory:inventory.targets,pages,rows:{},records:[],coverage:{complete:true,total:inventory.total,pages:inventory.pages,exact_reads:0},observed_at:new Date(Math.min(...pages.map(value=>Date.parse(value.observed_at)))).toISOString()}:await enrichCatalog(page.session,pages,input.account,{read:deps.read||readListing,minimum,now,targets:input.targets});
  const detailCoverage=inventoryOnly?'none':detail.records.length===inventory.total?'complete':'selected';
  const result={...common,...detail,status:'collected',complete:detailCoverage==='complete',inventory_complete:true,verified:true,source_id:'flatfilepro:catalog-items',catalog_scope:'all_nonarchived_listings',detail_coverage:detailCoverage};
  const bytes=Buffer.from(JSON.stringify(result)),sha256=createHash('sha256').update(bytes).digest('hex'),path=join(directory,`catalog-${now()}-${sha256.slice(0,12)}.json`);
  await writeFile(path,bytes,{flag:'wx'}).catch(async error=>{if(error.code!=='EEXIST'||!(await readFile(path)).equals(bytes))throw error;});
  outcome='success';return {...result,path,sha256};
 }catch(error){return {...common,status:'blocked',complete:false,reason:'ffp_catalog_discovery_unavailable',message:error.message};}
 finally{if(page)await(deps.release||releaseTaskPage)(page,{outcome});}
}

if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');console.log(JSON.stringify(await collect(JSON.parse(await readFile(process.argv[3],'utf8')))));}catch(error){console.log(JSON.stringify({schema_version:1,status:'blocked',reason:'collector_preflight',message:error.message}));process.exitCode=2;}}

/** Enrich only after every catalog page has passed coverage validation. */
export async function enrichCatalog(session,pages,account,{read=readListing,minimum=0,now=()=>Date.now(),targets}={}){
 const inventory=validateCatalogPages(pages,account);
 ui.check(pages.every(page=>Date.parse(page.observed_at)>=minimum&&Date.parse(page.observed_at)<=now()),'Catalog inventory read is stale or future dated');
 let selected=inventory.targets;
 if(targets!==undefined){
  ui.check(Array.isArray(targets)&&targets.length>0&&new Set(targets.map(target=>target.sku)).size===targets.length,'Invalid catalog detail target selection');
  selected=targets.map(target=>{const match=inventory.targets.find(item=>item.sku===target.sku);ui.check(match&&match.asin===target.asin,'Requested item is absent from the complete catalog');return match;});
 }
 const records=[];
 for(const target of selected){
  const record=await read(session,account,target);
  ui.check(record.seller_id===account.seller_id&&record.marketplace_id===account.marketplace_id,'Exact listing account differs from catalog');
  ui.check(record.sku===target.sku&&record.asin===target.asin&&record.row?.sku===target.sku&&record.row?.asin===target.asin,'Exact listing identity differs from catalog');
  ui.check(Date.parse(record.observed_at)>=minimum&&Date.parse(record.observed_at)<=now(),'Exact listing read is stale or future dated');
  records.push(record);
 }
 return {rows:Object.fromEntries(records.map(record=>[record.sku,record.row])),records,
  inventory:inventory.targets,pages,coverage:{complete:true,total:inventory.total,pages:inventory.pages,exact_reads:records.length},
  observed_at:new Date(Math.min(...pages.map(page=>Date.parse(page.observed_at)),...records.map(record=>Date.parse(record.observed_at)))).toISOString()};
}

/** Validate normalized page receipts after the observed UI transport is parsed. */
export function validateCatalogPages(pages,account){
 ui.check(Array.isArray(pages)&&pages.length>0,'Catalog pages missing');
 const targets=[],seen=new Set();let offset=0,total=null;
 for(const [index,page] of pages.entries()){
  ui.check(page.seller_id===account.seller_id&&page.marketplace_id===account.marketplace_id,'Catalog page account mismatch');
  ui.check(Number.isSafeInteger(page.offset)&&page.offset===offset,'Catalog page missing or repeated');
  ui.check(Number.isSafeInteger(page.total)&&page.total>=0,'Catalog total unavailable');
  total??=page.total;ui.check(page.total===total,'Catalog changed during pagination');
  ui.check(Array.isArray(page.items)&&typeof page.has_more==='boolean','Catalog page coverage unavailable');
  ui.check(Number.isFinite(Date.parse(page.observed_at)),'Catalog page read timestamp unavailable');
  ui.check(page.items.length>0||total===0&&pages.length===1,'Empty catalog page before completion');
  for(const item of page.items){
   ui.check(item.seller_id===account.seller_id&&item.marketplace_id===account.marketplace_id,'Catalog row account mismatch');
   ui.check(typeof item.sku==='string'&&item.sku.trim().length>0&&/^[A-Z0-9]{10}$/.test(item.asin||''),'Catalog row identity unavailable');
   ui.check(!seen.has(item.sku),'Duplicate catalog seller SKU');seen.add(item.sku);
   targets.push({...item});
  }
  offset+=page.items.length;
  ui.check(offset<=total,'Catalog rows exceed total');
  ui.check(page.has_more===(offset<total),'Catalog pagination disagrees with total');
  ui.check(page.has_more===(index<pages.length-1),'Catalog page coverage incomplete');
 }
 ui.check(offset===total,'Catalog coverage incomplete');
 return {targets,total,pages:pages.length};
}
