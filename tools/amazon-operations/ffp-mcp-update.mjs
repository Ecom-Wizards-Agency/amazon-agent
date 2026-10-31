/** Local build, gate, ledger and verify tool for FlatFilePro MCP V2 direct listing updates (attended only). */
// This tool never calls FlatFilePro or Amazon and never writes a listing. The agent calls the connector
// tools (get_listings_item_from_amazon, get_product_type_fields, update_listing_on_amazon,
// get_listing_update_status) and passes their saved results here. This tool builds the exact update
// arguments per SKU, binds the operator's approval to the batch SHA-256, hands out one payload at a time,
// keeps an append-only ledger and diffs live after-reads against the payloads.
// An update replaces the whole array of every supplied attribute, so untouched elements in a payload are
// carried content: they may only come from a verified export or a get_listings copy that agrees with live.
// A live read without kept_attributes must contain every touched attribute; list an absent one in
// kept_attributes to assert it is absent on Amazon. A change that equals the live value is refused (no_op_change).
//
// node tools/amazon-operations/ffp-mcp-update.mjs <subcommand>
//   build --seller-id S --marketplace-id M --scope seo|attributes|images (--changes CSV | --images FILE)
//         --live FILE... [--export FILE | --listings FILE] [--fields FILE]... [--allow-free-text ATTR]...
//         --out DIR [--ledger-root DIR] [--register-run RUN_ID]
//   approve --batch DIR --approved-by NAME [--main-review FILE]   approval expires after APPROVAL_HOURS; approve again then
//   next --batch DIR --live FILE      FILE: a fresh get_listings_item_from_amazon read of the offered SKU, taken
//                                     right before this write; refused (stale_base) unless it equals the build's before-read
//   record --batch DIR (--index N | --sku S) [--no-response --note TEXT]  < update_listing_on_amazon response on STDIN
//                                     a saved responses/NNN.json without a ledger record is recovered (recovered:true)
//   status --batch DIR (--index N | --sku S)                              < get_listing_update_status result on STDIN
//   verify --batch DIR (--index N | --sku S) --live FILE [--pixels FILE]...  pixel files from image_intake.py compare
//   pending --root DIR
//   close --batch DIR (--index N | --sku S) --reason TEXT --approved-by NAME [--landed]   an unsubmitted item is closed as void;
//     --landed records the operator's finding that a submitted item landed correctly, which releases the first-item hold
// verify states, first that applies: mismatch > update_failed > pixels_mismatch > issues_new_error > not_yet >
// landed_pixels_unchecked > verified (status SUCCEEDED) | landed_status_pending.
// JSON on stdout. Exit 0 ok, 2 blocked or held {status,reason,message}, 3 verify state other than verified,
// landed_status_pending or landed_pixels_unchecked. Only verified and landed_status_pending, or a close --landed, release
// the hold on the first item. Everything except pending is attended_only.
import {readFile,writeFile,appendFile,mkdir,rm,stat,readdir} from 'node:fs/promises';
import {dirname,join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
import {Blocked,redact,openExport,parseCsv,register,defaultArtifactctl} from './ffp-mcp.mjs';

const fail=(reason,message,extra)=>{throw new Blocked(reason,message,extra);};
const check=(ok,reason,message,extra)=>{if(!ok)fail(reason,message,extra);};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const iso=ms=>new Date(ms).toISOString();
const isObj=value=>value!==null&&typeof value==='object'&&!Array.isArray(value);
const clone=value=>value===undefined?undefined:JSON.parse(JSON.stringify(value));
const pad=index=>String(index).padStart(3,'0');
const exists=async path=>{try{return await stat(path);}catch(error){if(error.code==='ENOENT')return null;throw error;}};
const json1=value=>JSON.stringify(value,null,1)+'\n';

export const SEO_FIELDS=new Set(['item_name','bullet_point','product_description','generic_keyword','title_differentiation']);
export const LOCATORS=Object.freeze(['main_product_image_locator',...Array.from({length:9},(_,i)=>`other_product_image_locator_${i+1}`),'swatch_product_image_locator']);
const SLOT_ATTR=Object.fromEntries([['MAIN','main_product_image_locator'],...Array.from({length:9},(_,i)=>[`PT0${i+1}`,`other_product_image_locator_${i+1}`])]);
const LOCATOR_RE=/^(main|other|swatch)_product_image_locator(_\d+)?$/;
const ANY_IMAGE_RE=/_image_locator(_\d+)?$/;
const OFFER_RE=/^(purchasable_offer|list_price|uvp_list_price|fulfillment_availability|merchant_shipping_group|condition_type|condition_note|max_order_quantity|product_tax_code|skip_offer|merchant_release_date)|_seller_allowed_price$|_offer_image_locator(_\d+)?$/;
const SELECTORS=new Set(['marketplace_id','language_tag']);
const NOT_ATTRIBUTES=['parentAsins','childAsins'];
const TOOL='flatfilepro_update_listing_on_amazon';
const AMAZON_IMAGE='https://m.media-amazon.com/';
const RELEASES_HOLD=new Set(['verified','landed_status_pending']);
const PASSING=new Set(['verified','landed_status_pending','landed_pixels_unchecked']);
const FAILED_RE=/^(FAILED|FAILURE|REJECTED|CANCELLED|CANCELED|ERROR|PARTIALLY_FAILED|PARTIAL_FAILURE)$/i;
export const APPROVAL_HOURS=12;
// Keep in step with image_intake.py; a pixel file compared with looser thresholds is refused.
export const PIXEL_THRESHOLDS=Object.freeze({max_dhash:24,max_aspect_delta:0.02,max_color_delta:12});

// ---- canonical comparison ----
// Live reads return most numbers and booleans as strings and reorder object keys; compare text, not bytes.
// Strings stay exact after trim ('00123' is not '123'); only trailing fractional zeros go ('36.00' is '36').
export function canon(value){
 if(Array.isArray(value))return value.map(canon);
 if(isObj(value))return Object.fromEntries(Object.keys(value).filter(key=>value[key]!==undefined).sort().map(key=>[key,canon(value[key])]));
 if(value===undefined||value===null)return null;
 if(typeof value==='boolean'||typeof value==='number')return String(value);
 const text=String(value).trim();
 return /^-?\d+\.\d+$/.test(text)?text.replace(/0+$/,'').replace(/\.$/,''):text;
}
export const same=(a,b)=>JSON.stringify(canon(a))===JSON.stringify(canon(b));

// ---- arguments ----
const FLAGS={
 build:{value:['--seller-id','--marketplace-id','--scope','--changes','--images','--export','--listings','--out','--ledger-root','--register-run'],repeat:['--live','--fields','--allow-free-text']},
 approve:{value:['--batch','--approved-by','--main-review']},
 next:{value:['--batch','--live']},
 record:{value:['--batch','--index','--sku','--note'],bool:['--no-response']},
 status:{value:['--batch','--index','--sku']},
 verify:{value:['--batch','--index','--sku','--live'],repeat:['--pixels']},
 pending:{value:['--root']},
 close:{value:['--batch','--index','--sku','--reason','--approved-by'],bool:['--landed']},
};
export function parseArgs(argv){
 const [command,...rest]=argv;check(Object.hasOwn(FLAGS,command||''),'usage','Usage: ffp-mcp-update.mjs <'+Object.keys(FLAGS).join('|')+'> [flags]');
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
const attended=deps=>check(!deps.env.WIZARDS_AI_MODE,'attended_only','Direct FlatFilePro writes are attended only; Grimoire uses the workbook pipeline');

// ---- saved MCP results ----
const unwrap=body=>Array.isArray(body)&&body.length===1&&body[0]?.type==='text'&&typeof body[0].text==='string'?JSON.parse(body[0].text):body;
async function readSaved(file,reason,label){
 let bytes;try{bytes=await readFile(file);}catch(error){fail(reason,`${label} is unreadable (${error.code||'error'}): ${file}`);}
 let body;try{body=unwrap(JSON.parse(bytes.toString('utf8')));}catch{fail(reason,`${label} is not JSON: ${file}`);}
 return {path:resolve(file),sha256:sha(bytes),body};
}
const bodyOf=raw=>{try{return unwrap(JSON.parse(raw));}catch{return null;}};
async function readLive(file,bind){
 const read=await readSaved(file,'live_unreadable','Live read'),b=read.body;
 check(isObj(b)&&b.source==='AMAZON_SP_API'&&isObj(b.item),'live_mismatch',`${file}: not a saved get_listings_item_from_amazon result (source AMAZON_SP_API)`);
 check(b.sellerId===bind.seller&&b.marketplaceId===bind.marketplace,'live_mismatch',`${file}: the live read is for another seller or marketplace`);
 check(typeof b.item.sku==='string'&&b.item.sku!=='','live_mismatch',`${file}: the live read has no item.sku`);
 const attributes=b.item.attributes??{};check(isObj(attributes),'live_mismatch',`${file}: item.attributes is not an object`);
 const kept=b.kept_attributes;check(kept===undefined||Array.isArray(kept)&&kept.every(name=>typeof name==='string'),'live_mismatch',`${file}: kept_attributes must be a list of attribute names`);
 const summaries=Array.isArray(b.item.summaries)?b.item.summaries:[];
 return {...read,sku:b.item.sku,attributes,kept:kept?new Set(kept):null,summary:summaries.find(s=>s?.marketplaceId===bind.marketplace)??summaries[0]??null,issues:Array.isArray(b.item.issues)?b.item.issues:[]};
}
const requireKept=(live,names)=>{
 if(!live.kept)return;const missing=names.filter(name=>!live.kept.has(name));
 check(!missing.length,'live_incomplete',`Live read for ${live.sku} was trimmed without ${missing.join(', ')}; keep every touched attribute and every image locator`);
};
// A read without kept_attributes may have been trimmed, so a touched attribute it lacks is not proof of absence.
function requireComplete(live,touched){
 requireKept(live,[...new Set([...touched,...LOCATORS])]);
 const absent=live.kept?[]:touched.filter(attr=>!Object.hasOwn(live.attributes,attr));
 check(!absent.length,'live_incomplete',`Live read for ${live.sku} has no ${absent.join(', ')}; list it in kept_attributes to assert it is absent on Amazon`);
}
const issueKey=issue=>JSON.stringify([String(issue?.code??''),[...(Array.isArray(issue?.attributeNames)?issue.attributeNames:[])].map(String).sort(),String(issue?.severity??'')]);
const cleanIssue=issue=>({code:issue?.code??null,severity:issue?.severity??null,attributeNames:Array.isArray(issue?.attributeNames)?issue.attributeNames:[],categories:Array.isArray(issue?.categories)?issue.categories:[],message:redact(issue?.message??'')});
const stripNonAttributes=attributes=>Object.fromEntries(Object.entries(attributes||{}).filter(([key])=>!NOT_ATTRIBUTES.includes(key)));

// ---- field rules ----
function category(attr){
 if(/relationship/i.test(attr)||['parentage_level','variation_theme',...NOT_ATTRIBUTES].includes(attr))return 'relationship_field';
 if(OFFER_RE.test(attr))return 'offer_field';
 if(['brand','externally_assigned_product_identifier','merchant_suggested_asin'].includes(attr))return 'identity_field';
 return null;
}
function scopeCheck(attr,scope,where){
 const refused=category(attr);
 check(!refused,refused,`${where}: ${attr} is ${{relationship_field:'a relationship',offer_field:'an offer',identity_field:'an identity'}[refused]} field; direct updates never touch it, use the workbook route`);
 check(attr!=='swatch_product_image_locator','scope_violation',`${where}: the swatch image (SWCH) is outside direct updates`);
 if(scope==='seo')check(SEO_FIELDS.has(attr),'scope_violation',`${where}: ${attr} is not an SEO field (${[...SEO_FIELDS].join(', ')}); use --scope attributes`);
 if(scope==='attributes')check(!ANY_IMAGE_RE.test(attr),'scope_violation',`${where}: ${attr} is an image locator; use --scope images`);
}
function parsePath(text,where){
 check(!/__\d+__/.test(text),'usage',`${where}: ${text} is export spelling; use canonical attr.N.key spelling counted from 0 (bullet_point.2.value, unit_count.0.type.value)`);
 const match=/^([A-Za-z][A-Za-z0-9_]*)\.(\d+)((?:\.[A-Za-z0-9_]+)+)$/.exec(text);
 check(match,'usage',`${where}: attribute "${text}" is not canonical attr.N.key[.key...] (bullet_point.2.value); whole-element JSON is not supported`);
 const keys=match[3].slice(1).split('.').map(part=>/^\d+$/.test(part)?Number(part):part);
 check(typeof keys[0]==='string','usage',`${where}: attribute "${text}" needs a key after the element index`);
 return {attr:match[1],index:Number(match[2]),keys,text:[match[1],Number(match[2]),...keys].join('.')};
}
const isDef=value=>isObj(value)&&isObj(value.meta);
const literals=def=>isDef(def)?Object.entries(def).filter(([key,value])=>key!=='meta'&&!isObj(value)&&!Array.isArray(value)):[];
function newObject(def,sample){
 const object=Object.fromEntries(literals(def).map(([key,value])=>[key,value]));
 if(isObj(sample))for(const key of SELECTORS)if(sample[key]!==undefined&&object[key]===undefined)object[key]=sample[key];
 return object;
}
function typed(value,type,where){
 if(type==='number'||type==='integer'){
  const text=value.trim(),number=Number(text);
  check(text!==''&&Number.isFinite(number)&&(type==='number'||Number.isInteger(number)),'invalid_value',`${where}: "${value}" is not ${type==='integer'?'an integer':'a number'}`);
  return number;
 }
 if(type==='boolean'){const text=value.trim();check(text==='true'||text==='false','invalid_value',`${where}: "${value}" is not true or false`);return text==='true';}
 return value;
}
const byPath=(a,b)=>{
 const x=[a.path.index,...a.path.keys],y=[b.path.index,...b.path.keys];
 for(let i=0;i<Math.min(x.length,y.length);i++){
  if(x[i]===y[i])continue;
  if(typeof x[i]==='number'&&typeof y[i]==='number')return x[i]-y[i];
  if(typeof x[i]!==typeof y[i])return typeof x[i]==='number'?-1:1;
  return x[i]<y[i]?-1:1;
 }
 return x.length-y.length;
};
// Apply one attribute's changes to a clone of its starting array. Returns the payload array and which paths changed.
function buildAttribute({sku,attr,changes,origin,def,marketplace,allowFree}){
 check(origin===undefined||Array.isArray(origin),'structure_unknown',`${sku}: ${attr} is not an array in the base`);
 check(origin!==undefined||def,'structure_unknown',`${sku}: ${attr} is absent from the base and from Amazon; save get_product_type_fields for its product type`);
 const array=clone(origin)??[],element0=origin?.[0],setPaths=new Set(),newElements=new Set(),warnings=[];
 for(const change of [...changes].sort(byPath)){
  const {index,keys,text}=change.path,where=`${sku} ${text}`;
  check(index<=array.length,'index_gap',`${where}: element ${index} skips past the ${array.length} existing elements; indices must be contiguous`);
  if(index===array.length){
   check(isObj(element0)||isDef(def),'structure_unknown',`${where}: a new element needs element 0 of ${attr} or its field definition`);
   const element=newObject(def,element0);
   if(def?.marketplace_id!==undefined||element0?.marketplace_id!==undefined)element.marketplace_id=marketplace;
   array.push(element);newElements.add(index);
  }
  let node=array[index],d=def,sample=element0;
  check(isObj(node),'invalid_value',`${where}: element ${index} is not an object`);
  keys.forEach((key,k)=>{
   const last=k===keys.length-1,numeric=typeof key==='number';
   const nd=numeric?d:(isDef(d)?d[key]:undefined),ns=numeric?(Array.isArray(sample)?sample[key]??sample[0]:undefined):(isObj(sample)?sample[key]:undefined);
   if(numeric){check(Array.isArray(node),'invalid_value',`${where}: ${key} indexes a value that is not a list`);check(key<=node.length,'index_gap',`${where}: index ${key} skips past ${node.length} entries`);}
   else check(isObj(node),'invalid_value',`${where}: ${key} is under a value that is not an object`);
   const present=numeric?key<node.length:Object.hasOwn(node,key);
   check(present||nd!==undefined||ns!==undefined||(numeric&&node.length>0),'structure_unknown',`${where}: ${key} is new and neither element 0 nor the field definition shows it`);
   if(!last){
    if(!present)node[key]=typeof keys[k+1]==='number'?[]:newObject(nd,ns);
    node=node[key];d=nd;sample=ns;return;
   }
   const old=present?node[key]:undefined;
   check(!isObj(old)&&!Array.isArray(old),'invalid_value',`${where}: names an object, not a value`);
   const leaf=isDef(nd)?nd.meta:null;
   check(!leaf||leaf.type!=='object'&&!(leaf.type==='array'&&!numeric),'invalid_value',`${where}: the field definition says ${leaf?.type}, not a value`);
   let type=leaf&&leaf.type!=='array'?leaf.type:undefined;
   if(!type&&present)type=typeof old==='number'?'number':typeof old==='boolean'?'boolean':'string';
   const value=typed(change.value,type,where);
   if(typeof value==='string'&&Number.isInteger(leaf?.maxLength))check([...value].length<=leaf.maxLength,'max_length',`${where}: ${[...value].length} characters; the field allows ${leaf.maxLength}`);
   if(Array.isArray(leaf?.selectOptions)){
    const options=leaf.selectOptions.map(option=>String(Array.isArray(option)?option[0]:option));
    if(!options.includes(String(value))){
     check(allowFree.has(attr),'free_text_unapproved',`${where}: "${value}" is not one of the suggested values (${options.join(', ')}); pass --allow-free-text ${attr} after the operator accepts free text`);
     warnings.push({code:'not_in_select_options',attribute:attr,path:text,value:String(value),options});
    }
   }
   node[key]=value;setPaths.add([index,...keys].join('.'));
  });
 }
 const max=def?.meta?.maxUniqueItems;
 if(Number.isInteger(max))check(array.length<=max,'max_items',`${sku} ${attr}: ${array.length} elements; the field allows ${max}`);
 return {array,setPaths,newElements,warnings};
}
function leaves(value,path=[],out=[]){
 if(Array.isArray(value))value.forEach((item,i)=>leaves(item,[...path,i],out));
 else if(isObj(value))for(const [key,item] of Object.entries(value))leaves(item,[...path,key],out);
 else out.push([path.join('.'),value,path[path.length-1]]);
 return out;
}
const carriedPaths=(array,setPaths)=>leaves(array).filter(([path,,key])=>!SELECTORS.has(key)&&!setPaths.has(path)).map(([path])=>path);

// ---- inputs ----
async function readChanges(file,scope){
 let bytes;try{bytes=await readFile(file);}catch(error){fail('usage',`Changes CSV is unreadable (${error.code}): ${file}`);}
 const table=parseCsv(bytes.toString('utf8').replace(/^\uFEFF/,'')),header=(table[0]||[]).map(cell=>cell.trim());
 check(header.length===3&&['sku','attribute','value'].every(name=>header.includes(name)),'usage','Changes CSV needs exactly the columns sku, attribute, value');
 const col=Object.fromEntries(header.map((name,i)=>[name,i])),rows=[];
 table.slice(1).forEach((cells,i)=>{
  const where=`Changes row ${i+2}`;if(cells.length===1&&cells[0]==='')return;
  check(cells.length===3,'usage',`${where} has ${cells.length} cells; expected 3`);
  const sku=cells[col.sku],path=parsePath(cells[col.attribute].trim(),where),value=cells[col.value];
  check(sku.trim()!=='','usage',`${where} has no sku`);
  scopeCheck(path.attr,scope,where);
  check(value.trim()!=='','empty_value',`${where}: ${sku} ${path.text} is empty; clearing a value is a workbook-route change`);
  rows.push({sku,attr:path.attr,path,value,key:path.text});
 });
 check(rows.length,'usage','Changes CSV has no rows');
 return {kind:'changes',path:resolve(file),sha256:sha(bytes),rows};
}
async function readImages(file){
 const read=await readSaved(file,'usage','Images file');
 check(Array.isArray(read.body)&&read.body.length,'usage','Images file must be the image_intake.py publish list [{sku, slot, artifact:{path, sha256}, url}]');
 const rows=read.body.map((entry,i)=>{
  const where=`Image entry ${i}`;
  check(isObj(entry)&&typeof entry.sku==='string'&&entry.sku.trim()!==''&&typeof entry.slot==='string','usage',`${where} needs sku and slot`);
  check(entry.slot!=='SWCH','scope_violation',`${where}: the swatch image (SWCH) is outside direct updates`);
  check(Object.hasOwn(SLOT_ATTR,entry.slot),'invalid_value',`${where}: slot must be MAIN or PT01..PT09`);
  check(isObj(entry.artifact)&&/^[a-f0-9]{64}$/.test(entry.artifact.sha256||''),'invalid_value',`${where}: artifact.sha256 must be a lowercase SHA-256`);
  check(typeof entry.url==='string'&&entry.url.trim()!=='','empty_value',`${where}: url is empty`);
  let ok=false;try{ok=entry.url.startsWith('https://')&&new URL(entry.url).protocol==='https:';}catch{}
  check(ok,'invalid_value',`${where}: url must be an https:// URL`);
  // cloudinary_assets.publish names the hosted file after the PNG's SHA-256, which binds the URL to the reviewed hash.
  const url=new URL(entry.url);
  check(url.hostname==='res.cloudinary.com'&&url.pathname.endsWith('/'+entry.artifact.sha256+'.png'),'invalid_value',`${where}: url must be the res.cloudinary.com URL from image_intake.py publish ending in /${entry.artifact.sha256}.png`);
  return {sku:entry.sku,attr:SLOT_ATTR[entry.slot],slot:entry.slot,sha256:entry.artifact.sha256,url:entry.url,key:entry.slot};
 });
 return {kind:'images',path:read.path,sha256:read.sha256,rows};
}
async function readBase(args,bind,skus){
 const wanted=new Set(skus),records=new Map();
 if(args['--export']){
  const opened=await openExport(args['--export'],record=>wanted.has(record.sku));
  check(opened.receipt.sellerId===bind.seller&&opened.receipt.marketplaceId===bind.marketplace,'account_mismatch','The export belongs to another seller or marketplace');
  for(const record of opened.records){check(!records.has(record.sku),'sku_duplicate','SKU repeated in the export: '+record.sku);records.set(record.sku,record);}
  const missing=skus.filter(sku=>!records.has(sku));check(!missing.length,'sku_missing','SKUs not in the export: '+missing.join(', '));
  const archived=skus.filter(sku=>records.get(sku).archived===true);check(!archived.length,'sku_archived','Archived SKUs cannot be updated: '+archived.join(', '));
  return {kind:'export',path:opened.path,sha256:opened.receipt.sha256,records};
 }
 const read=await readSaved(args['--listings'],'listings_unreadable','Saved get_listings JSON');
 check(Array.isArray(read.body?.listings)&&Array.isArray(read.body?.missingSkus),'listings_unreadable','Saved get_listings JSON needs listings and missingSkus arrays');
 check(read.body.missingSkus.length===0,'sku_missing','get_listings reported missing SKUs: '+read.body.missingSkus.join(', '));
 for(const item of read.body.listings){
  check(isObj(item)&&typeof item.sku==='string'&&isObj(item.attributes),'listings_unreadable','A get_listings entry lacks sku or attributes');
  check(item.seller_id===bind.seller&&item.marketplace_id===bind.marketplace,'account_mismatch',`get_listings entry ${item.sku} belongs to another seller or marketplace`);
  check(!records.has(item.sku),'sku_duplicate','get_listings returned SKU more than once: '+item.sku);
  records.set(item.sku,{sku:item.sku,asin:item.asin??null,productType:item.productType??null,attributes:item.attributes});
 }
 const missing=skus.filter(sku=>!records.has(sku));check(!missing.length,'sku_missing','SKUs not in the get_listings copy: '+missing.join(', '));
 return {kind:'listings',path:read.path,sha256:read.sha256,records};
}
async function readFields(files,bind){
 const byType=new Map(),inputs=[];
 for(const file of files){
  const read=await readSaved(file,'fields_unreadable','Field definitions'),b=read.body;
  check(isObj(b)&&isObj(b.listingFieldDefinitions)&&typeof b.productType==='string','fields_unreadable',`${file}: not a saved get_product_type_fields result`);
  check(b.sellerId===bind.seller&&b.marketplaceId===bind.marketplace,'fields_mismatch',`${file}: field definitions are for another seller or marketplace`);
  check(!byType.has(b.productType),'usage','More than one --fields file for product type '+b.productType);
  const defs={};
  for(const group of Object.values(b.listingFieldDefinitions))if(isObj(group?.expandedFields))Object.assign(defs,group.expandedFields);
  byType.set(b.productType,defs);inputs.push({productType:b.productType,path:read.path,sha256:read.sha256});
 }
 return {byType,inputs};
}

// ---- ledger ----
async function readLedger(root){
 const text=await readFile(join(root,'ledger.jsonl'),'utf8').catch(error=>{if(error.code==='ENOENT')return '';throw error;});
 return text.split('\n').filter(line=>line.trim()).map((line,i)=>{try{return JSON.parse(line);}catch{fail('ledger_invalid',`${join(root,'ledger.jsonl')} line ${i+1} is not JSON`);}});
}
const append=(root,event,deps)=>appendFile(join(root,'ledger.jsonl'),JSON.stringify({at:iso(deps.now()),...event})+'\n');
function facts(events,index){
 const own=events.filter(event=>event.index===index);
 return {submitted:own.find(e=>e.event==='submitted'),statuses:own.filter(e=>e.event==='status'),verifies:own.filter(e=>e.event==='verify'),closed:own.find(e=>e.event==='closed')};
}
const isOpen=f=>Boolean(f.submitted)&&!f.closed&&f.verifies.at(-1)?.state!=='verified';
// The MAIN review is older than the approval, so its clock usually runs out first; either one expires the approval.
const expired=(approval,now)=>[approval.approved_at,approval.main_review?.approved_at].filter(Boolean).some(at=>!(now-Date.parse(at)<=APPROVAL_HOURS*3600e3));
// With unsubmitted, approved items of other batches that were never submitted or voided also count (build, approve).
async function openItems(root,exclude,{unsubmitted=false}={}){
 const entries=await readdir(root,{withFileTypes:true}).catch(error=>{if(error.code==='ENOENT')return [];throw error;});
 const open=[];
 for(const entry of entries){
  const dir=resolve(root,entry.name);if(!entry.isDirectory()||dir===exclude||!await exists(join(dir,'ledger.jsonl')))continue;
  let bytes,batch;try{bytes=await readFile(join(dir,'batch.json'));batch=JSON.parse(bytes.toString('utf8'));}catch{fail('ledger_invalid',`${dir} has a ledger but no readable batch.json`);}
  const events=await readLedger(dir),digest=sha(bytes),approved=events.some(e=>e.event==='approved'&&e.batch_sha256===digest);
  for(const item of batch.items||[]){
   const f=facts(events,item.index),waiting=unsubmitted&&approved&&!f.submitted&&!f.closed;
   if(isOpen(f)||waiting)open.push({batch:dir,index:item.index,sku:item.sku,touched:item.touched||[],kind:waiting?'approved_not_submitted':'submitted'});
  }
 }
 return open;
}
function pendingCheck(open,sku,touched){
 const hit=open.find(item=>item.sku===sku&&item.touched.some(attr=>touched.includes(attr)));
 if(!hit)return;
 const what=hit.kind==='approved_not_submitted'?'an approved, unsubmitted item':'an open submission',fix=hit.kind==='approved_not_submitted'?'submit and verify it, or close it (void), first':'verify it or close it first';
 fail('submission_pending',`${sku}: ${hit.touched.filter(a=>touched.includes(a)).join(', ')} has ${what} in batch ${hit.batch} item ${hit.index}; ${fix}`);
}

// ---- review.md ----
const cell=value=>(value===undefined?'':typeof value==='string'?value:JSON.stringify(value)).replace(/\|/g,'\\|').replace(/\r\n|\r|\n/g,'<br>');
function attributeTable(before,detail){
 const after=detail.array,rows=[];
 for(let i=0;i<Math.max(before?.length??0,after.length);i++){
  const b=new Map(leaves(before?.[i]??{}).map(([path,value])=>[path,value])),a=leaves(after[i]??{}),seen=new Set();
  for(const [path,value,key] of a){
   seen.add(path);const full=path?`${i}.${path}`:String(i);
   const note=detail.newElements.has(i)||!b.has(path)?'new':detail.setPaths.has(full)?'changed':SELECTORS.has(key)?'selector':'carried';
   rows.push(`| ${i} | ${cell(path)} | ${cell(b.get(path))} | ${cell(value)} | ${note} |`);
  }
  for(const [path,value] of b)if(!seen.has(path))rows.push(`| ${i} | ${cell(path)} | ${cell(value)} |  | removed |`);
 }
 return ['| Element | Field | Before | After | Note |','| --- | --- | --- | --- | --- |',...rows].join('\n');
}
function reviewText(batch,digest,details){
 const out=[`# FlatFilePro direct update batch`,'',`- Seller: ${batch.seller_id}`,`- Marketplace: ${batch.marketplace_id}`,`- Scope: ${batch.scope}`,`- Items: ${batch.items.length}`,`- Batch SHA-256: ${digest}`,`- Built: ${batch.created_at}`,'',
  'Each payload replaces the whole array of every touched attribute on Amazon. Notes: changed = set by this batch, new = added by this batch, carried = copied unchanged from the base, selector = marketplace or language selector.',''];
 for(const item of batch.items){
  out.push(`## ${pad(item.index)} ${item.sku}`,'',`- ASIN: ${item.asin??'unknown'}`,`- Product type: ${item.product_type}`,`- Base source: ${item.base_source}`,`- Carried content: ${item.carried?'yes':'no'}`,`- Payload: ${item.payload_file} (${item.payload_sha256})`,'');
  for(const attr of item.touched){
   if(LOCATOR_RE.test(attr))continue;
   out.push(`### ${attr}`,'',attributeTable(item.before.touched[attr],details[item.index][attr]),'');
  }
  if(item.images.length){
   out.push('### Images','','| Slot | Attribute | Image SHA-256 | Hosted URL | Current Amazon URL |','| --- | --- | --- | --- | --- |');
   for(const image of item.images)out.push(`| ${image.slot} | ${image.attribute} | ${image.sha256} | ${cell(image.url)} | ${cell(image.before??'none')} |`);
   out.push('');
  }
  out.push('### Warnings','');
  out.push(...(item.warnings.length?item.warnings.map(w=>`- ${w.code}: ${w.path} "${cell(w.value)}" is not one of ${cell(w.options.join(', '))}; free text accepted for ${w.attribute}`):['None.']),'');
  out.push('### Live issues before the write','');
  if(item.before.issues.length)out.push('| Code | Severity | Attributes | Message |','| --- | --- | --- | --- |',...item.before.issues.map(issue=>`| ${cell(String(issue.code??''))} | ${cell(String(issue.severity??''))} | ${cell((issue.attributeNames||[]).join(', '))} | ${cell(issue.message)} |`));
  else out.push('None.');
  out.push('');
 }
 return out.join('\n');
}

// ---- build ----
async function build(args,deps){
 attended(deps);
 const seller=args['--seller-id'],marketplace=args['--marketplace-id'],scope=args['--scope'],bind={seller,marketplace};
 check(seller&&marketplace,'usage','--seller-id and --marketplace-id are required');
 check(/^[A-Z0-9]+$/.test(seller)&&/^[A-Z0-9]+$/.test(marketplace),'usage','--seller-id and --marketplace-id must be the exact IDs from ffp-mcp.mjs binding');
 check(['seo','attributes','images'].includes(scope),'usage','--scope must be seo, attributes or images');
 check(args['--out'],'usage','--out DIR is required');
 if(scope==='images')check(args['--images']&&!args['--changes'],'usage','Scope images takes --images FILE and no --changes');
 else check(args['--changes']&&!args['--images'],'usage',`Scope ${scope} takes --changes CSV and no --images`);
 check(!(args['--export']&&args['--listings']),'usage','Use at most one base: --export FILE or --listings FILE');
 check(args['--live']?.length,'usage','One --live FILE per SKU is required');
 const out=resolve(args['--out']),present=await exists(out);
 check(!present||present.isDirectory()&&(await readdir(out)).length===0,'batch_exists',`${out} exists and is not an empty directory; choose a new batch directory`);
 const ledgerRoot=resolve(args['--ledger-root']||dirname(out)),allowFree=new Set(args['--allow-free-text']||[]);
 const input=scope==='images'?await readImages(args['--images']):await readChanges(args['--changes'],scope);
 // Group by SKU in first-appearance order.
 const bySku=new Map(),seen=new Set();
 for(const row of input.rows){
  const dup=`${row.sku}\u0000${row.key}`;check(!seen.has(dup),'duplicate_change',`${row.sku} ${row.key} appears more than once`);seen.add(dup);
  (bySku.get(row.sku)??bySku.set(row.sku,[]).get(row.sku)).push(row);
 }
 const skus=[...bySku.keys()];
 const lives=new Map();
 for(const file of args['--live']){
  const live=await readLive(file,bind);
  check(bySku.has(live.sku),'live_mismatch',`${file}: live read is for ${live.sku}, which this batch does not change`);
  check(!lives.has(live.sku),'live_duplicate','More than one --live file for '+live.sku);lives.set(live.sku,live);
 }
 const noLive=skus.filter(sku=>!lives.has(sku));check(!noLive.length,'live_missing','No --live read for: '+noLive.join(', '));
 const base=args['--export']||args['--listings']?await readBase(args,bind,skus):null;
 const fields=await readFields(args['--fields']||[],bind);
 const open=await openItems(ledgerRoot,out,{unsubmitted:true});
 const items=[],payloads=[],details=[];
 skus.forEach((sku,index)=>{
  const rows=bySku.get(sku),live=lives.get(sku),touched=[...new Set(rows.map(row=>row.attr))];
  requireComplete(live,touched);
  const record=base?.records.get(sku),baseAttrs=record?stripNonAttributes(record.attributes):null;
  const baseType=record?.productType??null,liveType=live.summary?.productType??null;
  check(!(baseType&&liveType&&baseType!==liveType),'product_type_mismatch',`${sku}: the base says ${baseType}, Amazon says ${liveType}`);
  const productType=baseType??liveType;check(productType,'product_type_unknown',`${sku}: no productType in the base or the live summaries`);
  if(baseAttrs)for(const attr of touched)check(same(live.attributes[attr],baseAttrs[attr]),'stale_base',`${sku}: ${attr} differs between the live read and the ${base.kind==='export'?'export':'get_listings copy'}; fetch a fresh base`);
  const defs=fields.byType.get(productType)||{},attributes={},detail={},warnings=[],images=[];let carried=false;
  for(const attr of touched){
   if(scope==='images'){
    const image=rows.find(row=>row.attr===attr);
    attributes[attr]=[{marketplace_id:marketplace,media_location:image.url}];
    detail[attr]={array:attributes[attr],setPaths:new Set(['0.media_location']),newElements:new Set()};
    images.push({slot:image.slot,attribute:attr,sha256:image.sha256,url:image.url,before:live.attributes[attr]?.[0]?.media_location??null});
    continue;
   }
   const built=buildAttribute({sku,attr,changes:rows.filter(row=>row.attr===attr),origin:baseAttrs?baseAttrs[attr]:live.attributes[attr],def:defs[attr],marketplace,allowFree});
   check(!same(built.array,live.attributes[attr]),'no_op_change',`${sku}: ${attr} already has these values on Amazon; verify could never show the write landed, so drop the row`);
   const carriedHere=carriedPaths(built.array,built.setPaths);
   check(!carriedHere.length||base,'base_unverified',`${sku}: ${attr} would carry untouched content (${carriedHere.join(', ')}) from the live read alone; pass a verified --export or an agreeing --listings base`);
   carried||=carriedHere.length>0;attributes[attr]=built.array;detail[attr]=built;warnings.push(...built.warnings);
  }
  pendingCheck(open,sku,touched);
  const payload={sku,sellerId:seller,marketplaceId:marketplace,productType,attributes},bytes=Buffer.from(json1(payload));
  const payloadFile=`payloads/${pad(index)}.json`;payloads.push([payloadFile,bytes]);details.push(detail);
  items.push({index,sku,asin:record?.asin??live.summary?.asin??null,product_type:productType,payload_file:payloadFile,payload_sha256:sha(bytes),touched,
   base_source:!base?'none':base.kind==='export'?'export':'agreeing_reads',carried,images,main_image_sha256:images.filter(image=>image.slot==='MAIN').map(image=>image.sha256),warnings,
   before:{image_locators:Object.fromEntries(LOCATORS.map(attr=>[attr,live.attributes[attr]?.[0]?.media_location??null])),touched:Object.fromEntries(touched.map(attr=>[attr,live.attributes[attr]??null])),issues:live.issues.map(cleanIssue)}});
 });
 const missing=skus.filter(sku=>!items.some(item=>item.sku===sku));
 check(items.length===skus.length&&!missing.length,'count_mismatch',`Read ${skus.length} SKUs but built ${items.length} items; missing: ${missing.join(', ')}`);
 const batch={schema_version:1,tool:'ffp-mcp-update',created_at:iso(deps.now()),seller_id:seller,marketplace_id:marketplace,scope,ledger_root:ledgerRoot,
  inputs:{[input.kind]:{path:input.path,sha256:input.sha256},base:base?{kind:base.kind,path:base.path,sha256:base.sha256}:null,live:skus.map(sku=>({sku,path:lives.get(sku).path,sha256:lives.get(sku).sha256})),fields:fields.inputs},items};
 const batchBytes=Buffer.from(json1(batch)),digest=sha(batchBytes),created=[];
 const write=async(path,data)=>{await writeFile(path,data,{flag:'wx'});created.push(path);};
 try{
  await mkdir(join(out,'payloads'),{recursive:true});
  for(const [file,bytes] of payloads)await write(join(out,file),bytes);
  await write(join(out,'batch.json'),batchBytes);
  await write(join(out,'batch.sha256'),digest+'\n');
  await write(join(out,'review.md'),reviewText(batch,digest,details));
  await append(out,{event:'built',batch_sha256:digest,items:items.length},deps);created.push(join(out,'ledger.jsonl'));
 }catch(error){for(const file of created.reverse())await rm(file,{force:true});throw error;}
 const result={status:'built',batch:out,batch_sha256:digest,items:items.length,skus_read:skus.length,review:join(out,'review.md'),warnings_count:items.reduce((n,item)=>n+item.warnings.length,0),registration:'not_requested'};
 if(args['--register-run']){
  // Registered preserve: cleanup never quarantines these files, so the append-only ledger may keep growing.
  Object.assign(result,register(args['--register-run'],[join(out,'batch.json'),join(out,'batch.sha256'),join(out,'review.md'),...payloads.map(([file])=>join(out,file)),join(out,'ledger.jsonl')],deps.artifactctl));
  result.registration_note='ledger.jsonl is append-only and registered preserve; do not re-register it in the same run';
 }
 return result;
}

// ---- batch state ----
async function loadBatch(dir,{verify=true}={}){
 const root=resolve(dir);
 let bytes;try{bytes=await readFile(join(root,'batch.json'));}catch{fail('batch_missing','No batch.json in '+root);}
 let batch;try{batch=JSON.parse(bytes.toString('utf8'));}catch{fail('batch_changed','batch.json is not JSON; rebuild the batch');}
 check(batch?.tool==='ffp-mcp-update'&&Array.isArray(batch.items),'batch_changed','batch.json is not an ffp-mcp-update batch');
 const digest=sha(bytes),events=await readLedger(root);
 if(verify){
  const recorded=(await readFile(join(root,'batch.sha256'),'utf8').catch(()=>'')).trim();
  check(recorded===digest&&events.find(e=>e.event==='built')?.batch_sha256===digest,'batch_changed','batch.json differs from the SHA-256 recorded at build; rebuild the batch');
  for(const item of batch.items){
   const payload=await readFile(join(root,item.payload_file)).catch(()=>null);
   check(payload&&sha(payload)===item.payload_sha256,'batch_changed',`${item.payload_file} differs from batch.json; rebuild the batch`);
  }
 }
 return {root,batch,digest,events,approval:events.filter(e=>e.event==='approved'&&e.batch_sha256===digest).at(-1)};
}
function pickItem(args,batch){
 check(Boolean(args['--index'])!==Boolean(args['--sku']),'usage','Use exactly one of --index N or --sku S');
 const item=args['--index']!==undefined?(check(/^\d+$/.test(args['--index']),'usage','--index must be a number'),batch.items.find(i=>i.index===Number(args['--index']))):batch.items.find(i=>i.sku===args['--sku']);
 check(item,'item_missing',`No item ${args['--index']??args['--sku']} in this batch`);
 return item;
}
const mainHashes=batch=>[...new Set(batch.items.flatMap(item=>item.main_image_sha256||[]))];
async function mainReview(file,hashes,now){
 let bytes,body;try{bytes=await readFile(file);body=JSON.parse(bytes.toString('utf8'));}catch{fail('main_review_required','MAIN review file is unreadable: '+file);}
 check(isObj(body)&&JSON.stringify(Object.keys(body).sort())==='["approved_at","approved_by","image_sha256"]','main_review_required','MAIN review needs exactly approved_by, approved_at and image_sha256');
 check(typeof body.approved_by==='string'&&body.approved_by.trim()!=='','main_review_required','MAIN review approved_by is empty');
 const at=Date.parse(body.approved_at);
 check(typeof body.approved_at==='string'&&/^\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d(\.\d+)?)?(Z|[+-]\d\d:?\d\d)$/.test(body.approved_at)&&Number.isFinite(at),'main_review_required','MAIN review approved_at must be an ISO time with a timezone');
 check(at<=now,'main_review_required','MAIN review approved_at is in the future');
 check(now-at<=APPROVAL_HOURS*3600e3,'main_review_required',`MAIN review approved_at is older than ${APPROVAL_HOURS} hours; the operator reviews the MAIN images again in this chat`);
 check(Array.isArray(body.image_sha256)&&body.image_sha256.every(hash=>typeof hash==='string'),'main_review_required','MAIN review image_sha256 must be a list');
 const given=new Set(body.image_sha256);
 check(given.size===hashes.length&&hashes.every(hash=>given.has(hash)),'main_review_required','MAIN review image_sha256 must list exactly the MAIN image hashes of this batch: '+hashes.join(', '));
 return {path:resolve(file),sha256:sha(bytes),approved_by:body.approved_by,approved_at:body.approved_at,image_sha256:body.image_sha256};
}

async function approve(args,deps){
 attended(deps);check(args['--batch']&&args['--approved-by'],'usage','--batch DIR and --approved-by NAME are required');
 const {root,batch,digest,events,approval}=await loadBatch(args['--batch']);
 check(!approval||expired(approval,deps.now()),'already_approved',`Batch ${digest} is already approved by ${approval?.approved_by}`);
 const open=await openItems(batch.ledger_root||dirname(root),root,{unsubmitted:true});
 for(const item of batch.items){const f=facts(events,item.index);if(!f.submitted&&!f.closed)pendingCheck(open,item.sku,item.touched);}
 const hashes=mainHashes(batch);let review;
 if(hashes.length){check(args['--main-review'],'main_review_required','This batch changes MAIN images; pass --main-review FILE listing every MAIN image SHA-256');review=await mainReview(args['--main-review'],hashes,deps.now());}
 else check(!args['--main-review'],'usage','--main-review is only for batches with MAIN images');
 await append(root,{event:'approved',batch_sha256:digest,approved_by:args['--approved-by'],approved_at:iso(deps.now()),...(review?{main_review:review}:{})},deps);
 return {status:'approved',batch_sha256:digest,items:batch.items.length,approved_by:args['--approved-by'],...(approval?{renewed:true}:{})};
}

async function next(args,deps){
 attended(deps);check(args['--batch']&&args['--live'],'usage','--batch DIR and --live FILE are required; FILE is a fresh get_listings_item_from_amazon read taken right before this write');
 const {root,batch,digest,events,approval}=await loadBatch(args['--batch']);
 check(approval,'not_approved',`Batch ${digest} has no approval; the operator approves the exact batch first`);
 check(!expired(approval,deps.now()),'approval_expired',`The approval of batch ${digest} (${approval.approved_at}) or its MAIN review is older than ${APPROVAL_HOURS} hours; the operator approves the exact batch (and any MAIN images) again in this chat, then run approve`);
 const hashes=mainHashes(batch);
 if(hashes.length){
  check(approval.main_review,'main_review_required','The approval has no MAIN review');
  const review=await mainReview(approval.main_review.path,hashes,deps.now());
  check(review.sha256===approval.main_review.sha256,'main_review_required','The MAIN review file changed after approval');
 }
 for(const i of batch.items){
  const saved=`responses/${pad(i.index)}.json`;
  check(facts(events,i.index).submitted||!await exists(join(root,saved)),'record_incomplete',`${saved} exists but item ${i.index} (${i.sku}) has no submitted record; run record for it, which recovers the saved response`);
 }
 const item=batch.items.find(i=>{const f=facts(events,i.index);return !f.submitted&&!f.closed;});
 if(!item)return {status:'complete',batch_sha256:digest,items:batch.items.length};
 // The hold anchors on the first item that was not voided before its write.
 const anchor=batch.items.find(i=>!facts(events,i.index).closed?.void);
 // A closed anchor releases the rest only when the operator confirmed it landed (close --landed).
 if(anchor.index!==item.index&&!facts(events,anchor.index).closed?.landed){
  const af=facts(events,anchor.index),state=af.verifies.at(-1)?.state;
  check(!af.closed,'first_item_unverified',`Item ${anchor.index} (${anchor.sku}) was closed after its write without --landed; build a new batch for the remaining items`,{status:'held'});
  check(RELEASES_HOLD.has(state),'first_item_unverified',`Item ${anchor.index} (${anchor.sku}) must verify before the rest are released; latest verify: ${state??'none'}`,{status:'held'});
 }
 const live=await readLive(args['--live'],{seller:batch.seller_id,marketplace:batch.marketplace_id});
 check(live.sku===item.sku,'live_mismatch',`The live read is for ${live.sku}, not ${item.sku}`);
 requireComplete(live,item.touched);
 const stale=item.touched.filter(attr=>!same(live.attributes[attr],item.before.touched[attr]));
 check(!stale.length,'stale_base',`${item.sku}: ${stale.join(', ')} changed on Amazon since the build's before-read; close this item (void) and build a new batch from a fresh read`);
 pendingCheck(await openItems(batch.ledger_root||dirname(root),root),item.sku,item.touched);
 const payload=JSON.parse(await readFile(join(root,item.payload_file),'utf8'));
 // The fresh read's issues become the verify baseline, so an issue that appeared after the build is not blamed on the write.
 await append(root,{event:'fresh_read',index:item.index,sku:item.sku,live:{path:live.path,sha256:live.sha256},issues:live.issues.map(cleanIssue)},deps);
 return {status:'next',index:item.index,sku:item.sku,payload_sha256:item.payload_sha256,tool:TOOL,arguments:payload};
}

// Best-effort fields from a tool response whose exact shape is unknown: top level or one object level down.
function extract(body){
 const layers=isObj(body)?[body,...Object.values(body).filter(isObj)]:[];
 const pick=(...names)=>{for(const layer of layers)for(const name of names)if(layer[name]!==undefined&&layer[name]!==null&&layer[name]!=='')return layer[name];};
 const id=value=>(typeof value==='number'&&Number.isInteger(value)&&value>0)||(typeof value==='string'&&/^[1-9]\d*$/.test(value))?String(value):null;
 const str=value=>typeof value==='string'?value:null,poll=pick('pollAfterSeconds','poll_after_seconds'),terminal=pick('terminal','isTerminal','is_terminal');
 return {runId:id(pick('runId','run_id')),runItemId:id(pick('runItemId','run_item_id')),status:str(pick('status','state')),outcome:str(pick('outcome')),terminal:typeof terminal==='boolean'?terminal:null,
  pollAfterSeconds:Number.isFinite(Number(poll))&&poll!==undefined?Number(poll):null,sku:str(pick('sku'))};
}
async function saveExclusive(dir,name,data){await mkdir(dir,{recursive:true});const path=join(dir,name);await writeFile(path,data,{flag:'wx'});return path;}
async function nextNumbered(dir,prefix){
 const names=await readdir(dir).catch(()=>[]),re=new RegExp(`^${prefix}-(\\d+)\\.json$`);
 return Math.max(0,...names.map(name=>re.exec(name)).filter(Boolean).map(match=>Number(match[1])))+1;
}

async function recordCmd(args,deps){
 attended(deps);check(args['--batch'],'usage','--batch DIR is required');
 // No hash or approval gate here: the write may already be live, so the record is always kept.
 const {root,batch,events}=await loadBatch(args['--batch'],{verify:false}),item=pickItem(args,batch);
 check(!facts(events,item.index).submitted,'already_recorded',`Item ${item.index} (${item.sku}) already has a submission record; it is never offered again`);
 const gap=batch.items.find(i=>{const g=facts(events,i.index);return i.index<item.index&&!g.submitted&&!g.closed;});
 check(!gap,'out_of_order',`Item ${gap?.index} (${gap?.sku}) has no record yet; record items in order`);
 const saved=join(root,'responses',pad(item.index)+'.json');
 const fromResponse=(raw,file)=>{
  const got=extract(bodyOf(raw));
  const event={event:'submitted',index:item.index,sku:item.sku,payload_sha256:item.payload_sha256,status:got.status??got.outcome,runId:got.runId,runItemId:got.runItemId,pollAfterSeconds:got.pollAfterSeconds,run_ids_missing:!got.runId||!got.runItemId,response_file:file};
  if(got.sku&&got.sku!==item.sku)event.response_sku_mismatch=true;
  return event;
 };
 let event;
 // A response saved by an earlier record whose ledger append failed: record it from the saved file.
 if(await exists(saved))event={...fromResponse(await readFile(saved,'utf8'),saved),recovered:true};
 else if(args['--no-response']){
  check(args['--note'],'usage','--no-response needs --note TEXT (timeout or tool error, delivery unknown)');
  event={event:'submitted',index:item.index,sku:item.sku,payload_sha256:item.payload_sha256,status:'UNKNOWN',runId:null,runItemId:null,pollAfterSeconds:null,run_ids_missing:true,response_file:null,note:args['--note']};
 }else{
  check(!args['--note'],'usage','--note goes with --no-response');
  const raw=await deps.readStdin();check(raw.trim()!=='','usage','STDIN is empty; pipe the update tool response, or use --no-response --note TEXT');
  let file;try{file=await saveExclusive(join(root,'responses'),pad(item.index)+'.json',raw);}catch(error){fail(error.code==='EEXIST'?'already_recorded':'record_failed',error.code==='EEXIST'?`responses/${pad(item.index)}.json already exists`:'Cannot save the response: '+error.code);}
  event=fromResponse(raw,file);
 }
 await append(root,event,deps);
 if(event.response_sku_mismatch)fail('response_sku_mismatch',`The response names a different SKU than ${item.sku}; recorded, check the live listing of both SKUs`,{event});
 return event;
}

async function statusCmd(args,deps){
 attended(deps);check(args['--batch'],'usage','--batch DIR is required');
 const {root,batch,events}=await loadBatch(args['--batch'],{verify:false}),item=pickItem(args,batch),submitted=facts(events,item.index).submitted;
 check(submitted?.runId&&submitted?.runItemId,'status_without_run',`Item ${item.index} (${item.sku}) has no submission with runId and runItemId`);
 const raw=await deps.readStdin();check(raw.trim()!=='','usage','STDIN is empty; pipe the get_listing_update_status result');
 const got=extract(bodyOf(raw));
 check((!got.runId||got.runId===submitted.runId)&&(!got.runItemId||got.runItemId===submitted.runItemId),'status_mismatch',`The status result is for run ${got.runId}/${got.runItemId}, not ${submitted.runId}/${submitted.runItemId}`);
 const dir=join(root,'status'),k=await nextNumbered(dir,pad(item.index));
 const file=await saveExclusive(dir,`${pad(item.index)}-${k}.json`,raw);
 const terminal=got.terminal??([got.status,got.outcome].some(s=>/^SUCCEEDED$/i.test(s||'')||FAILED_RE.test(s||''))?true:got.status||got.outcome?false:null);
 const event={event:'status',index:item.index,sku:item.sku,status:got.status,outcome:got.outcome,terminal,raw_file:file};
 await append(root,event,deps);
 return event;
}

async function readPixels(files){
 const results=[];
 for(const file of files){
  const read=await readSaved(file,'pixels_unreadable','Pixel comparison'),t=read.body?.thresholds;
  check(Array.isArray(read.body?.results),'pixels_unreadable',`${file}: needs a results list from image_intake.py compare`);
  const loose=Object.entries(PIXEL_THRESHOLDS).filter(([key,max])=>!(isObj(t)&&typeof t[key]==='number'&&t[key]>=0&&t[key]<=max)).map(([key])=>key);
  check(!loose.length,'pixels_thresholds',`${file}: thresholds ${loose.join(', ')} are missing or looser than ${JSON.stringify(PIXEL_THRESHOLDS)}; rerun image_intake.py compare without loosening them`);
  results.push(...read.body.results);
 }
 return results;
}
async function verify(args,deps){
 attended(deps);check(args['--batch']&&args['--live'],'usage','--batch DIR and --live FILE are required');
 const {root,batch,events}=await loadBatch(args['--batch']),item=pickItem(args,batch),f=facts(events,item.index);
 check(f.submitted,'not_submitted',`Item ${item.index} (${item.sku}) has no submission record`);
 const live=await readLive(args['--live'],{seller:batch.seller_id,marketplace:batch.marketplace_id});
 check(live.sku===item.sku,'live_mismatch',`The live read is for ${live.sku}, not ${item.sku}`);
 requireKept(live,[...new Set([...item.touched,...LOCATORS])]);
 const payload=JSON.parse(await readFile(join(root,item.payload_file),'utf8'));
 const attributes=item.touched.filter(attr=>!LOCATOR_RE.test(attr)).map(attr=>{
  const expected=payload.attributes[attr],actual=live.attributes[attr]??null;
  if(same(actual,expected))return {attribute:attr,result:'match'};
  return {attribute:attr,result:same(actual,item.before.touched[attr]??null)?'not_yet':'mismatch',expected,actual};
 });
 const images=item.images.map(image=>{
  const after=live.attributes[image.attribute]?.[0]?.media_location??null;
  const result=!after?(image.before?'missing':'not_yet'):after===image.before||after===image.url?'not_yet':after.startsWith(AMAZON_IMAGE)?'changed':'unexpected';
  return {slot:image.slot,attribute:image.attribute,image_sha256:image.sha256,before:image.before,after,result};
 });
 const protectedSlots=LOCATORS.filter(attr=>!item.touched.includes(attr)).map(attr=>{
  const before=item.before.image_locators[attr]??null,after=live.attributes[attr]?.[0]?.media_location??null;
  return {attribute:attr,before,after,result:same(before,after)?'preserved':'protected_slot_changed'};
 });
 // Multiset: an issue already present once before is new the second time it appears (image issues name no slot).
 const baseline=events.filter(e=>e.event==='fresh_read'&&e.index===item.index).at(-1)?.issues??item.before.issues;
 const seenBefore=new Map();for(const issue of baseline){const key=issueKey(issue);seenBefore.set(key,(seenBefore.get(key)??0)+1);}
 const touchesImage=item.touched.some(attr=>LOCATOR_RE.test(attr));
 const issuesNew=live.issues.filter(issue=>{const key=issueKey(issue),n=seenBefore.get(key)??0;if(n){seenBefore.set(key,n-1);return false;}return true;})
  // An issue without attributeNames is listing-level (a suppression, for example) and always counts.
  .filter(issue=>{const names=issue?.attributeNames||[];return !names.length||names.some(name=>item.touched.includes(name)||name==='media_locator'&&touchesImage);}).map(cleanIssue);
 const pixels=await readPixels(args['--pixels']||[]);
 const pixelChecks=images.filter(image=>image.result==='changed').map(image=>{
  const hits=pixels.filter(r=>r?.sku===item.sku&&r.slot===image.slot&&r.amazon_url===image.after&&r.image_sha256===image.image_sha256);
  const rejected=hits.some(r=>r.match===false),confirmed=!rejected&&hits.some(r=>r.match===true);
  const indistinct=rejected&&hits.filter(r=>r.match===false).every(r=>r.discriminating===false);
  return {sku:item.sku,slot:image.slot,attribute:image.attribute,amazon_url:image.after,image_sha256:image.image_sha256,before_url:image.before??null,confirmed,result:rejected?'rejected':confirmed?'confirmed':'unchecked',...(rejected?{indistinct}:{})};
 });
 // A failure word in the latest status (or the update response before any poll) fails the item; success needs a polled SUCCEEDED.
 const last=f.statuses.at(-1),words=[(last??f.submitted)?.status,last?.outcome],isSucceeded=word=>/^SUCCEEDED$/i.test(word||'');
 const failed=words.some(word=>FAILED_RE.test(word||''))||last?.terminal===true&&!words.some(isSucceeded);
 const succeeded=Boolean(last)&&!failed&&words.some(isSucceeded);
 const mismatch=attributes.some(a=>a.result==='mismatch')||images.some(i=>i.result==='missing'||i.result==='unexpected')||protectedSlots.some(p=>p.result!=='preserved');
 const state=mismatch?'mismatch':failed?'update_failed':pixelChecks.some(p=>p.result==='rejected')?'pixels_mismatch'
  :issuesNew.some(issue=>String(issue.severity??'').toUpperCase()==='ERROR')?'issues_new_error'
  :attributes.some(a=>a.result==='not_yet')||images.some(i=>i.result==='not_yet')?'not_yet'
  :pixelChecks.some(p=>!p.confirmed)?'landed_pixels_unchecked':succeeded?'verified':'landed_status_pending';
 const dir=join(root,'verify'),k=await nextNumbered(dir,pad(item.index)),name=`${pad(item.index)}-${k}.json`;
 const result={status:state,state,index:item.index,sku:item.sku,checked_at:iso(deps.now()),live:{path:live.path,sha256:live.sha256},attributes,images,protected_slots:protectedSlots,
  issues_new:issuesNew,issues_new_flag:issuesNew.length>0,pixel_checks:pixelChecks,update_status:{status:last?.status??f.submitted.status??null,outcome:last?.outcome??null,terminal:last?.terminal??null,succeeded,failed},verify_file:join(dir,name)};
 await saveExclusive(dir,name,json1(result));
 await append(root,{event:'verify',index:item.index,sku:item.sku,state,issues_new_count:issuesNew.length,verify_file:result.verify_file},deps);
 return {...result,exit_code:PASSING.has(state)?0:3};
}

const CLOSE_THEN_REBUILD="close this item with the operator's decision, then build a new approved batch if the change is still wanted";
const NEXT_ACTION={
 built:'operator approves the exact batch SHA-256, then run approve',
 approved_not_submitted:'save a fresh live read of the SKU, run next --live FILE and call the update tool with its arguments, then record',
 approval_expired:`the approval is older than ${APPROVAL_HOURS} hours: the operator approves the exact batch again in this chat and you run approve, or close the item (void) if it is no longer wanted`,
 submitted:'call get_listing_update_status, then run status',
 status_nonterminal:'poll again after pollAfterSeconds, then run status',
 status_terminal:'save a live after-read and run verify',
 unknown:'save a live read and run verify; close the item if the write never landed',
 landed_status_pending:'poll status until SUCCEEDED, then run verify again',
 landed_no_run:"the live read matches, but the status cannot be polled without a runId; the operator decides: close --landed releases the rest of the batch, close without it keeps the hold",
 landed_pixels_unchecked:'run image_intake.py compare and verify again with --pixels',
 mismatch:'review the verify file; '+CLOSE_THEN_REBUILD,
 mismatch_in_flight:"the write may still be in progress: poll status (when the item has a runId), save a new live after-read and verify again before treating the mismatch as final; if it stays a mismatch, "+CLOSE_THEN_REBUILD,
 update_failed:'Amazon reports the update failed; review the status and verify files and never resubmit this item; '+CLOSE_THEN_REBUILD,
 pixels_mismatch:"open the pixels file: discriminating false means the new image cannot be told apart from the before image, so the operator compares both by eye and, when it is right, you run close --landed; otherwise the live image is not the archived PNG: report it with the compare file; "+CLOSE_THEN_REBUILD,
 issues_new_error:'Amazon reports a new ERROR issue on a touched attribute or the whole listing; report it from the verify file; '+CLOSE_THEN_REBUILD,
 not_yet:"wait (poll status when the item has a runId), save a new live after-read and run verify again; never resubmit; close the item with the operator's decision if it never lands",
};
function nextAction(state,f,approval,now){
 const unknown=f.submitted&&(f.submitted.status==='UNKNOWN'||f.submitted.run_ids_missing);
 if(state==='approved_not_submitted'&&approval&&expired(approval,now))return NEXT_ACTION.approval_expired;
 if(state==='landed_status_pending'&&!f.submitted?.runId)return NEXT_ACTION.landed_no_run;
 if(state==='mismatch'&&(unknown||f.statuses.at(-1)?.terminal!==true))return NEXT_ACTION.mismatch_in_flight;
 return NEXT_ACTION[state]??'review the ledger';
}
function itemState(approved,f){
 if(f.closed||f.verifies.at(-1)?.state==='verified')return null;
 if(!f.submitted)return approved?'approved_not_submitted':'built';
 if(f.verifies.length)return f.verifies.at(-1).state;
 if(f.submitted.status==='UNKNOWN'||f.submitted.run_ids_missing)return 'unknown';
 const last=f.statuses.at(-1);
 return !last?'submitted':last.terminal===true?'status_terminal':'status_nonterminal';
}
async function pending(args,deps){
 check(args['--root'],'usage','--root DIR is required');
 const root=resolve(args['--root']),entries=await readdir(root,{withFileTypes:true}).catch(error=>fail('usage',`Cannot read ${root}: ${error.code}`)),items=[];
 for(const entry of entries.filter(e=>e.isDirectory()).sort((a,b)=>a.name<b.name?-1:a.name>b.name?1:0)){
  const dir=join(root,entry.name);if(!await exists(join(dir,'batch.json')))continue;
  const {batch,events,approval}=await loadBatch(dir,{verify:false});
  for(const item of batch.items){
   const f=facts(events,item.index),state=itemState(Boolean(approval),f);if(!state)continue;
   items.push({batch:dir,index:item.index,sku:item.sku,state,runId:f.submitted?.runId??null,runItemId:f.submitted?.runItemId??null,last_status:f.statuses.at(-1)?.status??f.submitted?.status??null,next_action:nextAction(state,f,approval,deps.now())});
  }
 }
 return {status:'pending',root,items};
}

async function close(args,deps){
 attended(deps);check(args['--batch']&&args['--reason']&&args['--approved-by'],'usage','--batch DIR, --reason TEXT and --approved-by NAME are required');
 const {root,batch,events}=await loadBatch(args['--batch'],{verify:false}),item=pickItem(args,batch),f=facts(events,item.index);
 check(!f.closed,'already_closed',`Item ${item.index} (${item.sku}) is already closed`);
 check(!args['--landed']||f.submitted,'usage','--landed needs a submitted item; an unsubmitted item is closed as void');
 let landedVerify=null;
 if(args['--landed']){
  // Only the two cases the tools cannot settle: an UNKNOWN write whose live read matches, and a pixel check the
  // operator accepted by eye with every other check clean.
  const lastVerify=f.verifies.at(-1);
  check(lastVerify,'landed_unproven','--landed needs a verify of this item first');
  let v;try{v=JSON.parse(await readFile(lastVerify.verify_file,'utf8'));}catch{fail('landed_unproven','The latest verify file is unreadable: '+lastVerify.verify_file);}
  const noRun=!f.submitted.runId,clean=!(v.issues_new||[]).some(i=>String(i.severity??'').toUpperCase()==='ERROR')&&(v.attributes||[]).every(a=>a.result==='match')
   &&(v.images||[]).every(i=>i.result==='changed')&&(v.protected_slots||[]).every(p=>p.result==='preserved');
  const unknownLanded=v.state==='landed_status_pending'&&noRun,pixelsByEye=v.state==='pixels_mismatch'&&clean&&(v.update_status?.succeeded===true||noRun);
  check(unknownLanded||pixelsByEye,'landed_unproven',`--landed fits only an UNKNOWN write whose live read matches, or a pixels_mismatch the operator accepted by eye with every other check clean and the update not pending; latest verify: ${v.state}`);
  landedVerify=lastVerify.verify_file;
 }
 // An item closed before any write is void: next never offers it and it no longer anchors the first-item hold.
 const event={event:'closed',index:item.index,sku:item.sku,reason:args['--reason'],approved_by:args['--approved-by'],last_verify_state:f.verifies.at(-1)?.state??null,...(f.submitted?{}:{void:true}),...(landedVerify?{landed:true,landed_verify_file:landedVerify}:{})};
 await append(root,event,deps);
 return {status:'closed',...event};
}

// ---- entry point ----
const readAll=async stream=>{const chunks=[];for await(const chunk of stream)chunks.push(chunk);return Buffer.concat(chunks).toString('utf8');};
const HANDLERS={build,approve,next,record:recordCmd,status:statusCmd,verify,pending,close};
export async function main(argv,deps={}){
 const options={now:deps.now||Date.now,artifactctl:deps.artifactctl||defaultArtifactctl,readStdin:deps.readStdin||(()=>readAll(process.stdin)),env:deps.env||process.env};
 let result,code=0;
 try{
  const args=parseArgs(argv);
  result=await HANDLERS[args.command](args,options);
  if(result.exit_code!==undefined){code=result.exit_code;delete result.exit_code;}
 }catch(error){
  result={status:'blocked',reason:error instanceof Blocked?error.reason:'unexpected',message:redact(error.message),...(error.extra||{})};code=2;
 }
 return {code,stdout:JSON.stringify(result)+'\n'};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){const {code,stdout}=await main(process.argv.slice(2));process.stdout.write(stdout);process.exitCode=code;}
