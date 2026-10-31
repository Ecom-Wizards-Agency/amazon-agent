/** Local, read-only tooling for saved FlatFilePro MCP results: binding, verified export download and per-SKU reads. */
// The MCP export download URL is a short-lived bearer secret. It is read from STDIN only and never
// printed, logged, passed in argv, written to a receipt or repeated in an error message.
// A get_listings JSON is a model-transcribed tool result, so it is a planning read only (D1): it may feed
// rows, survey, gaps and listing-json, never a workbook grid. Upload values come from the byte-verified export.
//
// node tools/amazon-operations/ffp-mcp.mjs <subcommand>
//   binding --marketplaces FILE (--seller-name N --marketplace-name M | --seller-id S --marketplace-id M)
//   fetch-export --out-dir DIR [--register-run RUN_ID]      < get_export_download result JSON on STDIN
//   resolve --export FILE (--sku S)... (--asin A)...
//   grid --export FILE --sku S... --out PATH.csv [--blank-columns] [--add-column HEADER]...
//   rows|survey|gaps|listing-json (--export FILE | --listings FILE) --sku S...
//     survey [--format json|csv|md]; gaps [--touch attr,attr]
// JSON on stdout (survey csv/md print text). Exit 0 ok, 2 blocked {status,reason,message}, 3 gaps found
// companion gaps. Every --export read first re-verifies the file SHA-256 against FILE.receipt.json.
// grid --blank-columns adds an empty column only for a blank path with an occurrence index and a leaf key
// (apparel_size[0].height_type). A change that names one writes that header into the upload workbook.
// Bare blank names (material) get no column: they go to blank_attributes_bare. header_count includes sku.
// grid --add-column adds an empty column under an export-spelled template header (generic_keyword__1__value)
// only when that attribute is absent from every selected record and listed in its analysed blankAttributes.
import {createReadStream} from 'node:fs';
import {readFile,writeFile,mkdir,rm,stat,open} from 'node:fs/promises';
import {basename,dirname,join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {createGunzip} from 'node:zlib';
import {StringDecoder} from 'node:string_decoder';
import {Readable,Transform} from 'node:stream';
import {pipeline} from 'node:stream/promises';
import {spawnSync} from 'node:child_process';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {authorizedBinding} from './flatfilepro-account.mjs';
import {normalizeListing,flattenAttributes} from './flatfilepro-listings.mjs';

export const EXPORT_HOST='ffp-mcp-export.s3.us-east-2.amazonaws.com';
export const CANDIDATE_ATTRIBUTES=Object.freeze(['material','item_form','special_feature','target_audience_keyword','ingredients','specific_uses_for_product','recommended_uses_for_product','product_benefit','care_instructions','included_components','number_of_items','unit_count','item_type_name','style','pattern','size','color','flavor','scent','age_range_description','directions','safety_warning','active_ingredients','skin_type','hair_type','closure','sleeve','fit_type','water_resistance_level','special_ingredients']);
const COMPANIONS={unit_count:[['value'],['type','value']],item_weight:[['value'],['unit']],item_package_weight:[['value'],['unit']],item_display_weight:[['value'],['unit']],nutritional_info:[['serving_quantity'],['serving_unit']]};
const SLOTS=[['MAIN','main_product_image_locator'],['SWCH','swatch_product_image_locator'],...Array.from({length:9},(_,i)=>[`PT0${i+1}`,`other_product_image_locator_${i+1}`])];
const DEFAULT_ARTIFACTCTL=join(dirname(fileURLToPath(import.meta.url)),'..','artifactctl','artifactctl');

export class Blocked extends Error{constructor(reason,message,extra={}){super(message);this.reason=reason;this.extra=extra;}}
const fail=(reason,message,extra)=>{throw new Blocked(reason,message,extra);};
const check=(ok,reason,message)=>{if(!ok)fail(reason,message);};
// Error text never carries a URL: S3 and fetch errors can echo the request.
export const redact=text=>String(text??'').replace(/[a-z][a-z0-9+.-]*:\/\/[^\s"'<>]+/gi,'[redacted-url]').replace(/X-Amz-[A-Za-z-]+=[^&\s"']+/g,'[redacted]');
const sha256File=async path=>{const hash=createHash('sha256');for await(const chunk of createReadStream(path))hash.update(chunk);return hash.digest('hex');};
const exists=async path=>{try{return await stat(path);}catch(error){if(error.code==='ENOENT')return null;throw error;}};
const text=value=>value===null||value===undefined?'':String(value);
const occurrence=(attributes,field,index=0)=>Array.isArray(attributes?.[field])?attributes[field][index]:undefined;
const firstValue=(attributes,field,key='value')=>text(occurrence(attributes,field)?.[key]);
const filled=value=>value!==null&&value!==undefined&&(typeof value==='object'?Object.values(value).some(filled):String(value).trim()!=='');

// ---- arguments ----
const FLAGS={
 binding:{value:['--marketplaces','--seller-name','--marketplace-name','--seller-id','--marketplace-id']},
 'fetch-export':{value:['--out-dir','--register-run']},
 resolve:{value:['--export'],repeat:['--sku','--asin']},
 grid:{value:['--export','--listings','--out'],repeat:['--sku','--add-column'],bool:['--blank-columns']},
 rows:{value:['--export','--listings'],repeat:['--sku']},
 survey:{value:['--export','--listings','--format'],repeat:['--sku']},
 gaps:{value:['--export','--listings','--touch'],repeat:['--sku']},
 'listing-json':{value:['--export','--listings'],repeat:['--sku']},
};
export function parseArgs(argv){
 const [command,...rest]=argv;check(Object.hasOwn(FLAGS,command||''),'usage','Usage: ffp-mcp.mjs <'+Object.keys(FLAGS).join('|')+'> [flags]');
 const spec=FLAGS[command],out={command};
 for(let i=0;i<rest.length;i++){
  let flag=rest[i],value;const eq=flag.indexOf('=');
  if(flag.startsWith('--')&&eq>2){value=flag.slice(eq+1);flag=flag.slice(0,eq);}
  if(spec.bool?.includes(flag)){check(value===undefined&&!out[flag],'usage','Flag takes no value or repeats: '+flag);out[flag]=true;continue;}
  const repeat=spec.repeat?.includes(flag);check(repeat||spec.value.includes(flag),'usage',`Unknown argument for ${command}: ${flag}`);
  // The next element is always the value, so dash-prefixed SKUs are never parsed as flags.
  if(value===undefined){check(i+1<rest.length,'usage','Missing value for '+flag);value=rest[++i];}
  check(value.trim()!=='','usage','Empty value for '+flag);
  if(repeat)(out[flag]??=[]).push(value);else{check(out[flag]===undefined,'usage','Repeated flag: '+flag);out[flag]=value;}
 }
 return out;
}

// ---- binding ----
const norm=value=>String(value??'').replace(/\s+/g,' ').trim().toLowerCase();
export async function binding(args){
 check(args['--marketplaces'],'usage','--marketplaces FILE is required');
 const byName=args['--seller-name']!==undefined||args['--marketplace-name']!==undefined,byId=args['--seller-id']!==undefined||args['--marketplace-id']!==undefined;
 check(byName!==byId,'usage','Use either --seller-name with --marketplace-name or --seller-id with --marketplace-id');
 let body;try{body=JSON.parse(await readFile(args['--marketplaces'],'utf8'));}catch(error){fail('marketplaces_unreadable','Saved get_authorized_marketplaces JSON is unreadable: '+error.message);}
 const rows=body?.marketplaces;check(Array.isArray(rows),'marketplaces_unreadable','Saved marketplaces JSON needs a marketplaces array');
 let account;
 if(byName){
  check(args['--seller-name']&&args['--marketplace-name'],'usage','--seller-name and --marketplace-name are both required');
  const matches=rows.filter(row=>norm(row?.seller_name)===norm(args['--seller-name'])&&norm(row?.marketplace_name)===norm(args['--marketplace-name']));
  check(matches.length===1,matches.length?'binding_ambiguous':'binding_unavailable',`${matches.length} authorized rows match seller "${args['--seller-name']}" in "${args['--marketplace-name']}"; exactly one is required`);
  account={seller_id:matches[0].selling_partner_id,marketplace_id:matches[0].marketplace_id};
 }else{
  check(args['--seller-id']&&args['--marketplace-id'],'usage','--seller-id and --marketplace-id are both required');
  account={seller_id:args['--seller-id'],marketplace_id:args['--marketplace-id']};
 }
 let names;try{names=authorizedBinding({sp_api_authorized_marketplaces:rows},account);}catch(error){fail('binding_unavailable',error.message);}
 return {status:'resolved',binding_source:'ffp-mcp',seller_id:account.seller_id,marketplace_id:account.marketplace_id,seller_name:names.seller_name,marketplace_name:names.marketplace_name,
  flatfilepro_option_name:names.seller_name,flatfilepro_display_name:`${names.seller_name} (${names.marketplace_name})`,note:'browser selector readback remains required before upload'};
}

// ---- export download ----
export function validateExportResult(result,now){
 check(result&&typeof result==='object'&&!Array.isArray(result),'export_result_invalid','STDIN must be the get_export_download result JSON object');
 let url;try{url=new URL(result.downloadUrl);}catch{fail('export_url_invalid','downloadUrl is missing or not a URL');}
 check(url.protocol==='https:','export_url_invalid','downloadUrl must use https');
 check(url.hostname===EXPORT_HOST,'export_url_invalid','downloadUrl host is not the FlatFilePro export bucket');
 check(url.username===''&&url.password===''&&url.port==='','export_url_invalid','downloadUrl must not carry userinfo or a port');
 check(url.pathname.startsWith('/catalog-exports/'),'export_url_invalid','downloadUrl path is outside /catalog-exports/');
 check(result.format==='JSONL'&&result.compression==='GZIP'&&result.checksumAlgorithm==='SHA-256','export_result_invalid','Export must be JSONL, GZIP and SHA-256');
 check(result.counts_match===true,'export_counts_mismatch','Export counts_match is not true');
 check(result.schemaVersion===2,'export_result_invalid','Unsupported export schemaVersion: '+result.schemaVersion);
 check(/^[A-Z0-9]+$/.test(result.sellerId||'')&&/^[A-Z0-9]+$/.test(result.marketplaceId||''),'export_result_invalid','Export sellerId or marketplaceId is invalid');
 check(typeof result.jobId==='string'&&result.jobId.trim()!=='','export_result_invalid','Export jobId is missing');
 check(Number.isInteger(result.export_count)&&result.export_count>=0,'export_result_invalid','Export export_count is invalid');
 check(Number.isInteger(result.compressedBytes)&&result.compressedBytes>0,'export_result_invalid','Export compressedBytes is invalid');
 check(/^[a-f0-9]{64}$/i.test(result.sha256||''),'export_result_invalid','Export sha256 is invalid');
 check(typeof result.fileName==='string'&&/^[A-Za-z0-9._-]+$/.test(result.fileName)&&result.fileName.endsWith('.jsonl.gz')&&!result.fileName.startsWith('.'),'export_result_invalid','Export fileName must match [A-Za-z0-9._-]+ and end .jsonl.gz');
 const expires=Date.parse(result.urlExpiresAt);check(!result.urlExpiresAt||!Number.isFinite(expires)||expires>now,'export_url_expired','The export download URL has expired; call get_export_download again');
 return url;
}
// One pass: hash the compressed bytes, gunzip and parse every non-empty line. Callers use kept records
// only after the digest has been compared.
async function scanExport(path,{sellerId,marketplaceId,keep=()=>false,onRecord=()=>{}}){
 const hash=createHash('sha256');let bytes=0,count=0;const kept=[];
 const hasher=new Transform({transform(chunk,encoding,done){hash.update(chunk);bytes+=chunk.length;done(null,chunk);}});
 try{
  const handle=line=>{
    if(!line.trim())return;count++;
    let record;try{record=JSON.parse(line);}catch{fail('export_record_invalid',`Export line ${count} is not JSON`);}
    check(record&&typeof record==='object'&&!Array.isArray(record),'export_record_invalid',`Export record ${count} is not an object`);
    check(record.sellerId===sellerId&&record.marketplaceId===marketplaceId,'export_foreign_record',`Export record ${count} belongs to another seller or marketplace`);
    check(typeof record.sku==='string'&&record.sku!==''&&typeof record.asin==='string'&&record.attributes&&typeof record.attributes==='object'&&!Array.isArray(record.attributes),'export_record_invalid',`Export record ${count} lacks sku, asin or attributes`);
    onRecord(record);if(keep(record))kept.push(record);
  };
  // Manual line split: readline re-emits a destroyed gunzip error after the loop has already failed.
  await pipeline(createReadStream(path),hasher,createGunzip(),async source=>{
   const decoder=new StringDecoder('utf8');let buffer='';
   for await(const chunk of source){const parts=(buffer+decoder.write(chunk)).split('\n');buffer=parts.pop();parts.forEach(handle);}
   handle(buffer+decoder.end());
  });
 }catch(error){if(error instanceof Blocked)throw error;fail('export_unreadable','Export file could not be decompressed or read: '+error.message);}
 return {sha256:hash.digest('hex'),bytes,count,kept};
}
const RECEIPT_FIELDS=['jobId','sellerId','marketplaceId','archiveStatus','schemaVersion','snapshotAt','completedAt','export_count','sha256','compressedBytes','fileName'];
export function defaultArtifactctl(args){const result=spawnSync(process.env.AMAZON_ARTIFACTCTL||DEFAULT_ARTIFACTCTL,args,{encoding:'utf8'});return {status:result.status,stdout:result.stdout||'',stderr:result.stderr||(result.error?.message??'')};}
export function register(run,paths,artifactctl){
 const artifacts=[];
 try{
  for(const path of paths){
   const result=artifactctl(['register','--run',run,'--path',path,'--disposition','preserve']);
   if(result.status!==0)return {registration:'failed',registration_message:redact((result.stderr||result.stdout||'artifactctl failed').trim())};
   const parsed=JSON.parse(result.stdout);artifacts.push({path,artifact_id:parsed.id??parsed.artifact_id??null,state:parsed.state??null});
  }
 }catch(error){return {registration:'failed',registration_message:redact(error.message)};}
 return {registration:'registered',registration_run:run,registered_artifacts:artifacts};
}
export async function fetchExport(args,deps){
 check(args['--out-dir'],'usage','--out-dir DIR is required');
 const now=deps.now(),raw=await deps.readStdin();
 check(raw.length<=1_000_000,'export_result_invalid','STDIN is larger than a get_export_download result');
 let result;try{result=JSON.parse(raw);}catch{fail('export_result_invalid','STDIN is not JSON; pipe the get_export_download result');}
 if(typeof result?.downloadUrl==='string'){deps.secrets.push(result.downloadUrl);try{const parsed=new URL(result.downloadUrl);deps.secrets.push(parsed.href,parsed.search);}catch{}}
 const url=validateExportResult(result,now);
 const expected={...result,sha256:result.sha256.toLowerCase()};
 const directory=resolve(args['--out-dir']);await mkdir(directory,{recursive:true});
 const path=join(directory,result.fileName),receiptPath=path+'.receipt.json',created=[];
 const verify=async()=>{
  const size=(await stat(path)).size;check(size===result.compressedBytes,'export_size_mismatch',`Export is ${size} bytes; result says ${result.compressedBytes}`);
  check(await sha256File(path)===expected.sha256,'export_sha_mismatch','Export SHA-256 differs from the result');
  const scan=await scanExport(path,{sellerId:result.sellerId,marketplaceId:result.marketplaceId,onRecord:record=>check(result.archiveStatus!=='UNARCHIVED'||record.archived!==true,'export_archive_mismatch',`Unarchived export carries archived SKU ${record.sku}`)});
  check(scan.bytes===result.compressedBytes,'export_size_mismatch',`Export is ${scan.bytes} bytes; result says ${result.compressedBytes}`);
  check(scan.sha256===expected.sha256,'export_sha_mismatch','Export SHA-256 differs from the result');
  check(scan.count===result.export_count,'export_count_mismatch',`Export has ${scan.count} records; result says ${result.export_count}`);
 };
 let status='fetched';
 try{
  const existing=await exists(path);
  if(existing){
   check(existing.size===result.compressedBytes&&await sha256File(path)===expected.sha256,'export_file_exists','A different file already exists at '+path+'; choose another --out-dir');
   status='existing';await verify();
  }else{
   let handle;try{handle=await open(path,'wx');}catch(error){fail('export_file_exists',error.code==='EEXIST'?'A file appeared at '+path+' during the fetch':'Cannot create '+path+': '+error.code);}
   created.push(path);
   let response;
   try{response=await deps.fetch(url.href,{redirect:'error'});}catch{await handle.close().catch(()=>{});fail('export_download_failed','Export download request failed; redirects are refused');}
   if(response.status!==200||!response.body){await handle.close().catch(()=>{});fail('export_download_failed',`Export download returned HTTP ${response.status}`);}
   let bytes=0;
   const limit=new Transform({transform(chunk,encoding,done){bytes+=chunk.length;done(bytes>result.compressedBytes?new Error('size limit'):null,chunk);}});
   try{await pipeline(Readable.fromWeb(response.body),limit,handle.createWriteStream());}
   catch{await handle.close().catch(()=>{});fail(bytes>result.compressedBytes?'export_size_mismatch':'export_download_failed',bytes>result.compressedBytes?`Export download exceeded ${result.compressedBytes} bytes`:'Export download stream failed');}
   await verify();
  }
  const receipt={...Object.fromEntries(RECEIPT_FIELDS.map(key=>[key,expected[key]])),path,fetched_at:new Date(now).toISOString(),source:'ffp-mcp-export'};
  const prior=await exists(receiptPath);
  if(prior){
   let saved;try{saved=JSON.parse(await readFile(receiptPath,'utf8'));}catch{fail('receipt_conflict','Existing receipt is unreadable: '+receiptPath);}
   check(RECEIPT_FIELDS.every(key=>saved[key]===receipt[key])&&saved.source==='ffp-mcp-export','receipt_conflict','Existing receipt differs from this export result: '+receiptPath);
   Object.assign(receipt,{fetched_at:saved.fetched_at,path:saved.path});
  }else{await writeFile(receiptPath,JSON.stringify(receipt,null,1)+'\n',{flag:'wx'});created.push(receiptPath);}
  const output={status,path,receipt_path:receiptPath,fileName:result.fileName,sha256:expected.sha256,compressedBytes:result.compressedBytes,export_count:result.export_count,seller_id:result.sellerId,marketplace_id:result.marketplaceId,archiveStatus:result.archiveStatus,jobId:result.jobId,snapshotAt:result.snapshotAt,registration:'not_requested'};
  if(args['--register-run'])Object.assign(output,register(args['--register-run'],[path,receiptPath],deps.artifactctl));
  return output;
 }catch(error){for(const file of created.reverse())await rm(file,{force:true});throw error;}
}

// ---- verified local reads ----
export async function openExport(file,keep){
 const path=resolve(file),receiptPath=path+'.receipt.json';
 let receipt;try{receipt=JSON.parse(await readFile(receiptPath,'utf8'));}catch{fail('receipt_missing','Export receipt is missing or unreadable: '+receiptPath+'; fetch the export with fetch-export');}
 check(receipt?.source==='ffp-mcp-export'&&receipt.fileName===basename(path)&&/^[a-f0-9]{64}$/.test(receipt.sha256||'')&&Number.isInteger(receipt.export_count),'receipt_invalid','Export receipt does not describe '+basename(path));
 check(await sha256File(path)===receipt.sha256,'receipt_mismatch','Export file SHA-256 differs from its receipt');
 // The scan hashes again so a file swapped between the two reads is still refused.
 const scan=await scanExport(path,{sellerId:receipt.sellerId,marketplaceId:receipt.marketplaceId,keep});
 check(scan.sha256===receipt.sha256,'receipt_mismatch','Export file SHA-256 differs from its receipt');
 check(scan.count===receipt.export_count,'receipt_mismatch',`Export has ${scan.count} records; receipt says ${receipt.export_count}`);
 return {path,receipt,records:scan.kept};
}
// Digest of the resolved tool arguments (ID selectors, SKUs in --sku order), keys in a fixed order.
const argumentsSha=args=>createHash('sha256').update(JSON.stringify(Object.fromEntries(Object.keys(args).sort().map(key=>[key,args[key]])))).digest('hex');
const exportMeta=receipt=>({sha256:receipt.sha256,jobId:receipt.jobId,snapshotAt:receipt.snapshotAt,fileName:receipt.fileName});
function requestedSkus(args){
 const skus=args['--sku']||[];check(skus.length>0,'usage','At least one --sku is required');
 const duplicate=skus.find((sku,i)=>skus.indexOf(sku)!==i);check(duplicate===undefined,'usage','Duplicate --sku: '+duplicate);return skus;
}
// Shared selection for rows, survey, gaps, listing-json and grid: one record per requested SKU, in --sku order.
async function loadSelection(args,{allowListings=true,refuseArchived=false}={}){
 check(Boolean(args['--export'])!==Boolean(args['--listings']),'usage','Use exactly one of --export FILE or --listings FILE');
 const skus=requestedSkus(args),wanted=new Set(skus);
 if(args['--listings']){
  check(allowListings,'planning_only_source','A get_listings JSON is a planning read only; build workbook grids from a verified MCP export (--export)');
  const bytes=await readFile(args['--listings']).catch(error=>fail('listings_unreadable','Saved get_listings JSON is unreadable: '+error.code));
  let body;try{body=JSON.parse(bytes.toString('utf8'));}catch{fail('listings_unreadable','Saved get_listings JSON is not JSON');}
  check(Array.isArray(body?.listings)&&Array.isArray(body?.missingSkus),'listings_unreadable','Saved get_listings JSON needs listings and missingSkus arrays');
  check(body.missingSkus.length===0,'sku_missing','get_listings reported missing SKUs: '+body.missingSkus.join(', '));
  const seen=new Map();
  for(const item of body.listings){
   check(item&&typeof item.sku==='string'&&typeof item.asin==='string'&&item.attributes&&typeof item.attributes==='object'&&!Array.isArray(item.attributes),'listings_unreadable','A get_listings entry lacks sku, asin or attributes');
   check(!seen.has(item.sku),'sku_duplicate','get_listings returned SKU more than once: '+item.sku);seen.set(item.sku,item);
  }
  const missing=skus.filter(sku=>!seen.has(sku)),extra=[...seen.keys()].filter(sku=>!wanted.has(sku));
  check(!missing.length&&!extra.length,'sku_coverage',`get_listings coverage differs from --sku${missing.length?'; missing: '+missing.join(', '):''}${extra.length?'; not requested: '+extra.join(', '):''}`);
  const pairs=new Set(body.listings.map(item=>item.seller_id+'/'+item.marketplace_id));
  check(pairs.size===1&&/^[A-Z0-9]+$/.test(body.listings[0].seller_id||'')&&/^[A-Z0-9]+$/.test(body.listings[0].marketplace_id||''),'account_mismatch','get_listings must cover exactly one valid seller/marketplace pair');
  const observedAt=(await stat(args['--listings'])).mtime.toISOString();
  const records=skus.map(sku=>{const item=seen.get(sku);return {sellerId:item.seller_id,marketplaceId:item.marketplace_id,sku,asin:item.asin,archived:null,versionId:null,productType:item.productType??null,attributes:item.attributes,blankAttributes:Array.isArray(item.blankAttributes)?item.blankAttributes:null,blankAttributesStatus:null};});
  return {transport:'mcp_get_listings',planning_only:true,tool:'flatfilepro_get_listings',arguments_sha256:argumentsSha({sellerId:records[0].sellerId,marketplaceId:records[0].marketplaceId,skus}),raw_sha256:createHash('sha256').update(bytes).digest('hex'),account:{seller_id:records[0].sellerId,marketplace_id:records[0].marketplaceId},observed_at:observedAt,source_id:'ffp-mcp-get-listings:'+basename(args['--listings']),records};
 }
 const opened=await openExport(args['--export'],record=>wanted.has(record.sku)),bySku=new Map();
 for(const record of opened.records)(bySku.get(record.sku)??bySku.set(record.sku,[]).get(record.sku)).push(record);
 const missing=skus.filter(sku=>!bySku.has(sku)),repeated=skus.filter(sku=>bySku.get(sku)?.length>1);
 check(!missing.length,'sku_missing','SKUs not in the export: '+missing.join(', '));
 check(!repeated.length,'sku_duplicate','SKUs repeated in the export: '+repeated.join(', '));
 const archived=skus.filter(sku=>bySku.get(sku)[0].archived===true);
 check(!refuseArchived||!archived.length,'sku_archived','Archived SKUs cannot be used: '+archived.join(', '));
 const {receipt}=opened;check(Number.isFinite(Date.parse(receipt.snapshotAt)),'receipt_invalid','Export receipt snapshotAt is not a timestamp');
 return {transport:'mcp_export',planning_only:false,tool:'flatfilepro_get_export_download',arguments_sha256:argumentsSha({jobId:receipt.jobId}),raw_sha256:receipt.sha256,account:{seller_id:receipt.sellerId,marketplace_id:receipt.marketplaceId},observed_at:receipt.snapshotAt,source_id:'ffp-mcp-export:'+receipt.fileName,export:exportMeta(receipt),receipt,
  records:skus.map(sku=>{const r=bySku.get(sku)[0];return {...r,archived:r.archived??null,versionId:r.versionId??null,productType:r.productType??null,blankAttributes:Array.isArray(r.blankAttributes)?r.blankAttributes:null,blankAttributesStatus:r.blankAttributesStatus??null};})};
}
function normalized(selection,record,options={}){
 const data={seller_id:record.sellerId,marketplace_id:record.marketplaceId,sku:record.sku,asin:record.asin,attributes:record.attributes,productType:record.productType??undefined,versionId:record.versionId??undefined,archived:record.archived??undefined};
 try{return normalizeListing(data,selection.account,{sku:record.sku,asin:record.asin},selection.observed_at,selection.source_id,options);}
 catch(error){fail('listing_unreadable',`SKU ${record.sku}: ${error.message}`);}
}
const sourceFields=selection=>({transport:selection.transport,planning_only:selection.planning_only,tool:selection.tool,arguments_sha256:selection.arguments_sha256,raw_sha256:selection.raw_sha256,...(selection.export?{export:selection.export}:{})});
const blankAnalysis=record=>Array.isArray(record.blankAttributes)&&record.blankAttributesStatus!=='SCHEMA_UNAVAILABLE';

export async function resolveTargets(args){
 check(args['--export'],'usage','--export FILE is required');
 const skus=args['--sku']||[],asins=args['--asin']||[];check(skus.length||asins.length,'usage','Give at least one --sku or --asin');
 const wantSku=new Set(skus),wantAsin=new Set(asins);
 const opened=await openExport(args['--export'],record=>wantSku.has(record.sku)||wantAsin.has(record.asin));
 const target=record=>({sku:record.sku,asin:record.asin,product_type:record.productType??null,parentage:firstValue(record.attributes,'parentage_level'),parent_sku:firstValue(record.attributes,'child_parent_sku_relationship','parent_sku')});
 const targets=[],seen=new Set(),excluded=new Map(),add=record=>{if(!seen.has(record.sku)){seen.add(record.sku);targets.push(target(record));}};
 for(const sku of skus){
  const matches=opened.records.filter(record=>record.sku===sku);
  check(matches.length===1,matches.length?'sku_duplicate':'sku_missing',`SKU ${sku} appears ${matches.length} times in the export; exactly one is required`);
  check(matches[0].archived!==true,'sku_archived',`SKU ${sku} is archived`);add(matches[0]);
 }
 for(const asin of asins){
  const matches=opened.records.filter(record=>record.asin===asin).sort((a,b)=>a.sku<b.sku?-1:a.sku>b.sku?1:0);
  for(const record of matches.filter(r=>r.archived===true))excluded.set(record.sku,{sku:record.sku,asin:record.asin});
  const live=matches.filter(record=>record.archived!==true);check(live.length,'asin_unavailable',`ASIN ${asin} has no non-archived SKU in the export`);live.forEach(add);
 }
 return {status:'resolved',source:'ffp-mcp-export',export:exportMeta(opened.receipt),seller_id:opened.receipt.sellerId,marketplace_id:opened.receipt.marketplaceId,targets,excluded_archived:[...excluded.values()]};
}

// ---- grid ----
export function blankPathToExport(path){
 const match=/^([A-Za-z0-9_]+)((?:\[\d+\]|\.[A-Za-z0-9_]+)*)$/.exec(String(path));if(!match)return null;
 let header=match[1],afterIndex=false;
 for(const token of match[2].match(/\[\d+\]|\.[A-Za-z0-9_]+/g)||[]){
  if(token.startsWith('[')){header+=`__${Number(token.slice(1,-1))+1}__`;afterIndex=true;}else{header+=(afterIndex?'':'_')+token.slice(1);afterIndex=false;}
 }
 return header;
}
const csvCell=value=>/[",\r\n]/.test(value)||/^\s|\s$/.test(value)?'"'+value.replace(/"/g,'""')+'"':value;
export function parseCsv(source){
 const rows=[];let row=[],cell='',quoted=false,i=0;
 while(i<source.length){
  const c=source[i];
  if(quoted){if(c==='"'){if(source[i+1]==='"'){cell+='"';i+=2;continue;}quoted=false;i++;continue;}cell+=c;i++;continue;}
  if(c==='"'&&cell===''){quoted=true;i++;continue;}
  if(c===','){row.push(cell);cell='';i++;continue;}
  if(c==='\r'&&source[i+1]==='\n'){row.push(cell);rows.push(row);row=[];cell='';i+=2;continue;}
  if(c==='\n'){row.push(cell);rows.push(row);row=[];cell='';i++;continue;}
  cell+=c;i++;
 }
 if(cell!==''||row.length)row.push(cell),rows.push(row);
 return rows;
}
export async function grid(args,deps){
 check(args['--out']&&/\.csv$/i.test(args['--out']),'usage','--out PATH.csv is required');
 const selection=await loadSelection(args,{allowListings:false,refuseArchived:true});
 const headers=['sku'],index=new Set(headers),flat=selection.records.map(record=>{
  let values;try{values=flattenAttributes(record.attributes,{style:'export'});}catch(error){fail('listing_unreadable',`SKU ${record.sku}: ${error.message}`);}
  for(const header of Object.keys(values))if(!index.has(header)){index.add(header);headers.push(header);}return values;
 });
 const blankColumns=[],blankUnavailable=[],unconvertible=[],bare=new Set();
 if(args['--blank-columns']){
  // A bare name lacks the occurrence and leaf key, so it is no upload header; guessing __1__value would defeat prepare's header check.
  for(const record of selection.records){
   if(record.blankAttributesStatus!=='AVAILABLE'||!Array.isArray(record.blankAttributes)){blankUnavailable.push(record.sku);continue;}
   for(const path of record.blankAttributes){
    const header=blankPathToExport(path);if(!header){unconvertible.push(path);continue;}
    if(!/\[\d+\]/.test(path)){bare.add(path);continue;}
    if(!/\.[A-Za-z0-9_]+$/.test(path)){unconvertible.push(path);continue;}
    if(!index.has(header)){index.add(header);headers.push(header);blankColumns.push({path,header});}
   }
  }
 }
 const added=[];
 for(const header of args['--add-column']||[]){
  // The header comes from the target template; the export only proves the attribute is empty today.
  const attribute=/^([a-z][a-z0-9_]*?)__[1-9]\d*__[A-Za-z0-9_]+$/.exec(header)?.[1];
  check(attribute,'usage','--add-column needs an export-spelled header such as generic_keyword__1__value: '+header);
  check(!index.has(header),'column_present','Column already in the grid: '+header);
  for(const record of selection.records){
   check(record.blankAttributesStatus==='AVAILABLE'&&Array.isArray(record.blankAttributes),'blank_status_unknown',`SKU ${record.sku}: blank analysis unavailable, cannot prove ${attribute} is empty`);
   check(!Object.hasOwn(record.attributes||{},attribute)&&record.blankAttributes.includes(attribute),'attribute_not_blank',`SKU ${record.sku}: ${attribute} is not a blank attribute; use its existing column`);
  }
  index.add(header);headers.push(header);added.push({header,attribute});
 }
 const table=[headers,...selection.records.map((record,i)=>headers.map(header=>header==='sku'?record.sku:text(flat[i][header])))];
 const out=resolve(args['--out']),provenancePath=out+'.provenance.json',created=[];
 try{
  await mkdir(dirname(out),{recursive:true});
  const csv=table.map(row=>row.map(csvCell).join(',')).join('\r\n')+'\r\n';
  await writeFile(out,csv,{flag:'wx'}).catch(error=>fail('grid_exists',error.code==='EEXIST'?'Refusing to overwrite '+out:'Cannot write '+out+': '+error.code));created.push(out);
  const reread=parseCsv(await readFile(out,'utf8'));
  check(reread.length===table.length,'grid_verify_failed',`Grid has ${reread.length-1} data rows; expected ${table.length-1}`);
  table.forEach((row,r)=>{check(reread[r].length===row.length,'grid_verify_failed',`Grid row ${r} has ${reread[r].length} cells; expected ${row.length}`);row.forEach((value,c)=>check(reread[r][c]===value,'grid_verify_failed',`Grid value differs at row ${r}, column ${headers[c]}`));});
  const csvSha=createHash('sha256').update(csv).digest('hex');
  const provenance={source:'ffp-mcp-export',export:selection.export,seller_id:selection.account.seller_id,marketplace_id:selection.account.marketplace_id,skus:selection.records.map(r=>r.sku),header_count:headers.length,header_style:'ffp-export',generated_at:new Date(deps.now()).toISOString(),csv_sha256:csvSha,
   ...(added.length?{added_columns:added,added_columns_note:'Empty columns added under template headers for attributes FlatFilePro lists as blank; confirm each header against the target template before mapping.'}:{}),
   ...(args['--blank-columns']?{blank_columns:blankColumns,blank_columns_unavailable:blankUnavailable,blank_paths_unconverted:unconvertible,blank_attributes_bare:[...bare],blank_columns_note:'A change that names a blank column writes that header into the upload workbook; confirm it against the target template first. blank_attributes_bare are blank attributes without an occurrence index or leaf key: they get no column, and filling one needs the technical header from the target template.'}:{})};
  await writeFile(provenancePath,JSON.stringify(provenance,null,1)+'\n',{flag:'wx'}).catch(error=>fail('grid_exists',error.code==='EEXIST'?'Refusing to overwrite '+provenancePath:'Cannot write '+provenancePath+': '+error.code));created.push(provenancePath);
  return {status:'written',path:out,provenance_path:provenancePath,rows:table.length-1,header_count:headers.length,csv_sha256:csvSha,verified:true,...(added.length?{added_columns:added}:{}),...(args['--blank-columns']?{blank_columns:blankColumns.length,blank_columns_unavailable:blankUnavailable,blank_attributes_bare:[...bare]}:{})};
 }catch(error){for(const file of created.reverse())await rm(file,{force:true});throw error;}
}

// ---- planning reads ----
export async function rows(args){
 const selection=await loadSelection(args),records=selection.records.map(record=>normalized(selection,record,{nested:true}));
 return {schema_version:1,source_kind:'flatfilepro_mcp_listing_read',status:'collected',...sourceFields(selection),account:selection.account,observed_at:selection.observed_at,source_id:selection.source_id,
  rows:Object.fromEntries(records.map(r=>[r.sku,r.row])),
  records:selection.records.map(record=>({sku:record.sku,asin:record.asin,product_type:record.productType,archived:record.archived,version_id:record.versionId,blank_attributes:record.blankAttributes,blank_attributes_status:record.blankAttributesStatus}))};
}
function slotsOf(row){return Object.fromEntries(SLOTS.map(([slot,field])=>[slot,text(row[field+'.0.media_location'])]));}
export async function survey(args){
 const format=args['--format']||'json';check(['json','csv','md'].includes(format),'usage','--format must be json, csv or md');
 const selection=await loadSelection(args);
 const table=selection.records.map(record=>{const row=normalized(selection,record).row,slots=slotsOf(row);
  return {sku:record.sku,asin:record.asin,parentage:text(row['parentage_level.0.value']),parent_sku:text(row['child_parent_sku_relationship.0.parent_sku']),archived:record.archived,...slots,free_slots:SLOTS.filter(([slot])=>slot.startsWith('PT')&&!slots[slot]).map(([slot])=>slot)};});
 const result={status:'surveyed',...sourceFields(selection),account:selection.account,observed_at:selection.observed_at,skus:table};
 if(format==='json')return result;
 const columns=['sku','asin','parentage','parent_sku','archived',...SLOTS.map(([slot])=>slot),'free_slots'],cell=(row,c)=>c==='free_slots'?row[c].join(' '):text(row[c]);
 if(format==='csv')return {text:[columns.join(','),...table.map(row=>columns.map(c=>csvCell(cell(row,c))).join(','))].join('\n')+'\n'};
 const md=value=>value.replace(/\|/g,'\\|');
 return {text:`${selection.planning_only?'Planning read only (get_listings); not upload or baseline evidence.\n\n':''}| ${columns.join(' | ')} |\n|${columns.map(()=>' --- ').join('|')}|\n`+table.map(row=>'| '+columns.map(c=>md(cell(row,c))).join(' | ')+' |').join('\n')+'\n'};
}
const topName=value=>(/^([A-Za-z0-9_]+?)(?:__\d+__|\.|\[|$)/.exec(value.trim())||[])[1];
function companionGaps(record,attribute){
 const values=record.attributes[attribute];if(!Array.isArray(values)||!values.length)return {blank:true,gaps:[]};
 const gaps=[];
 values.forEach((item,index)=>{
  if(!item||typeof item!=='object')return;
  if(COMPANIONS[attribute]){for(const path of COMPANIONS[attribute])if(!filled(path.reduce((value,key)=>value?.[key],item)))gaps.push(`${attribute}[${index}].${path.join('.')}`);return;}
  for(const [dimension,value] of Object.entries(item))if(value&&typeof value==='object'&&!Array.isArray(value))for(const key of ['value','unit'])if(!filled(value[key]))gaps.push(`${attribute}[${index}].${dimension}.${key}`);
 });
 return {blank:false,gaps};
}
export async function gaps(args){
 const touched=[...new Set((args['--touch']||'').split(',').map(x=>x.trim()).filter(Boolean).map(value=>{const name=topName(value);check(name,'usage','Unreadable --touch attribute: '+value);return name;}))];
 const selection=await loadSelection(args);
 const checked=touched.filter(attribute=>COMPANIONS[attribute]||/_dimensions$/.test(attribute)),unchecked=touched.filter(attribute=>!checked.includes(attribute));
 const skus=selection.records.map(record=>{
  const row=normalized(selection,record).row,slots=slotsOf(row),companion=[],blankTouched=[];
  for(const attribute of checked){const result=companionGaps(record,attribute);if(result.blank)blankTouched.push(attribute);companion.push(...result.gaps);}
  const candidates=blankAnalysis(record)
   ?{status:'available',attributes:CANDIDATE_ATTRIBUTES.filter(name=>record.blankAttributes.includes(name)&&!(record.attributes[name]||[]).length)}
   :{status:'unknown',attributes:[],reason:record.blankAttributesStatus==='SCHEMA_UNAVAILABLE'?'blank-attribute schema unavailable':'blankAttributes not provided'};
  return {sku:record.sku,asin:record.asin,archived:record.archived,companion_gaps:companion,touched_blank:blankTouched,candidates,free_image_slots:SLOTS.filter(([slot])=>slot.startsWith('PT')&&!slots[slot]).map(([slot])=>slot)};
 });
 const blocked=skus.some(sku=>sku.companion_gaps.length);
 return {status:blocked?'blocked':'ok',...(blocked?{reason:'companion_gaps',message:'Touched attribute groups have saved members missing; supply every listed member in the change or leave the group untouched'}:{}),
  ...sourceFields(selection),account:selection.account,observed_at:selection.observed_at,touched,companion_checked:checked,companion_unchecked:unchecked,
  candidates_note:'Suggestions only: fill from the product label or approved source-of-truth evidence; required vs optional comes from the target template. Unknown means the blank analysis is incomplete.',
  touched_blank_note:'A touched attribute that is blank today needs every companion member in the change (unit_count: value and type.value; weights: value and unit; dimensions: value and unit per dimension; nutritional_info: serving_quantity and serving_unit).',
  skus,exit_code:blocked?3:0};
}
export async function listingJson(args){
 const selection=await loadSelection(args),values=(attributes,field)=>(Array.isArray(attributes[field])?attributes[field]:[]).filter(item=>item&&(!item.marketplace_id||item.marketplace_id===selection.account.marketplace_id)).map(item=>text(item.value)).filter(value=>value.trim()!=='');
 return {source:'ffp-saved-backend',note:'FlatFilePro saved backend copy, not the live PDP',...sourceFields(selection),account:selection.account,observed_at:selection.observed_at,
  listings:selection.records.map(({sku,asin,attributes})=>({asin,sku,title:firstValue(attributes,'item_name'),bullets:values(attributes,'bullet_point'),description:firstValue(attributes,'product_description'),item_highlights:firstValue(attributes,'title_differentiation'),backend:values(attributes,'generic_keyword').join(' ')}))};
}

// ---- entry point ----
const readAll=async stream=>{const chunks=[];for await(const chunk of stream)chunks.push(chunk);return Buffer.concat(chunks).toString('utf8');};
export async function main(argv,deps={}){
 const secrets=[],options={now:deps.now||Date.now,fetch:deps.fetch||globalThis.fetch,artifactctl:deps.artifactctl||defaultArtifactctl,readStdin:deps.readStdin||(()=>readAll(process.stdin)),secrets};
 let result,code=0;
 try{
  const args=parseArgs(argv);
  const handlers={binding,'fetch-export':fetchExport,resolve:resolveTargets,grid,rows,survey,gaps,'listing-json':listingJson};
  result=await handlers[args.command](args,options);
  if(args.command==='gaps'){code=result.exit_code;delete result.exit_code;}
 }catch(error){
  result={status:'blocked',reason:error instanceof Blocked?error.reason:'unexpected',message:redact(error.message),...(error.extra||{})};code=2;
 }
 let stdout=result.text??JSON.stringify(result);
 // Belt and braces: the bearer URL and its query never leave this process.
 for(const secret of secrets.filter(value=>typeof value==='string'&&value.length>8))stdout=stdout.split(secret).join('[redacted-url]');
 return {code,stdout:stdout.endsWith('\n')?stdout:stdout+'\n'};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const {code,stdout}=await main(process.argv.slice(2));process.stdout.write(stdout);process.exitCode=code;}
