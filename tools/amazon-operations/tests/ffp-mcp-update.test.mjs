import '../../report-fetcher/test/helpers/isolated-runtime.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,rm,readFile,writeFile,readdir} from 'node:fs/promises';
import {join,dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {createHash} from 'node:crypto';
import {gzipSync} from 'node:zlib';
import {fileURLToPath} from 'node:url';
import {main,canon,same,LOCATORS,PIXEL_THRESHOLDS} from '../ffp-mcp-update.mjs';

const here=dirname(fileURLToPath(import.meta.url)),fixtures=join(here,'fixtures','ffp-mcp-update'),source=join(here,'..','ffp-mcp-update.mjs');
const S='A1TESTSELLER01',M='A1PA6795UKMFR9';
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const now=()=>Date.parse('2026-10-29T12:00:00.000Z');
const fixture=name=>join(fixtures,name);
const loadJson=async path=>JSON.parse(await readFile(path,'utf8'));
const records=(await readFile(fixture('export-records.jsonl'),'utf8')).trim().split('\n').map(line=>JSON.parse(line));
const record=sku=>records.find(r=>r.sku===sku);
const images=await loadJson(fixture('images.json'));
const run=async(argv,deps={})=>{const {code,stdout}=await main(argv,{now,env:{},...deps});assert.ok(stdout.endsWith('\n'));return {code,stdout,json:JSON.parse(stdout)};};
const withDir=async fn=>{const dir=await mkdtemp(join(tmpdir(),'ffp-mcp-update-'));try{return await fn(dir);}finally{await rm(dir,{recursive:true,force:true});}};

// A verified export with its receipt, built the way fetch-export writes them.
const exportDir=await mkdtemp(join(tmpdir(),'ffp-mcp-update-export-'));
process.once('exit',()=>{import('node:fs').then(fs=>fs.rmSync(exportDir,{recursive:true,force:true}));});
const exportFile=join(exportDir,'catalog-export-coat.jsonl.gz');
const gz=gzipSync(Buffer.from(records.map(r=>JSON.stringify(r)).join('\n')+'\n'));
await writeFile(exportFile,gz);
await writeFile(exportFile+'.receipt.json',JSON.stringify({jobId:'job-coat-0001',sellerId:S,marketplaceId:M,archiveStatus:'ALL',schemaVersion:2,snapshotAt:'2026-10-29T08:00:00.000Z',completedAt:'2026-10-29T08:00:01.000Z',export_count:records.length,sha256:sha(gz),compressedBytes:gz.length,fileName:'catalog-export-coat.jsonl.gz',path:exportFile,fetched_at:'2026-10-29T08:01:00.000Z',source:'ffp-mcp-export'},null,1));

const csv=rows=>['sku,attribute,value',...rows.map(row=>row.map(cell=>/[",\n]/.test(cell)?'"'+cell.replace(/"/g,'""')+'"':cell).join(','))].join('\n')+'\n';
async function changesFile(dir,rows,name='changes.csv'){const path=join(dir,name);await writeFile(path,csv(rows));return path;}
async function liveFile(dir,sku,mutate=()=>{},name){
 const body=await loadJson(live(sku));mutate(body);
 const path=join(dir,name||`live-${sku}-${Math.random().toString(16).slice(2)}.json`);await writeFile(path,JSON.stringify(body));return path;
}
// The dash-prefixed SKU's fixture file drops the leading dash from its name.
const live=sku=>fixture(`live-${sku.replace(/^-/,'')}.json`);
// A live read that asserts every attribute it lacks, among those listed in absent, is absent on Amazon.
const keptLive=(dir,sku,absent=[],mutate=()=>{})=>liveFile(dir,sku,b=>{mutate(b);b.kept_attributes=[...new Set([...Object.keys(b.item.attributes),...LOCATORS,...absent])];});
const nextItem=(out,sku,deps)=>run(['next','--batch',out,'--live',live(sku)],deps);
async function build(dir,{scope='seo',rows,imagesFile,lives,base=[],fields=[],extra=[],out=join(dir,'batches','b1'),deps}={}){
 const argv=['build','--seller-id',S,'--marketplace-id',M,'--scope',scope,'--out',out,...(rows?['--changes',await changesFile(dir,rows,'changes-'+Math.random().toString(16).slice(2)+'.csv')]:[]),...(imagesFile?['--images',imagesFile]:[]),
  ...lives.flatMap(path=>['--live',path]),...base,...fields.flatMap(path=>['--fields',path]),...extra];
 return {...await run(argv,deps),out};
}
const fieldsFile=fixture('fields-coat.json');
const payloadOf=async(out,index=0)=>loadJson(join(out,'payloads',String(index).padStart(3,'0')+'.json'));
const ledger=async out=>(await readFile(join(out,'ledger.jsonl'),'utf8')).trim().split('\n').map(line=>JSON.parse(line));
const rand=()=>Math.random().toString(16).slice(2);
const imageEntry=(sku,slot,digest)=>({sku,slot,artifact:{path:`/archive/source-archive/${digest}.png`,sha256:digest},url:`https://res.cloudinary.com/testcloud/image/upload/v1/ffp-test/${digest}.png`});
const writeJson=async(dir,prefix,body)=>{const path=join(dir,`${prefix}-${rand()}.json`);await writeFile(path,JSON.stringify(body));return path;};
const pixelsFile=(dir,results,thresholds=PIXEL_THRESHOLDS)=>writeJson(dir,'pixels',{status:'compared',...(thresholds?{thresholds}:{}),results});
const pendingOf=async(root,batch,index=0)=>(await run(['pending','--root',root])).json.items.find(i=>i.batch===batch&&i.index===index);
const response=(runId='101',runItemId='202',extra={})=>async()=>JSON.stringify({status:'ACCEPTED',runId,runItemId,pollAfterSeconds:1800,...extra});

test('canon compares text: key order, numeric strings, booleans and trimmed ends',()=>{
 assert.ok(same([{value:'0.26',unit:'kilograms'}],[{unit:'kilograms',value:0.26}]));
 assert.ok(same({a:' Text '},{a:'Text'}));assert.ok(same({b:false},{b:'false'}));assert.ok(same({v:'1.0'},{v:1}));
 assert.ok(same(undefined,undefined));assert.ok(!same(undefined,[]));assert.ok(!same(['a','b'],['b','a']));
 assert.deepEqual(canon({z:1,a:[true,' x ']}),{a:['true','x'],z:'1'});
});

test('canon keeps strings exact except trailing fractional zeros (LOGIC-6, WHOLE-2)',()=>{
 assert.ok(same(36,'36.00'));assert.ok(same(0.26,'0.26'));assert.ok(same(true,'true'));assert.ok(same('0.10','0.1'));assert.ok(same('-2.50',-2.5));
 assert.equal(canon('36.00'),'36');assert.equal(canon('0.10'),'0.1');assert.equal(canon('36.'),'36.');
 assert.ok(!same('00123','123'));assert.ok(!same([{value:'0042'}],[{value:'42'}]));assert.ok(!same('1e3','1000'));assert.ok(!same('1e3',1000));
 assert.ok(!same('12345678901234567890','12345678901234567891'));assert.ok(!same('007.50','7.5'));
});

test('seo build carries untouched bullets byte-identical from the verified export',async()=>withDir(async dir=>{
 const r=await build(dir,{rows:[['TEST-COAT-01','bullet_point.2.value','PFLEGE: Neuer dritter Punkt']],lives:[live('TEST-COAT-01')],base:['--export',exportFile]});
 assert.equal(r.code,0,r.stdout);
 assert.deepEqual(Object.keys(r.json),['status','batch','batch_sha256','items','skus_read','review','warnings_count','registration']);
 assert.equal(r.json.status,'built');assert.equal(r.json.items,1);assert.equal(r.json.skus_read,1);assert.equal(r.json.registration,'not_requested');
 const payload=await payloadOf(r.out),exported=record('TEST-COAT-01').attributes.bullet_point;
 assert.deepEqual(Object.keys(payload),['sku','sellerId','marketplaceId','productType','attributes']);
 assert.deepEqual(payload.attributes&&Object.keys(payload.attributes),['bullet_point']);
 assert.equal(payload.productType,'COAT');assert.equal(payload.attributes.bullet_point.length,5);
 for(const i of [0,1,3,4])assert.equal(JSON.stringify(payload.attributes.bullet_point[i]),JSON.stringify(exported[i]),'bullet '+i);
 assert.deepEqual(payload.attributes.bullet_point[2],{...exported[2],value:'PFLEGE: Neuer dritter Punkt'});
 const payloadText=await readFile(join(r.out,'payloads','000.json'),'utf8');assert.equal(payloadText,JSON.stringify(payload,null,1)+'\n');
 const batchBytes=await readFile(join(r.out,'batch.json')),batch=JSON.parse(batchBytes);
 assert.equal(sha(batchBytes),r.json.batch_sha256);assert.equal(await readFile(join(r.out,'batch.sha256'),'utf8'),r.json.batch_sha256+'\n');
 const item=batch.items[0];
 assert.equal(item.sku,'TEST-COAT-01');assert.equal(item.asin,'B0TESTCT01');assert.equal(item.base_source,'export');assert.equal(item.carried,true);
 assert.equal(item.payload_sha256,sha(payloadText));assert.deepEqual(item.touched,['bullet_point']);
 assert.equal(batch.inputs.base.kind,'export');assert.equal(batch.inputs.base.sha256,sha(gz));assert.equal(batch.inputs.live[0].sku,'TEST-COAT-01');
 assert.equal(item.before.image_locators.other_product_image_locator_2,'https://m.media-amazon.com/images/I/61TESTPT0201.jpg');assert.equal(item.before.image_locators.other_product_image_locator_3,null);
 assert.equal(item.before.touched.bullet_point.length,5);assert.equal(item.before.issues[0].code,'90220');
 const events=await ledger(r.out);assert.deepEqual(events.map(e=>e.event),['built']);assert.equal(events[0].batch_sha256,r.json.batch_sha256);
 const review=await readFile(r.json.review,'utf8');
 assert.match(review,/\| 2 \| value \| PFLEGE: Dritter Punkt \| PFLEGE: Neuer dritter Punkt \| changed \|/);
 assert.match(review,/\| 0 \| value \| WARM: Erster Punkt aus Wolle \| WARM: Erster Punkt aus Wolle \| carried \|/);
 assert.match(review,/GESCHENK: Fünfter Punkt \\\| mit Pipe/);assert.match(review,/\| 0 \| marketplace_id \| A1PA6795UKMFR9 \| A1PA6795UKMFR9 \| selector \|/);
 assert.match(review,new RegExp('Batch SHA-256: '+r.json.batch_sha256));assert.match(review,/Base source: export/);assert.match(review,/90220/);
 assert.ok(!review.includes(' \u2014 '));
}));

test('base_unverified without a base when content would be carried; single-item fields need none',async()=>withDir(async dir=>{
 const carried=await build(dir,{rows:[['TEST-COAT-01','bullet_point.2.value','Neu']],lives:[live('TEST-COAT-01')]});
 assert.equal(carried.code,2);assert.equal(carried.json.reason,'base_unverified');assert.match(carried.json.message,/bullet_point/);
 assert.ok(!(await readdir(dir)).includes('batches'));
 const single=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Neuer Titel'],['TEST-COAT-01','generic_keyword.0.value','neu begriffe']],lives:[live('TEST-COAT-01')]});
 assert.equal(single.code,0,single.stdout);
 const item=(await loadJson(join(single.out,'batch.json'))).items[0];assert.equal(item.base_source,'none');assert.equal(item.carried,false);
 assert.deepEqual((await payloadOf(single.out)).attributes.item_name,[{marketplace_id:M,language_tag:'de_DE',value:'Neuer Titel'}]);
 // All five bullets set: nothing carried, no base needed.
 const all=await build(dir,{rows:[0,1,2,3,4].map(i=>['TEST-COAT-01',`bullet_point.${i}.value`,'Punkt '+i]),lives:[live('TEST-COAT-01')],out:join(dir,'batches','b2')});
 assert.equal(all.code,0,all.stdout);
}));

test('stale_base when the live read differs from the export on a touched attribute',async()=>withDir(async dir=>{
 const changed=await liveFile(dir,'TEST-COAT-01',body=>{body.item.attributes.bullet_point[1].value='Anders';});
 const r=await build(dir,{rows:[['TEST-COAT-01','bullet_point.2.value','Neu']],lives:[changed],base:['--export',exportFile]});
 assert.equal(r.json.reason,'stale_base');assert.match(r.json.message,/TEST-COAT-01: bullet_point/);
 // An untouched attribute may differ.
 const other=await liveFile(dir,'TEST-COAT-01',body=>{body.item.attributes.item_name[0].value='Anders';});
 assert.equal((await build(dir,{rows:[['TEST-COAT-01','bullet_point.2.value','Neu']],lives:[other],base:['--export',exportFile]})).code,0);
}));

test('an agreeing get_listings copy is a base despite key order and parentAsins',async()=>withDir(async dir=>{
 const r=await build(dir,{rows:[['TEST-COAT-01','bullet_point.2.value','Neu'],['TEST-COAT-02','bullet_point.0.value','Neu zwei']],lives:[live('TEST-COAT-01'),live('TEST-COAT-02')],base:['--listings',fixture('get-listings.json')]});
 assert.equal(r.code,0,r.stdout);
 const batch=await loadJson(join(r.out,'batch.json'));
 assert.deepEqual(batch.items.map(i=>[i.index,i.sku,i.base_source,i.carried]),[[0,'TEST-COAT-01','agreeing_reads',true],[1,'TEST-COAT-02','agreeing_reads',true]]);
 const payload=await payloadOf(r.out);assert.ok(!('parentAsins' in payload.attributes));assert.equal(payload.attributes.bullet_point[4].value,'GESCHENK: Fünfter Punkt | mit Pipe');
 const body=await loadJson(fixture('get-listings.json'));body.listings[0].attributes.bullet_point[3].value='Veraltet';
 const stale=join(dir,'stale-listings.json');await writeFile(stale,JSON.stringify(body));
 assert.equal((await build(dir,{rows:[['TEST-COAT-01','bullet_point.2.value','Neu']],lives:[live('TEST-COAT-01')],base:['--listings',stale],out:join(dir,'batches','b2')})).json.reason,'stale_base');
 const missing=join(dir,'missing-listings.json');await writeFile(missing,JSON.stringify({...body,missingSkus:['TEST-COAT-01']}));
 assert.equal((await build(dir,{rows:[['TEST-COAT-01','bullet_point.2.value','Neu']],lives:[live('TEST-COAT-01')],base:['--listings',missing],out:join(dir,'batches','b3')})).json.reason,'sku_missing');
}));

test('number typing comes from the field definition or the existing leaf; booleans too',async()=>withDir(async dir=>{
 const r=await build(dir,{scope:'attributes',rows:[['TEST-COAT-01','item_package_weight.0.value','0.31'],['TEST-COAT-01','unit_count.0.value','2'],['TEST-COAT-01','is_fragile.0.value','true']],lives:[live('TEST-COAT-01')],base:['--export',exportFile],fields:[fieldsFile]});
 assert.equal(r.code,0,r.stdout);
 const a=(await payloadOf(r.out)).attributes;
 assert.strictEqual(a.item_package_weight[0].value,0.31);assert.equal(a.item_package_weight[0].unit,'kilograms');
 assert.strictEqual(a.unit_count[0].value,2);assert.deepEqual(a.unit_count[0].type,{value:'Stück',language_tag:'de_DE'});
 assert.strictEqual(a.is_fragile[0].value,true);
 // Without fields: the export leaf is a number, so the change stays a number.
 const plain=await build(dir,{scope:'attributes',rows:[['TEST-COAT-01','unit_count.0.value','3']],lives:[live('TEST-COAT-01')],base:['--export',exportFile],out:join(dir,'batches','b2')});
 assert.strictEqual((await payloadOf(plain.out)).attributes.unit_count[0].value,3);
 // Without fields the string leaf "0.26" keeps string type.
 const text=await build(dir,{scope:'attributes',rows:[['TEST-COAT-01','item_package_weight.0.value','0.4']],lives:[live('TEST-COAT-01')],base:['--export',exportFile],out:join(dir,'batches','b3')});
 assert.strictEqual((await payloadOf(text.out)).attributes.item_package_weight[0].value,'0.4');
 for(const [row,reason] of [[['TEST-COAT-01','item_package_weight.0.value','abc'],'invalid_value'],[['TEST-COAT-01','is_fragile.0.value','yes'],'invalid_value'],[['TEST-COAT-01','unit_count.0.type','Stück'],'invalid_value']]){
  const bad=await build(dir,{scope:'attributes',rows:[row],lives:[live('TEST-COAT-01')],base:['--export',exportFile],fields:[fieldsFile],out:join(dir,'batches','bad')});
  assert.equal(bad.json.reason,reason,row.join(' '));
 }
}));

test('new elements append with selectors; gaps and unknown structure are refused',async()=>withDir(async dir=>{
 const noGender=await keptLive(dir,'TEST-COAT-02',['target_gender']);
 const r=await build(dir,{scope:'attributes',rows:[['TEST-COAT-01','bullet_point.5.value','SECHS: Neuer Punkt'],['TEST-COAT-02','target_gender.0.value','male'],['TEST-COAT-02','unit_count.0.type.value','Paar']],lives:[live('TEST-COAT-01'),noGender],base:['--export',exportFile],fields:[fieldsFile]});
 assert.equal(r.code,0,r.stdout);
 const first=(await payloadOf(r.out,0)).attributes,second=(await payloadOf(r.out,1)).attributes;
 assert.equal(first.bullet_point.length,6);assert.deepEqual(first.bullet_point[5],{language_tag:'de_DE',marketplace_id:M,value:'SECHS: Neuer Punkt'});
 assert.deepEqual(second.target_gender,[{marketplace_id:M,value:'male'}]);
 assert.equal(second.unit_count[0].type.value,'Paar');assert.equal(second.unit_count[0].type.language_tag,'de_DE');
 const review=await readFile(join(r.out,'review.md'),'utf8');assert.match(review,/\| 5 \| value \|  \| SECHS: Neuer Punkt \| new \|/);
 // No base and no live array: structure must come from the definition.
 const nofields=await build(dir,{scope:'attributes',rows:[['TEST-COAT-02','target_gender.0.value','male']],lives:[noGender],out:join(dir,'batches','b2')});
 assert.equal(nofields.json.reason,'structure_unknown');
 const leaf=await build(dir,{scope:'attributes',rows:[['TEST-COAT-01','item_name.0.made_up_key','x']],lives:[live('TEST-COAT-01')],out:join(dir,'batches','b3')});
 assert.equal(leaf.json.reason,'structure_unknown');
 const gap=await build(dir,{rows:[['TEST-COAT-01','bullet_point.6.value','Lücke']],lives:[live('TEST-COAT-01')],base:['--export',exportFile],out:join(dir,'batches','b4')});
 assert.equal(gap.json.reason,'index_gap');
 // Contiguous appends are accepted in any row order.
 const two=await build(dir,{rows:[['TEST-COAT-01','bullet_point.6.value','Sieben'],['TEST-COAT-01','bullet_point.5.value','Sechs']],lives:[live('TEST-COAT-01')],base:['--export',exportFile],out:join(dir,'batches','b5')});
 assert.equal(two.code,0,two.stdout);assert.equal((await payloadOf(two.out)).attributes.bullet_point[6].value,'Sieben');
}));

test('values outside selectOptions need --allow-free-text and show as warnings',async()=>withDir(async dir=>{
 const rows=[['TEST-COAT-01','target_gender.0.value','divers']];
 const refused=await build(dir,{scope:'attributes',rows,lives:[live('TEST-COAT-01')],fields:[fieldsFile]});
 assert.equal(refused.json.reason,'free_text_unapproved');assert.match(refused.json.message,/--allow-free-text target_gender/);
 const r=await build(dir,{scope:'attributes',rows,lives:[live('TEST-COAT-01')],fields:[fieldsFile],extra:['--allow-free-text','target_gender']});
 assert.equal(r.code,0,r.stdout);assert.equal(r.json.warnings_count,1);
 const item=(await loadJson(join(r.out,'batch.json'))).items[0];
 assert.deepEqual(item.warnings,[{code:'not_in_select_options',attribute:'target_gender',path:'target_gender.0.value',value:'divers',options:['male','unisex','female']}]);
 assert.match(await readFile(join(r.out,'review.md'),'utf8'),/not_in_select_options: target_gender\.0\.value "divers"/);
 const ok=await build(dir,{scope:'attributes',rows:[['TEST-COAT-01','target_gender.0.value','unisex']],lives:[live('TEST-COAT-01')],fields:[fieldsFile],out:join(dir,'batches','b2')});
 assert.equal(ok.json.warnings_count,0);
}));

test('max_length and max_items come from the field definition',async()=>withDir(async dir=>{
 const long=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','x'.repeat(201)]],lives:[live('TEST-COAT-01')],fields:[fieldsFile]});
 assert.equal(long.json.reason,'max_length');assert.match(long.json.message,/201 characters; the field allows 200/);
 assert.equal((await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','ü'.repeat(200)]],lives:[live('TEST-COAT-01')],fields:[fieldsFile]})).code,0);
 const items=await build(dir,{rows:[['TEST-COAT-01','generic_keyword.1.value','zweite zeile']],lives:[live('TEST-COAT-01')],base:['--export',exportFile],fields:[fieldsFile],out:join(dir,'batches','b2')});
 assert.equal(items.json.reason,'max_items');
}));

test('build refusals leave no batch behind',async()=>withDir(async dir=>{
 const l1=live('TEST-COAT-01'),l2=live('TEST-COAT-02');
 const wrongSeller=await liveFile(dir,'TEST-COAT-01',b=>{b.sellerId='A2OTHERSELLER';});
 const wrongSource=await liveFile(dir,'TEST-COAT-01',b=>{b.source='FFP_SAVED';});
 const trimmed=await liveFile(dir,'TEST-COAT-01',b=>{b.kept_attributes=['bullet_point','main_product_image_locator','other_product_image_locator_1','other_product_image_locator_2','swatch_product_image_locator'];});
 const nope=await liveFile(dir,'TEST-COAT-01',b=>{b.item.sku='TEST-NOPE';});
 const old=await liveFile(dir,'TEST-COAT-01',b=>{b.item.sku='TEST-COAT-OLD';});
 const jacket=await liveFile(dir,'TEST-COAT-01',b=>{b.item.summaries[0].productType='JACKET';});
 const fieldsBody=await loadJson(fieldsFile),otherFields=join(dir,'fields-other.json');await writeFile(otherFields,JSON.stringify({...fieldsBody,sellerId:'A2OTHERSELLER'}));
 const httpImages=join(dir,'http.json');await writeFile(httpImages,JSON.stringify([{...images[0],url:'http://images.example.test/x.png'}]));
 const swatch=join(dir,'swatch.json');await writeFile(swatch,JSON.stringify([{...images[0],slot:'SWCH'}]));
 const dupImages=join(dir,'dup.json');await writeFile(dupImages,JSON.stringify([images[0],images[0]]));
 const bullet=['TEST-COAT-01','bullet_point.2.value','Neu'];
 const noType=await liveFile(dir,'TEST-COAT-01',b=>{b.item.summaries=[];});
 const listingsBody=await loadJson(fixture('get-listings.json')),foreignListings=join(dir,'foreign-listings.json');
 listingsBody.listings[0].seller_id='A2OTHERSELLER';await writeFile(foreignListings,JSON.stringify(listingsBody));
 const notJson=join(dir,'not-json.json');await writeFile(notJson,'not json');
 const cases=[
  ['export spelling',{rows:[['TEST-COAT-01','bullet_point__3__value','x']],lives:[l1]},'usage'],
  ['whole element',{rows:[['TEST-COAT-01','bullet_point.2','{"value":"x"}']],lives:[l1]},'usage'],
  ['images with changes',{scope:'images',rows:[bullet],lives:[l1]},'usage'],
  ['changes with images',{imagesFile:fixture('images.json'),lives:[l1,l2]},'usage'],
  ['two bases',{rows:[bullet],lives:[l1],base:['--export',exportFile,'--listings',fixture('get-listings.json')]},'usage'],
  ['unknown flag',{rows:[bullet],lives:[l1],extra:['--force']},'usage'],
  ['relationship',{scope:'attributes',rows:[['TEST-COAT-01','variation_theme.0.name','SIZE']],lives:[l1]},'relationship_field'],
  ['relationship by name',{scope:'attributes',rows:[['TEST-COAT-01','child_parent_sku_relationship.0.parent_sku','P']],lives:[l1]},'relationship_field'],
  ['parentage',{scope:'attributes',rows:[['TEST-COAT-01','parentage_level.0.value','child']],lives:[l1]},'relationship_field'],
  ['offer',{scope:'attributes',rows:[['TEST-COAT-01','purchasable_offer.0.our_price.0.schedule.0.value_with_tax','9.99']],lives:[l1]},'offer_field'],
  ['list price',{scope:'attributes',rows:[['TEST-COAT-01','list_price.0.value','9.99']],lives:[l1]},'offer_field'],
  ['identity',{scope:'attributes',rows:[['TEST-COAT-01','brand.0.value','Other']],lives:[l1]},'identity_field'],
  ['identifier',{scope:'attributes',rows:[['TEST-COAT-01','externally_assigned_product_identifier.0.value','123']],lives:[l1]},'identity_field'],
  ['seo scope',{rows:[['TEST-COAT-01','unit_count.0.value','2']],lives:[l1]},'scope_violation'],
  ['image locator in attributes',{scope:'attributes',rows:[['TEST-COAT-01','main_product_image_locator.0.media_location','https://images.example.test/a.png']],lives:[l1]},'scope_violation'],
  ['swatch locator',{scope:'attributes',rows:[['TEST-COAT-01','swatch_product_image_locator.0.media_location','https://images.example.test/a.png']],lives:[l1]},'scope_violation'],
  ['swatch slot',{scope:'images',imagesFile:swatch,lives:[l1]},'scope_violation'],
  ['empty value',{rows:[['TEST-COAT-01','item_name.0.value','   ']],lives:[l1]},'empty_value'],
  ['duplicate change',{rows:[bullet,['TEST-COAT-01','bullet_point.02.value','Doppelt']],lives:[l1],base:['--export',exportFile]},'duplicate_change'],
  ['duplicate image',{scope:'images',imagesFile:dupImages,lives:[l1]},'duplicate_change'],
  ['http image',{scope:'images',imagesFile:httpImages,lives:[l1]},'invalid_value'],
  ['live missing',{rows:[bullet,['TEST-COAT-02','item_name.0.value','x']],lives:[l1],base:['--export',exportFile]},'live_missing'],
  ['live duplicate',{rows:[bullet],lives:[l1,l1],base:['--export',exportFile]},'live_duplicate'],
  ['live for another SKU',{rows:[bullet],lives:[l1,l2],base:['--export',exportFile]},'live_mismatch'],
  ['live wrong seller',{rows:[bullet],lives:[wrongSeller],base:['--export',exportFile]},'live_mismatch'],
  ['live wrong source',{rows:[bullet],lives:[wrongSource],base:['--export',exportFile]},'live_mismatch'],
  ['live trimmed without a locator',{rows:[bullet],lives:[trimmed],base:['--export',exportFile]},'live_incomplete'],
  ['sku not in export',{rows:[['TEST-NOPE','item_name.0.value','x']],lives:[nope],base:['--export',exportFile]},'sku_missing'],
  ['archived sku',{rows:[['TEST-COAT-OLD','item_name.0.value','x']],lives:[old],base:['--export',exportFile]},'sku_archived'],
  ['fields for another seller',{rows:[bullet],lives:[l1],base:['--export',exportFile],fields:[otherFields]},'fields_mismatch'],
  ['product type mismatch',{rows:[bullet],lives:[jacket],base:['--export',exportFile]},'product_type_mismatch'],
  ['no product type anywhere',{rows:[['TEST-COAT-01','item_name.0.value','x']],lives:[noType]},'product_type_unknown'],
  ['listings for another seller',{rows:[bullet],lives:[l1],base:['--listings',foreignListings]},'account_mismatch'],
  ['live not JSON',{rows:[bullet],lives:[notJson]},'live_unreadable'],
 ];
 for(const [name,options,reason] of cases){
  const out=join(dir,'refused');const r=await build(dir,{...options,out});
  assert.equal(r.code,2,name+': '+r.stdout);assert.equal(r.json.status,'blocked');assert.equal(r.json.reason,reason,name+': '+r.json.message);
  assert.ok(!(await readdir(dir)).includes('refused'),name);
 }
 const export_spelling=await build(dir,{rows:[['TEST-COAT-01','bullet_point__3__value','x']],lives:[l1]});assert.match(export_spelling.json.message,/canonical attr\.N\.key/);
 // A trimmed live read that keeps every touched attribute and locator is complete.
 const kept=await liveFile(dir,'TEST-COAT-01',b=>{const keep=['bullet_point','main_product_image_locator','other_product_image_locator_1','other_product_image_locator_2','other_product_image_locator_3','other_product_image_locator_4','other_product_image_locator_5','other_product_image_locator_6','other_product_image_locator_7','other_product_image_locator_8','other_product_image_locator_9','swatch_product_image_locator'];b.kept_attributes=keep;b.item.attributes=Object.fromEntries(Object.entries(b.item.attributes).filter(([k])=>keep.includes(k)));});
 assert.equal((await build(dir,{rows:[bullet],lives:[kept],base:['--export',exportFile]})).code,0);
 const exists=join(dir,'occupied');await mkdir(exists);await writeFile(join(exists,'x'),'');
 assert.equal((await build(dir,{rows:[bullet],lives:[l1],base:['--export',exportFile],out:exists})).json.reason,'batch_exists');
}));

test('every write-path subcommand is attended_only under WIZARDS_AI_MODE; pending is read-only',async()=>withDir(async dir=>{
 const env={WIZARDS_AI_MODE:'1'};
 const b=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','x']],lives:[live('TEST-COAT-01')],deps:{env}});
 assert.equal(b.json.reason,'attended_only');assert.match(b.json.message,/attended only; Grimoire uses the workbook pipeline/);
 const ok=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','x']],lives:[live('TEST-COAT-01')]});
 for(const argv of [['approve','--batch',ok.out,'--approved-by','Operator'],['next','--batch',ok.out,'--live',live('TEST-COAT-01')],['record','--batch',ok.out,'--index','0','--no-response','--note','t'],['status','--batch',ok.out,'--index','0'],['verify','--batch',ok.out,'--index','0','--live',live('TEST-COAT-01')],['close','--batch',ok.out,'--index','0','--reason','r','--approved-by','Operator']])
  assert.equal((await run(argv,{env})).json.reason,'attended_only',argv[0]);
 assert.equal((await run(['pending','--root',dirname(ok.out)],{env})).json.status,'pending');
 assert.match(await readFile(source,'utf8'),/'attended_only'/);
}));

test('MAIN images need the main review at approve; images payloads carry nothing',async()=>withDir(async dir=>{
 const r=await build(dir,{scope:'images',imagesFile:fixture('images.json'),lives:[live('TEST-COAT-01'),live('TEST-COAT-02')]});
 assert.equal(r.code,0,r.stdout);
 const batch=await loadJson(join(r.out,'batch.json'));
 assert.deepEqual((await payloadOf(r.out,0)).attributes,{other_product_image_locator_2:[{marketplace_id:M,media_location:images[0].url}]});
 assert.deepEqual((await payloadOf(r.out,1)).attributes,{main_product_image_locator:[{marketplace_id:M,media_location:images[1].url}]});
 assert.deepEqual(batch.items[0].images,[{slot:'PT02',attribute:'other_product_image_locator_2',sha256:images[0].artifact.sha256,url:images[0].url,before:'https://m.media-amazon.com/images/I/61TESTPT0201.jpg'}]);
 assert.deepEqual(batch.items[1].main_image_sha256,[images[1].artifact.sha256]);assert.equal(batch.items[1].base_source,'none');assert.equal(batch.items[1].carried,false);
 assert.deepEqual(batch.inputs.images,{path:fixture('images.json'),sha256:sha(await readFile(fixture('images.json')))});
 const review=await readFile(join(r.out,'review.md'),'utf8');
 assert.match(review,new RegExp(`\\| MAIN \\| main_product_image_locator \\| ${images[1].artifact.sha256} \\| ${images[1].url} \\| https://m.media-amazon.com/images/I/61TESTMAIN02.jpg \\|`));
 // The live issue message URL is redacted; only image URLs are kept.
 assert.match(review,/\[redacted-url\]/);assert.ok(!review.includes('sellercentral.amazon.de'));assert.ok(!JSON.stringify(batch).includes('sellercentral.amazon.de'));
 const approve=extra=>run(['approve','--batch',r.out,'--approved-by','Operator',...extra]);
 assert.equal((await approve([])).json.reason,'main_review_required');
 const reviewFile=async body=>{const path=join(dir,'main-'+Math.random().toString(16).slice(2)+'.json');await writeFile(path,JSON.stringify(body));return path;};
 const good={approved_by:'Operator',approved_at:'2026-10-29T11:00:00+01:00',image_sha256:[images[1].artifact.sha256]};
 for(const body of [{...good,image_sha256:[images[0].artifact.sha256]},{...good,approved_at:'2026-10-30T11:00:00Z'},{...good,approved_at:'2026-10-29T11:00:00'},{...good,approved_at:'2026-10-28T20:00:00Z'},{...good,extra:true},{...good,image_sha256:[]}])
  assert.equal((await approve(['--main-review',await reviewFile(body)])).json.reason,'main_review_required',JSON.stringify(body));
 const ok=await approve(['--main-review',await reviewFile(good)]);
 assert.equal(ok.code,0,ok.stdout);assert.deepEqual(ok.json,{status:'approved',batch_sha256:batch&&r.json.batch_sha256,items:2,approved_by:'Operator'});
 const event=(await ledger(r.out)).at(-1);assert.equal(event.event,'approved');assert.equal(event.approved_at,'2026-10-29T12:00:00.000Z');assert.deepEqual(event.main_review.image_sha256,good.image_sha256);
 assert.equal((await approve([])).json.reason,'already_approved');
 const n=await nextItem(r.out,'TEST-COAT-01');assert.equal(n.json.status,'next');assert.equal(n.json.index,0);
 // The review (10:00Z) runs out before the approval (12:00Z); renewal opens as soon as it does.
 const late=()=>Date.parse('2026-10-29T23:00:00.000Z');
 const aged=await nextItem(r.out,'TEST-COAT-01',{now:late});assert.equal(aged.json.reason,'approval_expired');assert.match(aged.json.message,/MAIN review/);
 assert.equal((await run(['approve','--batch',r.out,'--approved-by','Operator','--main-review',await reviewFile(good)],{now:late})).json.reason,'main_review_required');
 const renewed=await run(['approve','--batch',r.out,'--approved-by','Operator','--main-review',await reviewFile({...good,approved_at:'2026-10-29T22:30:00Z'})],{now:late});
 assert.equal(renewed.code,0,renewed.stdout);assert.equal(renewed.json.renewed,true);
 assert.equal((await nextItem(r.out,'TEST-COAT-01',{now:late})).json.index,0);
}));

test('next and record sequence one payload at a time with a first-item hold',async()=>withDir(async dir=>{
 const r=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Neuer Titel eins'],['TEST-COAT-02','item_name.0.value','Neuer Titel zwei'],['-TEST-COAT-03','item_name.0.value','Neuer Titel drei']],lives:[live('TEST-COAT-01'),live('TEST-COAT-02'),live('-TEST-COAT-03')]});
 assert.equal(r.code,0,r.stdout);assert.equal(r.json.items,3);
 assert.equal((await nextItem(r.out,'TEST-COAT-01')).json.reason,'not_approved');
 assert.equal((await run(['approve','--batch',r.out,'--approved-by','Operator'])).code,0);
 assert.equal((await run(['next','--batch',r.out])).json.reason,'usage');
 const first=await nextItem(r.out,'TEST-COAT-01'),again=await nextItem(r.out,'TEST-COAT-01');
 assert.equal(first.stdout,again.stdout);assert.equal(first.stdout.trim().split('\n').length,1);
 assert.deepEqual(Object.keys(first.json),['status','index','sku','payload_sha256','tool','arguments']);
 assert.equal(first.json.tool,'flatfilepro_update_listing_on_amazon');assert.deepEqual(first.json.arguments,await payloadOf(r.out,0));
 assert.equal((await run(['record','--batch',r.out,'--index','1'],{readStdin:response()})).json.reason,'out_of_order');
 const rec=await run(['record','--batch',r.out,'--index','0'],{readStdin:async()=>JSON.stringify({result:{status:'ACCEPTED',runId:101,runItemId:'202',pollAfterSeconds:1800}})});
 assert.equal(rec.code,0,rec.stdout);
 assert.equal(rec.json.event,'submitted');assert.equal(rec.json.runId,'101');assert.equal(rec.json.runItemId,'202');assert.equal(rec.json.status,'ACCEPTED');assert.equal(rec.json.pollAfterSeconds,1800);assert.equal(rec.json.run_ids_missing,false);
 assert.equal(await readFile(rec.json.response_file,'utf8'),JSON.stringify({result:{status:'ACCEPTED',runId:101,runItemId:'202',pollAfterSeconds:1800}}));
 assert.equal((await run(['record','--batch',r.out,'--index','0'],{readStdin:response()})).json.reason,'already_recorded');
 const held=await nextItem(r.out,'TEST-COAT-02');assert.equal(held.code,2);assert.equal(held.json.status,'held');assert.equal(held.json.reason,'first_item_unverified');
 // Verify the first item: content landed, status not yet SUCCEEDED.
 const after=await liveFile(dir,'TEST-COAT-01',b=>{b.item.attributes.item_name=[{language_tag:'de_DE',value:'Neuer Titel eins ',marketplace_id:M}];});
 const v=await run(['verify','--batch',r.out,'--index','0','--live',after]);
 assert.equal(v.code,0,v.stdout);assert.equal(v.json.state,'landed_status_pending');
 assert.equal((await nextItem(r.out,'TEST-COAT-01')).json.reason,'live_mismatch');
 const second=await nextItem(r.out,'TEST-COAT-02');assert.equal(second.json.index,1);assert.equal(second.json.sku,'TEST-COAT-02');
 const unknown=await run(['record','--batch',r.out,'--sku','TEST-COAT-02','--no-response','--note','tool timed out']);
 assert.equal(unknown.json.status,'UNKNOWN');assert.equal(unknown.json.run_ids_missing,true);assert.equal(unknown.json.note,'tool timed out');
 // An UNKNOWN is never offered again; a dash-prefixed SKU is a value.
 const third=await nextItem(r.out,'-TEST-COAT-03');assert.equal(third.json.sku,'-TEST-COAT-03');
 assert.equal((await run(['record','--batch',r.out,'--sku','-TEST-COAT-03','--no-response'])).json.reason,'usage');
 const odd=await run(['record','--batch',r.out,'--sku','-TEST-COAT-03'],{readStdin:async()=>'Tool error: upstream 502'});
 assert.equal(odd.code,0);assert.equal(odd.json.status,null);assert.equal(odd.json.run_ids_missing,true);
 assert.deepEqual((await nextItem(r.out,'-TEST-COAT-03')).json,{status:'complete',batch_sha256:r.json.batch_sha256,items:3});
}));

test('a response naming another SKU is recorded and then blocks',async()=>withDir(async dir=>{
 const r=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','x']],lives:[live('TEST-COAT-01')]});
 await run(['approve','--batch',r.out,'--approved-by','Operator']);
 const out=await run(['record','--batch',r.out,'--index','0'],{readStdin:response('5','6',{sku:'TEST-COAT-02'})});
 assert.equal(out.code,2);assert.equal(out.json.reason,'response_sku_mismatch');assert.equal(out.json.event.response_sku_mismatch,true);
 assert.equal((await ledger(r.out)).at(-1).event,'submitted');
 assert.equal((await run(['record','--batch',r.out,'--index','0'],{readStdin:response()})).json.reason,'already_recorded');
}));

test('status needs the run IDs, refuses another run and saves the raw result',async()=>withDir(async dir=>{
 const r=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','x'],['TEST-COAT-02','item_name.0.value','y']],lives:[live('TEST-COAT-01'),live('TEST-COAT-02')]});
 await run(['approve','--batch',r.out,'--approved-by','Operator']);
 assert.equal((await run(['status','--batch',r.out,'--index','0'],{readStdin:async()=>'{}'})).json.reason,'status_without_run');
 await run(['record','--batch',r.out,'--index','0'],{readStdin:response()});
 assert.equal((await run(['status','--batch',r.out,'--index','0'],{readStdin:async()=>JSON.stringify({runId:'999',runItemId:'202',status:'SUCCEEDED'})})).json.reason,'status_mismatch');
 const raw=JSON.stringify([{type:'text',text:JSON.stringify({runId:'101',runItemId:'202',status:'PROCESSING',terminal:false,attributes:[{name:'item_name',status:'PENDING'}]})}]);
 const s=await run(['status','--batch',r.out,'--index','0'],{readStdin:async()=>raw});
 assert.equal(s.code,0,s.stdout);assert.equal(s.json.event,'status');assert.equal(s.json.status,'PROCESSING');assert.equal(s.json.terminal,false);
 assert.ok(s.json.raw_file.endsWith('status/000-1.json'));assert.equal(await readFile(s.json.raw_file,'utf8'),raw);
 const done=await run(['status','--batch',r.out,'--index','0'],{readStdin:async()=>JSON.stringify({runId:'101',runItemId:'202',outcome:'SUCCEEDED'})});
 assert.equal(done.json.outcome,'SUCCEEDED');assert.equal(done.json.terminal,true);assert.ok(done.json.raw_file.endsWith('status/000-2.json'));
 await run(['record','--batch',r.out,'--index','1','--no-response','--note','timeout']);
 assert.equal((await run(['status','--batch',r.out,'--index','1'],{readStdin:async()=>'{}'})).json.reason,'status_without_run');
}));

async function submitted(dir,options,{approve=true,stdin=response()}={}){
 const r=await build(dir,options);assert.equal(r.code,0,r.stdout);
 if(approve)assert.equal((await run(['approve','--batch',r.out,'--approved-by','Operator'])).code,0);
 const rec=await run(['record','--batch',r.out,'--index','0'],{readStdin:stdin});assert.equal(rec.code,0,rec.stdout);
 return r;
}
const succeeded=out=>run(['status','--batch',out,'--index','0'],{readStdin:async()=>JSON.stringify({runId:'101',runItemId:'202',status:'SUCCEEDED',terminal:true})});

test('verify normalises key order, string numbers and trimmed text, and reports mismatches',async()=>withDir(async dir=>{
 const r=await submitted(dir,{scope:'attributes',rows:[['TEST-COAT-01','item_package_weight.0.value','0.31'],['TEST-COAT-01','unit_count.0.value','2'],['TEST-COAT-01','bullet_point.2.value','Neu drei']],lives:[live('TEST-COAT-01')],base:['--export',exportFile],fields:[fieldsFile]});
 const after=await liveFile(dir,'TEST-COAT-01',b=>{const a=b.item.attributes;a.item_package_weight=[{value:'0.31',marketplace_id:M,unit:'kilograms'}];a.unit_count[0].value='2.0';a.bullet_point[2].value='  Neu drei';});
 const pending=await run(['verify','--batch',r.out,'--index','0','--live',after]);
 assert.equal(pending.code,0,pending.stdout);assert.equal(pending.json.state,'landed_status_pending');
 assert.deepEqual(pending.json.attributes.map(a=>a.result),['match','match','match']);
 assert.ok(pending.json.protected_slots.every(p=>p.result==='preserved'));assert.deepEqual(pending.json.pixel_checks,[]);
 assert.ok(pending.json.verify_file.endsWith('verify/000-1.json'));assert.deepEqual(await loadJson(pending.json.verify_file),{...pending.json});
 await succeeded(r.out);
 const done=await run(['verify','--batch',r.out,'--index','0','--live',after]);assert.equal(done.code,0);assert.equal(done.json.state,'verified');assert.ok(done.json.verify_file.endsWith('verify/000-2.json'));
 const wrong=await liveFile(dir,'TEST-COAT-01',b=>{const a=b.item.attributes;a.item_package_weight=[{value:'0.31',marketplace_id:M,unit:'kilograms'}];a.unit_count[0].value='2';a.bullet_point[2].value='Alt';});
 const bad=await run(['verify','--batch',r.out,'--index','0','--live',wrong]);
 assert.equal(bad.code,3);assert.equal(bad.json.state,'mismatch');assert.deepEqual(bad.json.attributes.map(a=>a.result),['match','match','mismatch']);
 const miss=bad.json.attributes.find(a=>a.result==='mismatch');assert.equal(miss.attribute,'bullet_point');assert.equal(miss.expected[2].value,'Neu drei');assert.equal(miss.actual[2].value,'Alt');
 const events=(await ledger(r.out)).filter(e=>e.event==='verify');assert.deepEqual(events.map(e=>e.state),['landed_status_pending','verified','mismatch']);
 const other=await liveFile(dir,'TEST-COAT-02');assert.equal((await run(['verify','--batch',r.out,'--index','0','--live',other])).json.reason,'live_mismatch');
}));

test('image verify: changed, not_yet, missing, protected slots, new media_locator issues and pixels',async()=>withDir(async dir=>{
 const img=JSON.parse(JSON.stringify(images[0])),file=join(dir,'images.json');await writeFile(file,JSON.stringify([img]));
 const r=await submitted(dir,{scope:'images',imagesFile:file,lives:[live('TEST-COAT-01')]});
 const newUrl='https://m.media-amazon.com/images/I/71NEWPT02.jpg';
 const variant=mutate=>liveFile(dir,'TEST-COAT-01',b=>{b.item.attributes.other_product_image_locator_2=[{marketplace_id:M,media_location:newUrl}];mutate(b);});
 const verify=async(path,extra=[])=>run(['verify','--batch',r.out,'--index','0','--live',path,...extra]);
 const changed=await verify(await variant(b=>{b.item.issues.push({code:'18027',message:'Bild https://example.test/x',severity:'WARNING',attributeNames:['media_locator'],categories:[]},{code:'90300',message:'Andere',severity:'WARNING',attributeNames:['material'],categories:[]});}));
 assert.equal(changed.code,0,changed.stdout);assert.equal(changed.json.state,'landed_pixels_unchecked');
 assert.deepEqual(changed.json.images.map(i=>[i.slot,i.result,i.after]),[['PT02','changed',newUrl]]);
 assert.deepEqual(changed.json.issues_new.map(i=>i.code),['18027']);assert.equal(changed.json.issues_new_flag,true);assert.ok(!changed.stdout.includes('example.test/x'));
 assert.deepEqual(changed.json.pixel_checks,[{sku:'TEST-COAT-01',slot:'PT02',attribute:'other_product_image_locator_2',amazon_url:newUrl,image_sha256:img.artifact.sha256,before_url:'https://m.media-amazon.com/images/I/61TESTPT0201.jpg',confirmed:false,result:'unchecked'}]);
 const pixels=(match,thresholds)=>pixelsFile(dir,[{sku:'TEST-COAT-01',slot:'PT02',amazon_url:newUrl,image_sha256:img.artifact.sha256,match,dhash_distance:2}],thresholds);
 await succeeded(r.out);
 const plain=await variant(()=>{});
 // IMAGE-1: a rejected pixel check is its own failing state.
 const rejected=await verify(plain,['--pixels',await pixels(false)]);
 assert.equal(rejected.code,3);assert.equal(rejected.json.state,'pixels_mismatch');assert.equal(rejected.json.pixel_checks[0].result,'rejected');
 assert.match((await pendingOf(dirname(r.out),r.out)).next_action,/is not the archived PNG.*close this item/);
 assert.match((await pendingOf(dirname(r.out),r.out)).next_action,/discriminating false.*close --landed/);
 // IMAGE-4: thresholds must be present and no looser than the pinned ones.
 for(const thresholds of [null,{...PIXEL_THRESHOLDS,max_dhash:64},{...PIXEL_THRESHOLDS,max_aspect_delta:10},{max_dhash:24,max_aspect_delta:0.02},{...PIXEL_THRESHOLDS,max_color_delta:'12'}])
  assert.equal((await verify(plain,['--pixels',await pixels(true,thresholds)])).json.reason,'pixels_thresholds',JSON.stringify(thresholds));
 assert.equal((await verify(plain,['--pixels',await pixels(true,{max_dhash:10,max_aspect_delta:0.01,max_color_delta:6})])).json.state,'verified');
 const confirmed=await verify(plain,['--pixels',await pixels(true)]);assert.equal(confirmed.json.state,'verified');assert.equal(confirmed.json.pixel_checks[0].confirmed,true);
 const notYet=await verify(live('TEST-COAT-01'));assert.equal(notYet.code,3);assert.equal(notYet.json.state,'not_yet');
 const gone=await verify(await liveFile(dir,'TEST-COAT-01',b=>{delete b.item.attributes.other_product_image_locator_2;}));assert.equal(gone.json.state,'mismatch');assert.equal(gone.json.images[0].result,'missing');
 const moved=await verify(await variant(b=>{b.item.attributes.other_product_image_locator_1[0].media_location='https://m.media-amazon.com/images/I/71MOVED.jpg';}));
 assert.equal(moved.code,3);assert.equal(moved.json.state,'mismatch');
 assert.deepEqual(moved.json.protected_slots.filter(p=>p.result!=='preserved').map(p=>[p.attribute,p.result]),[['other_product_image_locator_1','protected_slot_changed']]);
}));

test('submission_pending holds another batch on the same SKU and attribute until close',async()=>withDir(async dir=>{
 const root=join(dir,'batches'),rows=[['TEST-COAT-01','item_name.0.value','Titel A']];
 const a=await submitted(dir,{rows,lives:[live('TEST-COAT-01')],out:join(root,'a')});
 const blocked=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Titel B']],lives:[live('TEST-COAT-01')],out:join(root,'b')});
 assert.equal(blocked.json.reason,'submission_pending');assert.match(blocked.json.message,/batches\/a item 0/);
 // Another attribute on the same SKU is not blocked.
 assert.equal((await build(dir,{rows:[['TEST-COAT-01','generic_keyword.0.value','neu']],lives:[live('TEST-COAT-01')],out:join(root,'c')})).code,0);
 assert.equal((await run(['close','--batch',a.out,'--index','1','--reason','x','--approved-by','Operator'])).json.reason,'item_missing');
 const closed=await run(['close','--batch',a.out,'--index','0','--reason','Live read shows the write never landed','--approved-by','Operator']);
 assert.equal(closed.code,0,closed.stdout);assert.equal(closed.json.status,'closed');assert.equal(closed.json.void,undefined);
 assert.equal((await run(['close','--batch',a.out,'--index','0','--reason','again','--approved-by','Operator'])).json.reason,'already_closed');
 assert.equal((await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Titel B']],lives:[live('TEST-COAT-01')],out:join(root,'b')})).code,0);
 // A batch approved before the other one's write was recorded is held at next.
 const d=await build(dir,{rows:[['TEST-COAT-02','item_name.0.value','D']],lives:[live('TEST-COAT-02')],out:join(root,'d')});
 const e=await build(dir,{rows:[['TEST-COAT-02','item_name.0.value','E']],lives:[live('TEST-COAT-02')],out:join(root,'e')});
 assert.equal((await run(['approve','--batch',e.out,'--approved-by','Operator'])).code,0);
 await run(['record','--batch',d.out,'--index','0'],{readStdin:response()});
 const held=await nextItem(e.out,'TEST-COAT-02');assert.equal(held.json.reason,'submission_pending');assert.match(held.json.message,/open submission in batch .*batches\/d item 0/);
}));

test('approved but unsubmitted items block overlapping build and approve until voided (DOCS-2)',async()=>withDir(async dir=>{
 const root=join(dir,'batches'),kw=value=>({rows:[['TEST-COAT-02','generic_keyword.0.value',value]],lives:[live('TEST-COAT-02')]});
 const h=await build(dir,{...kw('h'),out:join(root,'h')}),i=await build(dir,{...kw('i'),out:join(root,'i')});
 assert.equal((await run(['approve','--batch',h.out,'--approved-by','Operator'])).code,0);
 const refused=await run(['approve','--batch',i.out,'--approved-by','Operator']);
 assert.equal(refused.json.reason,'submission_pending');assert.match(refused.json.message,/approved, unsubmitted item in batch .*batches\/h item 0; submit and verify it, or close it \(void\)/);
 assert.equal((await build(dir,{...kw('j'),out:join(root,'j')})).json.reason,'submission_pending');
 // A built but unapproved batch blocks nothing.
 assert.equal((await build(dir,{rows:[['TEST-COAT-02','item_name.0.value','k']],lives:[live('TEST-COAT-02')],out:join(root,'k')})).code,0);
 const voided=await run(['close','--batch',h.out,'--index','0','--reason','superseded','--approved-by','Operator']);
 assert.equal(voided.code,0,voided.stdout);assert.equal(voided.json.void,true);
 assert.equal((await nextItem(h.out,'TEST-COAT-02')).json.status,'complete');
 assert.ok(!(await run(['pending','--root',root])).json.items.some(x=>x.batch===h.out));
 assert.equal((await run(['approve','--batch',i.out,'--approved-by','Operator'])).code,0);
}));

test('pending lists every unfinished item with its next action',async()=>withDir(async dir=>{
 const root=join(dir,'batches'),one=sku=>({rows:[[sku,'item_name.0.value','Titel '+sku]],lives:[live(sku)]});
 await build(dir,{...one('TEST-COAT-01'),out:join(root,'1-built')});
 const approved=await build(dir,{...one('TEST-COAT-02'),out:join(root,'2-approved')});await run(['approve','--batch',approved.out,'--approved-by','Operator']);
 await submitted(dir,{...one('-TEST-COAT-03'),out:join(root,'3-submitted')});
 const unknownBatch=await build(dir,{rows:[['TEST-COAT-01','generic_keyword.0.value','x']],lives:[live('TEST-COAT-01')],out:join(root,'4-unknown')});
 await run(['approve','--batch',unknownBatch.out,'--approved-by','Operator']);await run(['record','--batch',unknownBatch.out,'--index','0','--no-response','--note','timeout']);
 const polled=await submitted(dir,{rows:[['TEST-COAT-02','generic_keyword.0.value','y']],lives:[live('TEST-COAT-02')],out:join(root,'5-polled')});
 await run(['status','--batch',polled.out,'--index','0'],{readStdin:async()=>JSON.stringify({runId:'101',runItemId:'202',status:'IN_PROGRESS'})});
 const verified=await submitted(dir,{rows:[['-TEST-COAT-03','bullet_point.0.value','Erster Punkt neu'],['-TEST-COAT-03','bullet_point.1.value','Zweiter Punkt neu']],lives:[live('-TEST-COAT-03')],out:join(root,'6-verified')});
 await succeeded(verified.out);
 const after=await liveFile(dir,'-TEST-COAT-03',b=>{b.item.attributes.bullet_point[0].value='Erster Punkt neu';b.item.attributes.bullet_point[1].value='Zweiter Punkt neu';});
 assert.equal((await run(['verify','--batch',verified.out,'--index','0','--live',after])).json.state,'verified');
 const out=await run(['pending','--root',root]);
 assert.equal(out.code,0,out.stdout);
 assert.deepEqual(out.json.items.map(i=>[i.batch.split('/').pop(),i.index,i.sku,i.state]),[['1-built',0,'TEST-COAT-01','built'],['2-approved',0,'TEST-COAT-02','approved_not_submitted'],['3-submitted',0,'-TEST-COAT-03','submitted'],['4-unknown',0,'TEST-COAT-01','unknown'],['5-polled',0,'TEST-COAT-02','status_nonterminal']]);
 const polledItem=out.json.items[4];assert.equal(polledItem.runId,'101');assert.equal(polledItem.runItemId,'202');assert.equal(polledItem.last_status,'IN_PROGRESS');
 assert.ok(out.json.items.every(i=>typeof i.next_action==='string'&&i.next_action));
}));

test('batch_changed when a payload or batch.json is edited after build or approval',async()=>withDir(async dir=>{
 const r=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Titel']],lives:[live('TEST-COAT-01')]});
 await run(['approve','--batch',r.out,'--approved-by','Operator']);
 const path=join(r.out,'payloads','000.json'),original=await readFile(path,'utf8');
 await writeFile(path,original.replace('Titel','Anderer Titel'));
 assert.equal((await nextItem(r.out,'TEST-COAT-01')).json.reason,'batch_changed');
 await writeFile(path,original);assert.equal((await nextItem(r.out,'TEST-COAT-01')).json.status,'next');
 const batchPath=join(r.out,'batch.json'),batchText=await readFile(batchPath,'utf8');
 await writeFile(batchPath,batchText.replace('"scope": "seo"','"scope": "attributes"'));
 assert.equal((await nextItem(r.out,'TEST-COAT-01')).json.reason,'batch_changed');
 assert.equal((await run(['approve','--batch',r.out,'--approved-by','Operator'])).json.reason,'batch_changed');
}));

test('build registers every batch file as preserve and survives a registration failure',async()=>withDir(async dir=>{
 const seen=[];
 const ok=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Titel']],lives:[live('TEST-COAT-01')],extra:['--register-run','run_test'],deps:{artifactctl:args=>{seen.push(args);return {status:0,stdout:JSON.stringify({id:'art_'+seen.length,state:'preserved'}),stderr:''};}}});
 assert.equal(ok.code,0,ok.stdout);assert.equal(ok.json.registration,'registered');
 assert.deepEqual(seen.map(args=>args[4].slice(ok.out.length+1)),['batch.json','batch.sha256','review.md','payloads/000.json','ledger.jsonl']);
 assert.ok(seen.every(args=>args[0]==='register'&&args[2]==='run_test'&&args[6]==='preserve'));assert.match(ok.json.registration_note,/append-only/);
 const failed=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Titel']],lives:[live('TEST-COAT-01')],out:join(dir,'batches','b2'),extra:['--register-run','run_missing'],deps:{artifactctl:()=>({status:1,stdout:'',stderr:'unknown run: run_missing'})}});
 assert.equal(failed.code,0);assert.equal(failed.json.registration,'failed');assert.match(failed.json.registration_message,/unknown run/);
}));

test('usage errors are blocked JSON with exit 2',async()=>{
 for(const argv of [[],['nope'],['next'],['approve','--batch','x'],['record','--batch','x','--index','0','--sku','A'],['pending'],['next','--batch','x','--force'],['build','--scope','seo']]){
  const out=await run(argv);assert.equal(out.code,2,JSON.stringify(argv));assert.equal(out.json.status,'blocked');
 }
 assert.equal((await run(['next','--batch'])).json.reason,'usage');
 assert.equal((await run(['pending','--root=/nonexistent-ffp-root'])).json.reason,'usage');
});

test('changes apply in full path order, so nested appends need no row order (LOGIC-7)',async()=>withDir(async dir=>{
 const withList=await liveFile(dir,'TEST-COAT-01',b=>{b.item.attributes.x_feature=[{marketplace_id:M,list:['a']}];});
 const rows=[['TEST-COAT-01','x_feature.0.list.2','c'],['TEST-COAT-01','x_feature.0.list.0','z'],['TEST-COAT-01','x_feature.0.list.1','b']];
 const r=await build(dir,{scope:'attributes',rows,lives:[withList]});
 assert.equal(r.code,0,r.stdout);assert.deepEqual((await payloadOf(r.out)).attributes.x_feature,[{marketplace_id:M,list:['z','b','c']}]);
}));

test('offer fields and offer image locators are refused; any image locator is refused in scope attributes (SAFETY-3)',async()=>withDir(async dir=>{
 const offers=['condition_type.0.value','condition_note.0.value','max_order_quantity.0.value','product_tax_code.0.value','skip_offer.0.value','merchant_release_date.0.value','uvp_list_price.0.value',
  'min_seller_allowed_price.0.value','max_seller_allowed_price.0.value','main_offer_image_locator.0.media_location','other_offer_image_locator_1.0.media_location','fulfillment_availability.0.quantity','purchasable_offer.0.currency','merchant_shipping_group.0.value'];
 for(const attr of offers)for(const scope of ['attributes','seo']){
  const r=await build(dir,{scope,rows:[['TEST-COAT-01',attr,'1']],lives:[live('TEST-COAT-01')],out:join(dir,'refused')});
  assert.equal(r.json.reason,'offer_field',scope+' '+attr);
 }
 const locator=await build(dir,{scope:'attributes',rows:[['TEST-COAT-01','future_product_image_locator_2.0.media_location','https://x.test/a.jpg']],lives:[live('TEST-COAT-01')],out:join(dir,'refused')});
 assert.equal(locator.json.reason,'scope_violation');
 assert.ok(!(await readdir(dir)).includes('refused'));
}));

test('build refuses a change that equals the live value (SAFETY-2 no_op_change)',async()=>withDir(async dir=>{
 const title=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Testmantel Damen Wolle Grau']],lives:[live('TEST-COAT-01')]});
 assert.equal(title.json.reason,'no_op_change');assert.match(title.json.message,/TEST-COAT-01: item_name/);
 const count=await build(dir,{scope:'attributes',rows:[['TEST-COAT-01','unit_count.0.value','1']],lives:[live('TEST-COAT-01')],base:['--export',exportFile]});
 assert.equal(count.json.reason,'no_op_change');
}));

test('a live read without kept_attributes must hold every touched attribute (WHOLE-1)',async()=>withDir(async dir=>{
 const trimmed=await liveFile(dir,'TEST-COAT-01',b=>{delete b.item.attributes.bullet_point;delete b.item.attributes.other_product_image_locator_2;});
 const r=await build(dir,{rows:[['TEST-COAT-01','bullet_point.0.value','Neuer erster Punkt']],lives:[trimmed]});
 assert.equal(r.json.reason,'live_incomplete');assert.match(r.json.message,/has no bullet_point; list it in kept_attributes to assert it is absent on Amazon/);
 // An empty image slot is written only with a read that asserts it is empty.
 const pt05=await writeJson(dir,'images',[imageEntry('TEST-COAT-01','PT05',sha('pt05'))]);
 assert.equal((await build(dir,{scope:'images',imagesFile:pt05,lives:[live('TEST-COAT-01')]})).json.reason,'live_incomplete');
 assert.equal((await build(dir,{scope:'images',imagesFile:pt05,lives:[await keptLive(dir,'TEST-COAT-01')]})).code,0);
}));

test('images build binds the hosted URL to the artifact SHA-256 (IMAGE-3)',async()=>withDir(async dir=>{
 const digest=sha('pt02'),other=sha('other');
 for(const url of [`https://images.example.test/ffp-test/${digest}.png`,`https://res.cloudinary.com/testcloud/image/upload/v1/ffp-test/${other}.png`,`https://res.cloudinary.com/testcloud/image/upload/v1/ffp-test/${digest}.jpg`,`https://res.cloudinary.com.evil.test/x/${digest}.png`]){
  const file=await writeJson(dir,'images',[{...imageEntry('TEST-COAT-01','PT02',digest),url}]);
  const r=await build(dir,{scope:'images',imagesFile:file,lives:[live('TEST-COAT-01')],out:join(dir,'refused')});
  assert.equal(r.json.reason,'invalid_value',url);assert.match(r.json.message,/res\.cloudinary\.com/);
 }
 const ok=await writeJson(dir,'images',[imageEntry('TEST-COAT-01','PT02',digest)]);
 assert.equal((await build(dir,{scope:'images',imagesFile:ok,lives:[live('TEST-COAT-01')]})).code,0);
}));

test('next needs a fresh live read equal to the build before-read (SAFETY-1, WHOLE-1)',async()=>withDir(async dir=>{
 const root=join(dir,'batches'),bullet=(i,value)=>({rows:[['TEST-COAT-01',`bullet_point.${i}.value`,value]],lives:[live('TEST-COAT-01')],base:['--export',exportFile]});
 const a=await build(dir,{...bullet(1,'A-CHANGE'),out:join(root,'a')}),b=await build(dir,{...bullet(3,'B-CHANGE'),out:join(root,'b')});
 await run(['approve','--batch',a.out,'--approved-by','Operator']);
 const edited=await liveFile(dir,'TEST-COAT-01',x=>{x.item.attributes.bullet_point[1].value='Anders in Seller Central';});
 const stale=await run(['next','--batch',a.out,'--live',edited]);
 assert.equal(stale.json.reason,'stale_base');assert.match(stale.json.message,/TEST-COAT-01: bullet_point changed on Amazon/);
 const untouched=await liveFile(dir,'TEST-COAT-01',x=>{x.item.attributes.item_name[0].value='Anderer Titel';});
 assert.equal((await run(['next','--batch',a.out,'--live',untouched])).json.status,'next');
 const trimmed=await liveFile(dir,'TEST-COAT-01',x=>{delete x.item.attributes.bullet_point;});
 assert.equal((await run(['next','--batch',a.out,'--live',trimmed])).json.reason,'live_incomplete');
 const foreign=await liveFile(dir,'TEST-COAT-01',x=>{x.marketplaceId='A13V1IB3VIYZZH';});
 assert.equal((await run(['next','--batch',a.out,'--live',foreign])).json.reason,'live_mismatch');
 // Batch A lands; batch B was built on the old bullets and must not undo A.
 await run(['record','--batch',a.out,'--index','0'],{readStdin:response()});await succeeded(a.out);
 const landed=await liveFile(dir,'TEST-COAT-01',x=>{x.item.attributes.bullet_point[1].value='A-CHANGE';});
 assert.equal((await run(['verify','--batch',a.out,'--index','0','--live',landed])).json.state,'verified');
 assert.equal((await run(['approve','--batch',b.out,'--approved-by','Operator'])).code,0);
 const reverted=await run(['next','--batch',b.out,'--live',landed]);
 assert.equal(reverted.code,2);assert.equal(reverted.json.reason,'stale_base');
}));

test('next refuses record_incomplete and record recovers a saved response (SAFETY-4)',async()=>withDir(async dir=>{
 const r=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Titel']],lives:[live('TEST-COAT-01')]});
 await run(['approve','--batch',r.out,'--approved-by','Operator']);
 const saved=join(r.out,'responses','000.json'),raw=JSON.stringify({status:'ACCEPTED',runId:'301',runItemId:'302'});
 await mkdir(dirname(saved),{recursive:true});await writeFile(saved,raw);
 const blocked=await nextItem(r.out,'TEST-COAT-01');assert.equal(blocked.json.reason,'record_incomplete');assert.match(blocked.json.message,/responses\/000\.json exists/);
 const rec=await run(['record','--batch',r.out,'--index','0'],{readStdin:async()=>{throw new Error('stdin must not be read');}});
 assert.equal(rec.code,0,rec.stdout);assert.equal(rec.json.recovered,true);assert.equal(rec.json.runId,'301');assert.equal(rec.json.runItemId,'302');assert.equal(rec.json.response_file,saved);
 assert.equal(await readFile(saved,'utf8'),raw);
 const event=(await ledger(r.out)).at(-1);assert.equal(event.event,'submitted');assert.equal(event.recovered,true);
 assert.equal((await nextItem(r.out,'TEST-COAT-01')).json.status,'complete');
 assert.equal((await run(['record','--batch',r.out,'--index','0'],{readStdin:response()})).json.reason,'already_recorded');
}));

test('verify reports not_yet for an unchanged attribute and an empty slot that stays empty (LOGIC-2, DOCS-1)',async()=>withDir(async dir=>{
 const r=await submitted(dir,{rows:[['TEST-COAT-01','generic_keyword.0.value','neu wolle']],lives:[live('TEST-COAT-01')]});
 const early=await run(['verify','--batch',r.out,'--index','0','--live',live('TEST-COAT-01')]);
 assert.equal(early.code,3);assert.equal(early.json.state,'not_yet');assert.equal(early.json.attributes[0].result,'not_yet');
 assert.match((await pendingOf(dirname(r.out),r.out)).next_action,/never resubmit/);
 const pt05=await writeJson(dir,'images',[imageEntry('TEST-COAT-01','PT05',sha('pt05'))]);
 const img=await submitted(dir,{scope:'images',imagesFile:pt05,lives:[await keptLive(dir,'TEST-COAT-01')],out:join(dir,'batches','img')});
 const empty=await run(['verify','--batch',img.out,'--index','0','--live',live('TEST-COAT-01')]);
 assert.equal(empty.code,3);assert.equal(empty.json.state,'not_yet');assert.deepEqual(empty.json.images.map(i=>[i.slot,i.before,i.after,i.result]),[['PT05',null,null,'not_yet']]);
}));

test('a mismatch tells the agent to wait while in flight and to close before rebuilding (LOGIC-3)',async()=>withDir(async dir=>{
 const root=join(dir,'batches'),r=await submitted(dir,{rows:[['TEST-COAT-01','item_name.0.value','Neuer Titel']],lives:[live('TEST-COAT-01')],out:join(root,'a')});
 await run(['status','--batch',r.out,'--index','0'],{readStdin:async()=>JSON.stringify({runId:'101',runItemId:'202',status:'IN_PROGRESS',terminal:false})});
 const other=await liveFile(dir,'TEST-COAT-01',b=>{b.item.attributes.item_name[0].value='Ganz anderer Titel';});
 assert.equal((await run(['verify','--batch',r.out,'--index','0','--live',other])).json.state,'mismatch');
 assert.match((await pendingOf(root,r.out)).next_action,/^the write may still be in progress: poll status .*verify again before treating the mismatch as final/);
 await succeeded(r.out);
 const final=await run(['verify','--batch',r.out,'--index','0','--live',other]);assert.equal(final.code,3);assert.equal(final.json.state,'mismatch');
 assert.equal((await pendingOf(root,r.out)).next_action,"review the verify file; close this item with the operator's decision, then build a new approved batch if the change is still wanted");
 // The order the action gives works: close first, then the new batch builds.
 const live2=await liveFile(dir,'TEST-COAT-01',b=>{b.item.attributes.item_name[0].value='Ganz anderer Titel';});
 assert.equal((await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Neuer Titel']],lives:[live2],out:join(root,'b')})).json.reason,'submission_pending');
 assert.equal((await run(['close','--batch',r.out,'--index','0','--reason','operator: rebuild','--approved-by','Operator'])).code,0);
 assert.equal((await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','Neuer Titel']],lives:[live2],out:join(root,'b')})).code,0);
 // An UNKNOWN write that does not match yet is not final either.
 const u=await build(dir,{rows:[['TEST-COAT-02','item_name.0.value','Neu zwei']],lives:[live('TEST-COAT-02')],out:join(root,'u')});
 await run(['approve','--batch',u.out,'--approved-by','Operator']);await run(['record','--batch',u.out,'--index','0','--no-response','--note','timeout']);
 const otherTwo=await liveFile(dir,'TEST-COAT-02',b=>{b.item.attributes.item_name[0].value='Fremd';});
 assert.equal((await run(['verify','--batch',u.out,'--index','0','--live',otherTwo])).json.state,'mismatch');
 assert.match((await pendingOf(root,u.out)).next_action,/^the write may still be in progress/);
}));

test('a failed update is update_failed, exits 3 and keeps the first-item hold (LOGIC-5, SAFETY-2)',async()=>withDir(async dir=>{
 const r=await submitted(dir,{rows:[['TEST-COAT-01','item_name.0.value','Neuer Titel eins'],['TEST-COAT-02','item_name.0.value','Neuer Titel zwei']],lives:[live('TEST-COAT-01'),live('TEST-COAT-02')]});
 const status=body=>run(['status','--batch',r.out,'--index','0'],{readStdin:async()=>JSON.stringify({runId:'101',runItemId:'202',...body})});
 const landed=await liveFile(dir,'TEST-COAT-01',b=>{b.item.attributes.item_name[0].value='Neuer Titel eins';});
 const verify=path=>run(['verify','--batch',r.out,'--index','0','--live',path]);
 assert.equal((await status({status:'FAILED',terminal:true})).json.terminal,true);
 const failed=await verify(landed);
 assert.equal(failed.code,3);assert.equal(failed.json.state,'update_failed');assert.equal(failed.json.update_status.failed,true);assert.equal(failed.json.update_status.succeeded,false);
 assert.equal((await verify(live('TEST-COAT-01'))).json.state,'update_failed');
 assert.equal((await nextItem(r.out,'TEST-COAT-02')).json.reason,'first_item_unverified');
 assert.match((await pendingOf(dirname(r.out),r.out)).next_action,/update failed.*never resubmit/);
 // SUCCEEDED with a failure outcome, a terminal non-success, and an inferred terminal REJECTED all fail.
 for(const body of [{status:'SUCCEEDED',outcome:'FAILED'},{status:'DONE',terminal:true},{status:'rejected'},{outcome:'Partially_Failed'}]){
  await status(body);assert.equal((await verify(landed)).json.state,'update_failed',JSON.stringify(body));
 }
 await status({status:'SUCCEEDED',terminal:true});assert.equal((await verify(landed)).json.state,'verified');
 // A rejected update response with no poll yet fails too.
 const rejected=await submitted(dir,{rows:[['-TEST-COAT-03','item_name.0.value','Neu drei']],lives:[live('-TEST-COAT-03')],out:join(dir,'batches','rej')},{stdin:async()=>JSON.stringify({status:'REJECTED',runId:'7',runItemId:'8'})});
 const after3=await liveFile(dir,'-TEST-COAT-03',b=>{b.item.attributes.item_name[0].value='Neu drei';});
 assert.equal((await run(['verify','--batch',rejected.out,'--index','0','--live',after3])).json.state,'update_failed');
}));

test('a new ERROR issue is issues_new_error and keeps the hold; issues compare as multisets (LOGIC-1, LOGIC-4)',async()=>withDir(async dir=>{
 const d1=sha('coat01-pt02'),d2=sha('coat02-pt01');
 const file=await writeJson(dir,'images',[imageEntry('TEST-COAT-01','PT02',d1),imageEntry('TEST-COAT-02','PT01',d2)]);
 const r=await submitted(dir,{scope:'images',imagesFile:file,lives:[live('TEST-COAT-01'),live('TEST-COAT-02')]});
 await succeeded(r.out);
 const url='https://m.media-amazon.com/images/I/71NEW01.jpg',pixels=await pixelsFile(dir,[{sku:'TEST-COAT-01',slot:'PT02',amazon_url:url,image_sha256:d1,match:true}]);
 const after=extra=>liveFile(dir,'TEST-COAT-01',b=>{b.item.attributes.other_product_image_locator_2[0].media_location=url;b.item.issues.push(...extra);});
 const error={code:'18027',severity:'ERROR',attributeNames:['media_locator'],message:'Bild abgelehnt',categories:[]};
 const bad=await run(['verify','--batch',r.out,'--index','0','--live',await after([error]),'--pixels',pixels]);
 assert.equal(bad.code,3);assert.equal(bad.json.state,'issues_new_error');assert.deepEqual(bad.json.issues_new.map(i=>[i.code,i.severity]),[['18027','ERROR']]);
 assert.equal((await nextItem(r.out,'TEST-COAT-02')).json.reason,'first_item_unverified');
 assert.match((await pendingOf(dirname(r.out),r.out)).next_action,/new ERROR issue/);
 // A listing-level ERROR (no attributeNames, such as a suppression) always counts.
 const listingLevel=await run(['verify','--batch',r.out,'--index','0','--live',await after([{code:'5000',severity:'ERROR',attributeNames:[],message:'Angebot unterdrückt',categories:[]}]),'--pixels',pixels]);
 assert.equal(listingLevel.json.state,'issues_new_error');assert.deepEqual(listingLevel.json.issues_new.map(i=>i.code),['5000']);
 // An issue already present in the fresh read taken at next is not blamed on the write; a second occurrence is.
 const supp={code:'5001',severity:'ERROR',attributeNames:[],message:'Angebot unterdrückt',categories:[]};
 const f=await build(dir,{scope:'images',imagesFile:await writeJson(dir,'images',[imageEntry('TEST-COAT-01','PT02',d1)]),lives:[live('TEST-COAT-01')],out:join(dir,'fresh-root','f')});
 await run(['approve','--batch',f.out,'--approved-by','Operator']);
 const freshRead=await liveFile(dir,'TEST-COAT-01',b=>{b.item.issues.push(supp);});
 assert.equal((await run(['next','--batch',f.out,'--live',freshRead])).json.status,'next');
 assert.equal((await run(['record','--batch',f.out,'--index','0'],{readStdin:response()})).code,0);
 assert.deepEqual((await run(['verify','--batch',f.out,'--index','0','--live',await after([supp]),'--pixels',pixels])).json.issues_new,[]);
 assert.deepEqual((await run(['verify','--batch',f.out,'--index','0','--live',await after([supp,supp]),'--pixels',pixels])).json.issues_new.map(i=>i.code),['5001']);
 // A WARNING is reported but does not fail the item.
 const warn=await run(['verify','--batch',r.out,'--index','0','--live',await after([{...error,severity:'WARNING'}]),'--pixels',pixels]);
 assert.equal(warn.json.state,'verified');assert.equal(warn.json.issues_new_flag,true);
 // Multiset: TEST-COAT-02 already had one 18027 WARNING on media_locator; a second occurrence is new.
 await run(['record','--batch',r.out,'--index','1'],{readStdin:response('101','203')});
 const known={code:'18027',severity:'WARNING',attributeNames:['media_locator'],message:'Bild PT01 zu klein',categories:[]};
 const two=await liveFile(dir,'TEST-COAT-02',b=>{b.item.attributes.other_product_image_locator_1[0].media_location='https://m.media-amazon.com/images/I/71NEW02.jpg';b.item.issues.push(known);});
 const v2=await run(['verify','--batch',r.out,'--index','1','--live',two]);
 assert.deepEqual(v2.json.issues_new.map(i=>i.message),['Bild PT01 zu klein']);
 const one=await liveFile(dir,'TEST-COAT-02',b=>{b.item.attributes.other_product_image_locator_1[0].media_location='https://m.media-amazon.com/images/I/71NEW02.jpg';});
 assert.deepEqual((await run(['verify','--batch',r.out,'--index','1','--live',one])).json.issues_new,[]);
}));

test('verify numbering ignores compare output in verify/ (IMAGE-6)',async()=>withDir(async dir=>{
 const r=await submitted(dir,{rows:[['TEST-COAT-01','item_name.0.value','Neuer Titel']],lives:[live('TEST-COAT-01')]});
 const v1=await run(['verify','--batch',r.out,'--index','0','--live',live('TEST-COAT-01')]);assert.ok(v1.json.verify_file.endsWith('verify/000-1.json'));
 await writeFile(join(r.out,'verify','000-1-pixels.json'),'{}');await writeFile(join(r.out,'verify','000-7-notes.json'),'{}');
 const v2=await run(['verify','--batch',r.out,'--index','0','--live',live('TEST-COAT-01')]);assert.ok(v2.json.verify_file.endsWith('verify/000-2.json'),v2.json.verify_file);
}));

test('approvals expire, void items are skipped and the first-item hold anchors on the first non-void item (DOCS-2)',async()=>withDir(async dir=>{
 const root=join(dir,'batches'),later=()=>now()+13*3600e3;
 const r=await build(dir,{rows:[['TEST-COAT-01','item_name.0.value','T1'],['TEST-COAT-02','item_name.0.value','T2'],['-TEST-COAT-03','item_name.0.value','T3']],lives:[live('TEST-COAT-01'),live('TEST-COAT-02'),live('-TEST-COAT-03')],out:join(root,'a')});
 await run(['approve','--batch',r.out,'--approved-by','Operator']);
 assert.equal((await run(['approve','--batch',r.out,'--approved-by','Operator'])).json.reason,'already_approved');
 const expired=await nextItem(r.out,'TEST-COAT-01',{now:later});assert.equal(expired.json.reason,'approval_expired');assert.match(expired.json.message,/older than 12 hours/);
 assert.match((await run(['pending','--root',root],{now:later})).json.items[0].next_action,/approval is older than 12 hours/);
 const renewed=await run(['approve','--batch',r.out,'--approved-by','Operator'],{now:later});assert.equal(renewed.code,0,renewed.stdout);assert.equal(renewed.json.renewed,true);
 // Void item 0; item 1 becomes the anchor and is offered without a hold.
 const v=await run(['close','--batch',r.out,'--index','0','--reason','operator dropped it','--approved-by','Operator'],{now:later});assert.equal(v.json.void,true);
 const offered=await nextItem(r.out,'TEST-COAT-02',{now:later});assert.equal(offered.json.index,1,offered.stdout);
 assert.equal((await run(['record','--batch',r.out,'--index','1'],{readStdin:response(),now:later})).code,0,'a void item is no record-order gap');
 const held=await nextItem(r.out,'-TEST-COAT-03',{now:later});assert.equal(held.json.reason,'first_item_unverified');assert.match(held.json.message,/Item 1 \(TEST-COAT-02\)/);
 const landed=await liveFile(dir,'TEST-COAT-02',b=>{b.item.attributes.item_name[0].value='T2';});
 assert.equal((await run(['verify','--batch',r.out,'--index','1','--live',landed],{now:later})).json.state,'landed_status_pending');
 assert.equal((await nextItem(r.out,'-TEST-COAT-03',{now:later})).json.index,2);
 // A submitted-then-closed anchor keeps the hold.
 const s=await submitted(dir,{rows:[['TEST-COAT-01','generic_keyword.0.value','k1'],['TEST-COAT-02','generic_keyword.0.value','k2']],lives:[live('TEST-COAT-01'),live('TEST-COAT-02')],out:join(root,'s')});
 await run(['close','--batch',s.out,'--index','0','--reason','operator closed','--approved-by','Operator']);
 const kept=await nextItem(s.out,'TEST-COAT-02');assert.equal(kept.json.reason,'first_item_unverified');assert.match(kept.json.message,/closed after its write without --landed; build a new batch/);
 // close --landed needs a submitted item, and a landed close of the anchor releases the rest.
 const t=await submitted(dir,{rows:[['TEST-COAT-01','generic_keyword.0.value','k1'],['TEST-COAT-02','generic_keyword.0.value','k2']],lives:[live('TEST-COAT-01'),live('TEST-COAT-02')],out:join(dir,'other-root','t')});
 assert.equal((await run(['close','--batch',t.out,'--index','1','--reason','x','--approved-by','Operator','--landed'])).json.reason,'usage');
 const landedClose=out=>run(['close','--batch',out,'--index','0','--reason','operator checked the live listing','--approved-by','Operator','--landed']);
 assert.equal((await landedClose(t.out)).json.reason,'landed_unproven','no verify yet');
 const k1=await liveFile(dir,'TEST-COAT-01',b=>{b.item.attributes.generic_keyword[0].value='k1';});
 assert.equal((await run(['verify','--batch',t.out,'--index','0','--live',k1])).json.state,'landed_status_pending');
 assert.equal((await landedClose(t.out)).json.reason,'landed_unproven','a write with a runId is polled, not closed as landed');
 // An UNKNOWN write whose live read matches can be closed as landed, which releases the rest.
 const u=await build(dir,{rows:[['TEST-COAT-01','generic_keyword.0.value','k1'],['TEST-COAT-02','generic_keyword.0.value','k2']],lives:[live('TEST-COAT-01'),live('TEST-COAT-02')],out:join(dir,'third-root','u')});
 await run(['approve','--batch',u.out,'--approved-by','Operator']);
 assert.equal((await run(['record','--batch',u.out,'--index','0','--no-response','--note','timeout'])).code,0);
 assert.equal((await run(['verify','--batch',u.out,'--index','0','--live',k1])).json.state,'landed_status_pending');
 const ok=await landedClose(u.out);assert.equal(ok.json.landed,true,ok.stdout);assert.match(ok.json.landed_verify_file,/verify/);
 assert.equal((await nextItem(u.out,'TEST-COAT-02')).json.index,1);
}));

test('a landed UNKNOWN write says it cannot be polled and is closed by decision (DOCS-3)',async()=>withDir(async dir=>{
 const r=await build(dir,{rows:[['-TEST-COAT-03','item_name.0.value','Neuer Titel drei']],lives:[live('-TEST-COAT-03')]});
 await run(['approve','--batch',r.out,'--approved-by','Operator']);await run(['record','--batch',r.out,'--sku','-TEST-COAT-03','--no-response','--note','timeout']);
 const after=await liveFile(dir,'-TEST-COAT-03',b=>{b.item.attributes.item_name[0].value='Neuer Titel drei';});
 const v=await run(['verify','--batch',r.out,'--index','0','--live',after]);assert.equal(v.code,0);assert.equal(v.json.state,'landed_status_pending');
 assert.equal((await pendingOf(dirname(r.out),r.out)).next_action,'the live read matches, but the status cannot be polled without a runId; the operator decides: close --landed releases the rest of the batch, close without it keeps the hold');
}));
