/** Read exact listings through their normal FlatFilePro editor requests. */
import {readFile,mkdir,writeFile} from 'node:fs/promises';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {acquireTaskPage,releaseTaskPage,taskIdFor} from '../browserctl/task-tabs.mjs';
import * as ui from './browser-ui.mjs';

export const imageFields=['main_product_image_locator','swatch_product_image_locator',...Array.from({length:9},(_,i)=>`other_product_image_locator_${i+1}`)].map(x=>x+'.0.media_location');
export function listingLocation(account,target){
 ui.check(/^[A-Z0-9]+$/.test(account.seller_id||'')&&/^[A-Z0-9]+$/.test(account.marketplace_id||'')&&typeof target.sku==='string'&&target.sku.length>0&&/^[A-Z0-9]{10}$/.test(target.asin||''),'Exact listing identity required');
 const sku=encodeURIComponent(target.sku),market=account.marketplace_id,seller=account.seller_id;
 return {url:`https://app.flatfile.pro/amazon-listings-item/${market}/${seller}/${sku}/edit`,endpoint:`https://api.flatfile.pro/amazon-listings/item-detail?marketplace_id=${market}&seller_id=${seller}&sku=${sku}`};
}
export function normalizeListing(data,account,target,observedAt,sourceId){
 ui.check(data?.seller_id===account.seller_id&&data.marketplace_id===account.marketplace_id&&data.sku===target.sku&&data.asin===target.asin,'Listing response identity mismatch');
 ui.check(data.attributes&&typeof data.attributes==='object'&&!Array.isArray(data.attributes),'Complete listing attributes unavailable');
 ui.check(Number.isFinite(Date.parse(observedAt)),'Listing read timestamp unavailable');
 const row={sku:data.sku,asin:data.asin},relatedAsins={};
 for(const [field,values] of Object.entries(data.attributes)){
  ui.check(Array.isArray(values),'Unexpected listing attribute structure');
  if(['parentAsins','childAsins'].includes(field)){
   ui.check(values.every(value=>typeof value==='string'&&/^[A-Z0-9]{10}$/.test(value))&&new Set(values).size===values.length,'Invalid related listing ASINs');
   relatedAsins[field]=[...values];continue;
  }
  values.forEach((value,index)=>{ui.check(value&&typeof value==='object'&&!Array.isArray(value),'Unexpected attribute occurrence');ui.check(!value.marketplace_id||value.marketplace_id===account.marketplace_id,'Listing attribute marketplace mismatch');for(const [key,item] of Object.entries(value))if(item===null||['string','number','boolean'].includes(typeof item))row[`${field}.${index}.${key}`]=item===null?'':String(item);});
 }
 // Absence is established from the full item-detail attributes object, never a partial table.
 for(const field of imageFields)if(!Object.hasOwn(row,field))row[field]='';
 for(const field of ['parentage_level.0.value','child_parent_sku_relationship.0.parent_sku'])if(!Object.hasOwn(row,field))row[field]='';
 const parentage=row['parentage_level.0.value'],parent=row['child_parent_sku_relationship.0.parent_sku'];
 if(!parentage&&!parent&&!data.parent_sku&&!Object.values(relatedAsins).some(values=>values.length)&&Array.isArray(data.relationships)&&data.relationships.length===0&&!Object.keys(data.attributes).some(x=>/relationship/.test(x)&&data.attributes[x]?.length))row.listing_relationship_evidence='standalone';
 if(data.itemName)row.itemName=String(data.itemName);
 if(data.productType||data.product_type)row.product_type=String(data.productType||data.product_type);
 // Keep discovery aliases derived from the same exact item attributes. Conflicting
 // occurrences remain unavailable to the resolver rather than choosing the first.
 const value=field=>{const values=[...new Set((data.attributes[field]||[]).map(x=>x.value).filter(x=>x!==undefined&&x!==null&&String(x).trim()!=='').map(String))];return values.length===1?values[0]:'';};
 for(const [key,field] of Object.entries({mpn:'part_number',color:'color',size:'size',parentage:'parentage_level'}))row[key]=value(field);
 const summary=(data.summaries||[]).filter(x=>!x.marketplaceId||x.marketplaceId===account.marketplace_id);
 ui.check(summary.length<=1,'Ambiguous listing summary marketplace');
 const amazonUpdated=summary[0]?.lastUpdatedDate??data.lastUpdatedDate??null;
 ui.check(amazonUpdated===null||Number.isFinite(Date.parse(amazonUpdated)),'Invalid Amazon listing update timestamp');
 return {seller_id:data.seller_id,marketplace_id:data.marketplace_id,sku:data.sku,asin:data.asin,row,observed_at:observedAt,source_id:sourceId,version_id:data.id??data.versionId??null,
  amazon_updated_at:amazonUpdated,ffp_synced_at:null,
  relationships:Array.isArray(data.relationships)?structuredClone(data.relationships):null,related_asins:relatedAsins,
  parent_sku:data.parent_sku??null,archived:data.archived??null};
}
export async function readListing(session,account,target){
 await session.assertTaskControl({exclusiveContext:true});
 const location=listingLocation(account,target),responses=[],finished=new Set();let active=true;
 await session.send('Network.enable',{});
 const stops=[session.subscribe('Network.responseReceived',e=>{if(active&&['XHR','Fetch'].includes(e.type)&&e.response.url===location.endpoint)responses.push({id:e.requestId,status:e.response.status});}),session.subscribe('Network.loadingFinished',e=>{if(active)finished.add(e.requestId);})];
 try{
  await session.send('Page.navigate',{url:location.url});
  await ui.waitFor(async()=>responses,r=>r.length>0&&r.every(x=>finished.has(x.id)),60000);
  ui.check(responses.length===1&&responses[0].status===200,'Expected exactly one successful listing response');
  const response=await session.send('Network.getResponseBody',{requestId:responses[0].id});
  ui.check(!response.base64Encoded,'Unexpected listing response encoding');
  const data=JSON.parse(response.body);
  await ui.waitFor(()=>ui.snapshot(session),s=>s.url===location.url&&s.text.includes('ASIN: '+target.asin));
  await session.assertTaskControl({exclusiveContext:true});
  return normalizeListing(data,account,target,new Date().toISOString(),location.url);
 }finally{active=false;for(const stop of stops)if(typeof stop==='function')stop();}
}
export async function collect(input,deps={}){
 const common={schema_version:1,account:input.account,plan_hash:input.plan_hash,source_kind:'flatfilepro_listing_read'};
 let page,outcome='error';const at=deps.now||(()=>Date.now());
 try{
  ui.check(input.schema_version===1&&input.operation_id&&/^[a-f0-9]{64}$/.test(input.plan_hash||'')&&Array.isArray(input.targets)&&input.targets.length>0,'Invalid listing collector request');
  ui.check(new Set(input.targets.map(x=>x.sku)).size===input.targets.length,'Duplicate listing target');
  input.targets.forEach(x=>listingLocation(input.account,x));
  const minimum=input.minimum_after?Date.parse(input.minimum_after):0;ui.check(Number.isFinite(minimum)&&minimum<=at(),'Invalid listing read boundary');
  const directory=resolve(input.output_dir);await mkdir(directory,{recursive:true});
  page=await (deps.acquire||acquireTaskPage)({taskId:taskIdFor('amazon-operations',input.operation_id),slot:'ffp-listing-read',workflow:'amazon-flatfilepro',initialUrl:'https://app.flatfile.pro/exports',exclusiveContext:true});
  if(!deps.read){await page.session.send('Page.navigate',{url:'https://app.flatfile.pro/exports'});await ui.selectFlatFileProAccount(page.session,input.account);}
  const records=[];for(const target of input.targets)records.push(await (deps.read||readListing)(page.session,input.account,target));
  ui.check(records.length===input.targets.length&&records.every((r,i)=>r.sku===input.targets[i].sku&&r.asin===input.targets[i].asin&&Date.parse(r.observed_at)>=minimum&&Date.parse(r.observed_at)<=at()),'Listing coverage or read timestamp mismatch');
  const rows=Object.fromEntries(records.map(r=>[r.sku,r.row]));
  const observed_at=new Date(Math.min(...records.map(r=>Date.parse(r.observed_at)))).toISOString();
  const result={...common,status:'collected',complete:true,observed_at,source_id:'flatfilepro:item-detail',rows,records};
  const bytes=Buffer.from(JSON.stringify(result)),path=join(directory,`listings-${at()}-${createHash('sha256').update(bytes).digest('hex').slice(0,12)}.json`);
  await writeFile(path,bytes,{flag:'wx'}).catch(async e=>{if(e.code!=='EEXIST'||!(await readFile(path)).equals(bytes))throw e;});
  outcome='success';return {...result,path,sha256:createHash('sha256').update(bytes).digest('hex')};
 }catch(error){return {...common,status:'blocked',reason:'ffp_listing_read_unavailable',message:error.message};}
 finally{if(page)await (deps.release||releaseTaskPage)(page,{outcome});}
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){try{ui.check(process.argv.length===4&&process.argv[2]==='--request','Usage: --request FILE');console.log(JSON.stringify(await collect(JSON.parse(await readFile(process.argv[3],'utf8')))));}catch(error){console.log(JSON.stringify({schema_version:1,status:'blocked',reason:'collector_preflight',message:error.message}));process.exitCode=2;}}
