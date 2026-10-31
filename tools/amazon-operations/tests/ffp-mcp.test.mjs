import '../../report-fetcher/test/helpers/isolated-runtime.mjs';
import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,rm,readFile,writeFile,copyFile,readdir,stat} from 'node:fs/promises';
import {join,dirname} from 'node:path';
import {tmpdir} from 'node:os';
import {createHash} from 'node:crypto';
import {gunzipSync,gzipSync} from 'node:zlib';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {main,parseCsv,blankPathToExport} from '../ffp-mcp.mjs';
import {flattenAttributes} from '../flatfilepro-listings.mjs';

const here=dirname(fileURLToPath(import.meta.url)),fixtures=join(here,'fixtures','ffp-mcp'),cli=join(here,'..','ffp-mcp.mjs');
const exportFile=join(fixtures,'catalog-export-test.jsonl.gz'),listingsFile=join(fixtures,'get-listings.json'),marketplacesFile=join(fixtures,'authorized-marketplaces.json');
const download=JSON.parse(await readFile(join(fixtures,'get-export-download.json'),'utf8')),gz=await readFile(exportFile);
const records=(await readFile(join(fixtures,'export-records.jsonl'),'utf8')).trim().split('\n').map(line=>JSON.parse(line));
const now=()=>Date.parse('2026-10-28T09:05:00.000Z');
const run=async(argv,deps={})=>{const {code,stdout}=await main(argv,{now,...deps});return {code,stdout,json:stdout.trim().startsWith('{')?JSON.parse(stdout):null};};
const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const withDir=async fn=>{const dir=await mkdtemp(join(tmpdir(),'ffp-mcp-'));try{return await fn(dir);}finally{await rm(dir,{recursive:true,force:true});}};
const secretParts=[download.downloadUrl,new URL(download.downloadUrl).search,'fakesignaturedeadbeef','TESTCREDENTIALFAKE'];
const assertNoSecret=(...texts)=>{for(const text of texts)for(const part of secretParts)assert.ok(!String(text).includes(part),'bearer URL leaked: '+part);};

test('fixture export decompresses to the readable records and matches its receipt',async()=>{
 assert.equal(gunzipSync(gz).toString('utf8'),records.map(r=>JSON.stringify(r)).join('\n')+'\n');
 const receipt=JSON.parse(await readFile(exportFile+'.receipt.json','utf8'));
 assert.equal(receipt.sha256,sha(gz));assert.equal(receipt.compressedBytes,gz.length);assert.equal(receipt.export_count,records.length);
 assert.equal(download.sha256,sha(gz));
});

test('flattenAttributes reproduces every verified FFP export header and its canonical form',()=>{
 const blue=records.find(r=>r.sku==='TEST-CHILD-BLUE').attributes;
 const exported=flattenAttributes(blue,{style:'export'}),canonical=flattenAttributes(blue,{style:'canonical'});
 const expected={
  item_name__1__value:'Test Shirt Blue',unit_count__1__type_value:'Count',item_dimensions__1__height_unit:'centimeters',
  purchasable_offer__1__end_at_value:'',item_weight__1__normalized_value_unit:'kilograms',
  purchasable_offer__1__our_price__1__schedule__1__value_with_tax:'49.99',outer__1__material__2__value:'Polyester',
  color__1__standardized_values__1__:'Blau',unit_count__1__value:'60',is_fragile__1__value:'false',variation_theme__1__name:'COLOR',
  fulfillment_availability__1__quantity:'5',
 };
 for(const [header,value] of Object.entries(expected))assert.equal(exported[header],value,header);
 for(const [header,value] of Object.entries({'unit_count.0.type_value':'Count','color.0.standardized_values.0.':'Blau','purchasable_offer.0.our_price.0.schedule.0.value_with_tax':'49.99','outer.0.material.1.value':'Polyester','item_weight.0.normalized_value_unit':'kilograms','purchasable_offer.0.end_at_value':'','item_name.0.value':'Test Shirt Blue'}))assert.equal(canonical[header],value,header);
 // Canonical is exactly prepare canonical_attribute applied to the export header (__N__ -> .N-1.).
 assert.deepEqual(Object.entries(exported).map(([h,v])=>[h.replace(/__(\d+)__/g,(m,n)=>`.${n-1}.`),v]),Object.entries(canonical));
 assert.ok(!Object.keys(exported).some(h=>/parentAsins|childAsins/.test(h)));
 assert.throws(()=>flattenAttributes(blue,{style:'dots'}),/style/);
 assert.throws(()=>flattenAttributes({a:[{b_c:'2',b:{c:'1'}}]},{style:'export'}),/Ambiguous flattened attribute header: a__1__b_c/);
});

test('blank attribute paths convert to export spelling mechanically',()=>{
 assert.equal(blankPathToExport('purchasable_offer[0].end_at.value'),'purchasable_offer__1__end_at_value');
 assert.equal(blankPathToExport('apparel_size[0].height_type'),'apparel_size__1__height_type');
 assert.equal(blankPathToExport('color[0].standardized_values'),'color__1__standardized_values');
 assert.equal(blankPathToExport('other_product_image_locator_8'),'other_product_image_locator_8');
 assert.equal(blankPathToExport('bad path!'),null);
});

test('binding resolves one authorized row by names or IDs and refuses ambiguity',async()=>{
 const ok=await run(['binding','--marketplaces',marketplacesFile,'--seller-name','  test SELLER ','--marketplace-name','united states']);
 assert.equal(ok.code,0);
 assert.deepEqual(ok.json,{status:'resolved',binding_source:'ffp-mcp',seller_id:'A1TESTSELLER01',marketplace_id:'ATVPDKIKX0DER',seller_name:'Test Seller',marketplace_name:'United States',flatfilepro_option_name:'Test Seller',flatfilepro_display_name:'Test Seller (United States)',note:'browser selector readback remains required before upload'});
 assert.ok(!('context_binding' in ok.json)&&!('unique_label_mapping' in ok.json));
 assert.equal((await run(['binding','--marketplaces',marketplacesFile,'--seller-id','A1TESTSELLER01','--marketplace-id','A1PA6795UKMFR9'])).json.marketplace_name,'Germany');
 const twin=await run(['binding','--marketplaces',marketplacesFile,'--seller-name','Twin Seller','--marketplace-name','United States']);
 assert.equal(twin.code,2);assert.equal(twin.json.reason,'binding_ambiguous');
 const missing=await run(['binding','--marketplaces',marketplacesFile,'--seller-name','Test Seller','--marketplace-name','France']);
 assert.equal(missing.code,2);assert.equal(missing.json.reason,'binding_unavailable');
 assert.equal((await run(['binding','--marketplaces',marketplacesFile,'--seller-id','A9NOTTHERE','--marketplace-id','ATVPDKIKX0DER'])).json.reason,'binding_unavailable');
 assert.equal((await run(['binding','--marketplaces',marketplacesFile,'--seller-name','Test Seller','--marketplace-name','Germany','--seller-id','A1TESTSELLER01','--marketplace-id','A1PA6795UKMFR9'])).json.reason,'usage');
 await withDir(async dir=>{const file=join(dir,'m.json');await writeFile(file,'{"rows":[]}');assert.equal((await run(['binding','--marketplaces',file,'--seller-id','A','--marketplace-id','B'])).json.reason,'marketplaces_unreadable');});
});

const bodyResponse=(bytes,status=200)=>new Response(bytes,{status});
const fetchDeps=(dir,overrides={})=>{const calls=[];return {calls,deps:{readStdin:async()=>JSON.stringify({...download,...overrides.result}),fetch:async(url,init)=>{calls.push({url,init});return overrides.fetch?overrides.fetch(url,init):bodyResponse(gz);},artifactctl:overrides.artifactctl,...overrides.deps}};};

test('fetch-export downloads, verifies and writes a URL-free receipt',async()=>withDir(async dir=>{
 const {calls,deps}=fetchDeps(dir);
 const result=await run(['fetch-export','--out-dir',dir],deps);
 assert.equal(result.code,0,result.stdout);assert.equal(result.json.status,'fetched');assert.equal(result.json.registration,'not_requested');
 assert.equal(calls.length,1);assert.equal(calls[0].init.redirect,'error');assert.equal(calls[0].url,download.downloadUrl);
 const path=join(dir,download.fileName),receiptText=await readFile(path+'.receipt.json','utf8'),receipt=JSON.parse(receiptText);
 assert.equal(sha(await readFile(path)),download.sha256);
 assert.deepEqual(Object.keys(receipt).sort(),['archiveStatus','completedAt','compressedBytes','export_count','fetched_at','fileName','jobId','marketplaceId','path','schemaVersion','sellerId','sha256','snapshotAt','source'].sort());
 assert.equal(receipt.source,'ffp-mcp-export');assert.equal(receipt.path,path);assert.equal(receipt.export_count,records.length);
 assertNoSecret(result.stdout,receiptText);
 // A second run with the same bytes reuses the file without any network call.
 const again=fetchDeps(dir);const second=await run(['fetch-export','--out-dir',dir],again.deps);
 assert.equal(second.json.status,'existing');assert.equal(again.calls.length,0);
}));

test('fetch-export registers the export and receipt as preserve, and reports a registration failure separately',async()=>withDir(async dir=>{
 const seen=[];const ok=fetchDeps(dir,{artifactctl:args=>{seen.push(args);return {status:0,stdout:JSON.stringify({id:'art_'+seen.length,state:'preserved'}),stderr:''};}});
 const result=await run(['fetch-export','--out-dir',dir,'--register-run','run_test'],ok.deps);
 assert.equal(result.json.registration,'registered');assert.equal(result.json.registered_artifacts.length,2);
 assert.deepEqual(seen.map(args=>[args[0],args[2],args[4],args[5],args[6]]),[['register','run_test',join(dir,download.fileName),'--disposition','preserve'],['register','run_test',join(dir,download.fileName)+'.receipt.json','--disposition','preserve']]);
 assertNoSecret(JSON.stringify(seen));
 const failing=fetchDeps(dir,{artifactctl:()=>({status:1,stdout:'',stderr:'unknown run: run_missing'})});
 const failed=await run(['fetch-export','--out-dir',dir,'--register-run','run_missing'],failing.deps);
 assert.equal(failed.code,0);assert.equal(failed.json.status,'existing');assert.equal(failed.json.registration,'failed');assert.match(failed.json.registration_message,/unknown run/);
}));

for(const [name,result,reason] of [
 ['wrong host',{downloadUrl:download.downloadUrl.replace('ffp-mcp-export.s3','evil.s3')},'export_url_invalid'],
 ['look-alike host',{downloadUrl:download.downloadUrl.replace('amazonaws.com/','amazonaws.com.evil.test/')},'export_url_invalid'],
 ['http',{downloadUrl:download.downloadUrl.replace('https:','http:')},'export_url_invalid'],
 ['userinfo',{downloadUrl:download.downloadUrl.replace('https://','https://user:pass@')},'export_url_invalid'],
 ['port',{downloadUrl:download.downloadUrl.replace('amazonaws.com/','amazonaws.com:8443/')},'export_url_invalid'],
 ['path',{downloadUrl:download.downloadUrl.replace('/catalog-exports/','/other/')},'export_url_invalid'],
 ['format',{format:'CSV'},'export_result_invalid'],
 ['compression',{compression:'NONE'},'export_result_invalid'],
 ['checksum',{checksumAlgorithm:'MD5'},'export_result_invalid'],
 ['counts_match',{counts_match:false},'export_counts_mismatch'],
 ['file name traversal',{fileName:'../escape.jsonl.gz'},'export_result_invalid'],
 ['file name suffix',{fileName:'export.json'},'export_result_invalid'],
 ['expired URL',{urlExpiresAt:'2026-10-28T09:00:00.000Z'},'export_url_expired'],
])test('fetch-export refuses '+name+' before any request',async()=>withDir(async dir=>{
 const {calls,deps}=fetchDeps(dir,{result});const out=await run(['fetch-export','--out-dir',dir],deps);
 assert.equal(out.code,2);assert.equal(out.json.reason,reason);assert.equal(calls.length,0);assert.deepEqual(await readdir(dir),[]);
 assertNoSecret(out.stdout);
}));

const foreignGz=gzipSync(Buffer.from(records.map((r,i)=>JSON.stringify(i===2?{...r,sellerId:'A9OTHERSELLER'}:r)).join('\n')+'\n'));
const archivedInUnarchived={archiveStatus:'UNARCHIVED'};
for(const [name,overrides,reason] of [
 ['a redirect (fetch rejects with the URL in its message)',{fetch:url=>{throw new TypeError('fetch failed: redirect from '+url);}},'export_download_failed'],
 ['a non-200 response',{fetch:()=>bodyResponse('moved',302)},'export_download_failed'],
 ['a larger body',{fetch:()=>bodyResponse(Buffer.concat([gz,Buffer.from('extra')]))},'export_size_mismatch'],
 ['a shorter body',{fetch:()=>bodyResponse(gz.subarray(0,gz.length-4))},'export_size_mismatch'],
 ['a SHA-256 mismatch',{fetch:()=>{const bytes=Buffer.from(gz);bytes[bytes.length-1]^=0xff;return bodyResponse(bytes);}},'export_sha_mismatch'],
 ['a record count mismatch',{result:{export_count:records.length+1}},'export_count_mismatch'],
 ['a foreign seller record',{result:{sha256:sha(foreignGz),compressedBytes:foreignGz.length},fetch:()=>bodyResponse(foreignGz)},'export_foreign_record'],
 ['an archived record in an unarchived export',{result:archivedInUnarchived},'export_archive_mismatch'],
])test('fetch-export removes the partial file after '+name,async()=>withDir(async dir=>{
 const {deps}=fetchDeps(dir,overrides);const out=await run(['fetch-export','--out-dir',dir],deps);
 assert.equal(out.code,2,out.stdout);assert.equal(out.json.reason,reason);assert.deepEqual(await readdir(dir),[]);
 assertNoSecret(out.stdout);
}));

test('fetch-export refuses to overwrite a different existing file and leaves it intact',async()=>withDir(async dir=>{
 const path=join(dir,download.fileName);await writeFile(path,'operator file');
 const {calls,deps}=fetchDeps(dir);const out=await run(['fetch-export','--out-dir',dir],deps);
 assert.equal(out.json.reason,'export_file_exists');assert.equal(calls.length,0);assert.equal(await readFile(path,'utf8'),'operator file');
}));

test('the bearer URL never reaches stdout or stderr of the CLI process',async()=>withDir(async dir=>{
 for(const result of [{...download,downloadUrl:download.downloadUrl.replace('ffp-mcp-export','other')},{...download,format:'CSV'},{...download,urlExpiresAt:'2000-01-01T00:00:00Z'}]){
  const child=spawnSync(process.execPath,[cli,'fetch-export','--out-dir',dir],{input:JSON.stringify(result),encoding:'utf8',env:process.env});
  assert.equal(child.status,2);assert.equal(JSON.parse(child.stdout).status,'blocked');assertNoSecret(child.stdout,child.stderr);
 }
 // A URL pasted into argv by mistake is not echoed back either.
 const argv=spawnSync(process.execPath,[cli,'fetch-export','--out-dir',dir,download.downloadUrl],{input:'',encoding:'utf8',env:process.env});
 assert.equal(argv.status,2);assertNoSecret(argv.stdout,argv.stderr);
}));

test('resolve returns every non-archived SKU of an ASIN and names archived SKUs',async()=>{
 const out=await run(['resolve','--export',exportFile,'--asin','B0TEST0002','--sku','TEST-PARENT-01']);
 assert.equal(out.code,0,out.stdout);
 assert.deepEqual(out.json.targets,[
  {sku:'TEST-PARENT-01',asin:'B0TEST0001',product_type:'SHIRT',parentage:'parent',parent_sku:''},
  {sku:'TEST-CHILD-BLUE',asin:'B0TEST0002',product_type:'SHIRT',parentage:'child',parent_sku:'TEST-PARENT-01'},
  {sku:'TEST-CHILD-BLUE-B',asin:'B0TEST0002',product_type:'SHIRT',parentage:'child',parent_sku:'TEST-PARENT-01'}]);
 assert.deepEqual(out.json.excluded_archived,[{sku:'TEST-CHILD-BLUE-OLD',asin:'B0TEST0002'}]);
 assert.equal(out.json.export.sha256,download.sha256);
 const archived=await run(['resolve','--export',exportFile,'--sku','TEST-CHILD-RED']);assert.equal(archived.json.reason,'sku_archived');assert.match(archived.json.message,/TEST-CHILD-RED/);
 assert.equal((await run(['resolve','--export',exportFile,'--sku','NOPE'])).json.reason,'sku_missing');
 assert.equal((await run(['resolve','--export',exportFile,'--asin','B0TEST0003'])).json.reason,'asin_unavailable');
 assert.equal((await run(['resolve','--export',exportFile,'--asin','B0TEST9999'])).json.reason,'asin_unavailable');
});

test('every export read re-verifies the receipt SHA-256',async()=>withDir(async dir=>{
 const copy=join(dir,download.fileName);await copyFile(exportFile,copy);
 assert.equal((await run(['resolve','--export',copy,'--sku','TEST-PARENT-01'])).json.reason,'receipt_missing');
 const receipt=JSON.parse(await readFile(exportFile+'.receipt.json','utf8'));
 await writeFile(copy+'.receipt.json',JSON.stringify({...receipt,sha256:'0'.repeat(64)}));
 for(const argv of [['resolve','--sku','TEST-PARENT-01'],['rows','--sku','TEST-PARENT-01'],['survey','--sku','TEST-PARENT-01'],['gaps','--sku','TEST-PARENT-01'],['listing-json','--sku','TEST-PARENT-01'],['grid','--sku','TEST-PARENT-01','--out',join(dir,'g.csv')]]){
  const out=await run([argv[0],'--export',copy,...argv.slice(1)]);assert.equal(out.code,2);assert.equal(out.json.reason,'receipt_mismatch',argv[0]);
 }
 await writeFile(copy+'.receipt.json',JSON.stringify({...receipt,fileName:'other.jsonl.gz'}));
 assert.equal((await run(['rows','--export',copy,'--sku','TEST-PARENT-01'])).json.reason,'receipt_invalid');
}));

test('grid writes FFP export spelling with provenance and verifies every value',async()=>withDir(async dir=>{
 const out=join(dir,'source.csv');
 const result=await run(['grid','--export',exportFile,'--sku','TEST-CHILD-BLUE-B','--sku','TEST-CHILD-BLUE','--out',out]);
 assert.equal(result.code,0,result.stdout);assert.equal(result.json.rows,2);assert.equal(result.json.verified,true);
 const table=parseCsv(await readFile(out,'utf8')),[headers,...rows]=table;
 assert.equal(headers[0],'sku');assert.deepEqual(rows.map(r=>r[0]),['TEST-CHILD-BLUE-B','TEST-CHILD-BLUE']);
 assert.deepEqual(headers.slice(1,4),['item_name__1__value','item_name__1__language_tag','item_name__1__marketplace_id']);
 for(const header of ['unit_count__1__type_value','color__1__standardized_values__1__','purchasable_offer__1__our_price__1__schedule__1__value_with_tax','outer__1__material__2__value'])assert.ok(headers.includes(header),header);
 assert.equal(new Set(headers).size,headers.length);
 const blue=flattenAttributes(records.find(r=>r.sku==='TEST-CHILD-BLUE').attributes,{style:'export'});
 for(const [header,value] of Object.entries(blue))assert.equal(rows[1][headers.indexOf(header)],value,header);
 assert.equal(rows[1][headers.indexOf('bullet_point__3__value')],'Third "quoted" bullet');
 assert.equal(rows[1][headers.indexOf('product_description__1__value')],'A plain test description.\nSecond line.');
 assert.equal(rows[0][headers.indexOf('bullet_point__1__value')],'');
 const provenance=JSON.parse(await readFile(out+'.provenance.json','utf8'));
 assert.equal(provenance.source,'ffp-mcp-export');assert.equal(provenance.header_style,'ffp-export');assert.equal(provenance.header_count,headers.length);
 assert.deepEqual(provenance.export,{sha256:download.sha256,jobId:'job-test-0001',snapshotAt:'2026-10-28T09:00:00.000Z',fileName:download.fileName});
 assert.deepEqual(provenance.skus,['TEST-CHILD-BLUE-B','TEST-CHILD-BLUE']);assert.equal(provenance.seller_id,'A1TESTSELLER01');assert.equal(provenance.marketplace_id,'ATVPDKIKX0DER');
 assert.ok(!('blank_columns' in provenance));assert.equal(provenance.csv_sha256,sha(await readFile(out)));
 assert.equal((await run(['grid','--export',exportFile,'--sku','TEST-CHILD-BLUE','--out',out])).json.reason,'grid_exists');
}));

test('grid blank columns come only from AVAILABLE indexed leaf paths and bare names never become headers',async()=>withDir(async dir=>{
 const out=join(dir,'source.csv');
 const result=await run(['grid','--export',exportFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-SCHEMA-NA','--out',out,'--blank-columns']);
 assert.equal(result.code,0,result.stdout);assert.deepEqual(result.json.blank_columns_unavailable,['TEST-SCHEMA-NA']);
 const bare=['material','special_feature','unrelated_attribute','image_locator_ps01','other_product_image_locator_8'];
 assert.deepEqual(result.json.blank_attributes_bare,bare);
 const headers=parseCsv(await readFile(out,'utf8'))[0];
 assert.ok(headers.includes('apparel_size__1__height_type'));
 for(const header of bare)assert.ok(!headers.includes(header),header);
 assert.equal(headers.filter(h=>h==='purchasable_offer__1__end_at_value').length,1);
 const provenance=JSON.parse(await readFile(out+'.provenance.json','utf8'));
 assert.deepEqual(provenance.blank_columns,[{path:'apparel_size[0].height_type',header:'apparel_size__1__height_type'}]);
 assert.deepEqual(provenance.blank_attributes_bare,bare);
 assert.match(provenance.blank_columns_note,/writes that header into the upload workbook/);assert.match(provenance.blank_columns_note,/technical header from the target template/);
}));

test('grid --add-column adds an empty template column only for an attribute that is blank on every SKU',async()=>withDir(async dir=>{
 const out=join(dir,'source.csv');
 const result=await run(['grid','--export',exportFile,'--sku','TEST-CHILD-BLUE','--out',out,'--add-column','material__1__value']);
 assert.equal(result.code,0,result.stdout);assert.deepEqual(result.json.added_columns,[{header:'material__1__value',attribute:'material'}]);
 const table=parseCsv(await readFile(out,'utf8')),column=table[0].indexOf('material__1__value');
 assert.ok(column>0);assert.equal(table[1][column],'');
 const provenance=JSON.parse(await readFile(out+'.provenance.json','utf8'));
 assert.deepEqual(provenance.added_columns,[{header:'material__1__value',attribute:'material'}]);assert.match(provenance.added_columns_note,/target template/);
 for(const [argv,reason] of [
  [['--sku','TEST-CHILD-BLUE','--add-column','material'],'usage'],
  [['--sku','TEST-CHILD-BLUE','--add-column','material.0.value'],'usage'],
  [['--sku','TEST-CHILD-BLUE','--add-column','brand__1__value'],'column_present'],
  [['--sku','TEST-CHILD-BLUE','--add-column','generic_keyword__3__value'],'attribute_not_blank'],
  [['--sku','TEST-CHILD-BLUE','--sku','TEST-CHILD-BLUE-B','--add-column','material__1__value'],'attribute_not_blank'],
  [['--sku','TEST-SCHEMA-NA','--add-column','material__1__value'],'blank_status_unknown'],
 ]){const failed=join(dir,'refused.csv'),refused=await run(['grid','--export',exportFile,...argv,'--out',failed]);assert.equal(refused.code,2,argv.join(' '));assert.equal(refused.json.reason,reason,argv.join(' '));assert.ok(!(await readdir(dir)).includes('refused.csv'));}
}));

test('grid refuses get_listings input, archived SKUs and missing SKUs without writing',async()=>withDir(async dir=>{
 const out=join(dir,'g.csv');
 for(const [argv,reason] of [
  [['--listings',listingsFile,'--sku','TEST-CHILD-BLUE'],'planning_only_source'],
  [['--export',exportFile,'--sku','TEST-CHILD-RED'],'sku_archived'],
  [['--export',exportFile,'--sku','TEST-CHILD-BLUE','--sku','MISSING-1'],'sku_missing'],
  [['--export',exportFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-CHILD-BLUE'],'usage'],
 ]){const result=await run(['grid',...argv,'--out',out]);assert.equal(result.code,2);assert.equal(result.json.reason,reason);}
 assert.deepEqual(await readdir(dir),[]);
}));

test('dash-prefixed SKUs are values, not flags',async()=>{
 const out=await run(['rows','--export',exportFile,'--sku','-NOT-A-FLAG']);assert.equal(out.json.reason,'sku_missing');assert.match(out.json.message,/-NOT-A-FLAG/);
});

test('rows read nested values from both transports and never synthesize itemName',async()=>{
 const fromExport=await run(['rows','--export',exportFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-CHILD-RED']);
 assert.equal(fromExport.code,0,fromExport.stdout);
 const e=fromExport.json;assert.equal(e.source_kind,'flatfilepro_mcp_listing_read');assert.equal(e.transport,'mcp_export');assert.equal(e.planning_only,false);assert.equal(e.raw_sha256,download.sha256);
 assert.equal(e.tool,'flatfilepro_get_export_download');assert.equal(e.arguments_sha256,sha(JSON.stringify({jobId:download.jobId})));
 assert.deepEqual(e.account,{seller_id:'A1TESTSELLER01',marketplace_id:'ATVPDKIKX0DER'});
 const row=e.rows['TEST-CHILD-BLUE'];
 assert.equal(row['unit_count.0.type_value'],'Count');assert.equal(row['color.0.standardized_values.0.'],'Blau');assert.equal(row['item_name.0.value'],'Test Shirt Blue');
 assert.equal(row.itemName,'');assert.equal(row.listing_relationship_evidence,'');
 assert.deepEqual(e.records[0],{sku:'TEST-CHILD-BLUE',asin:'B0TEST0002',product_type:'SHIRT',archived:false,version_id:12,blank_attributes:records[1].blankAttributes,blank_attributes_status:'AVAILABLE'});
 assert.equal(e.records[1].archived,true);
 const fromListings=await run(['rows','--listings',listingsFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-CHILD-RED']);
 const l=fromListings.json;assert.equal(l.transport,'mcp_get_listings');assert.equal(l.planning_only,true);assert.equal(l.raw_sha256,sha(await readFile(listingsFile)));
 assert.equal(l.tool,'flatfilepro_get_listings');
 assert.equal(l.arguments_sha256,sha(JSON.stringify({marketplaceId:'ATVPDKIKX0DER',sellerId:'A1TESTSELLER01',skus:['TEST-CHILD-BLUE','TEST-CHILD-RED']})));
 assert.equal(l.records[0].archived,null);assert.equal(l.records[0].version_id,null);assert.equal(l.records[1].archived,null);
 assert.deepEqual(l.rows['TEST-CHILD-BLUE'],row);
});

test('get_listings input needs empty missingSkus, exact coverage, no duplicates and one account',async()=>withDir(async dir=>{
 const body=JSON.parse(await readFile(listingsFile,'utf8')),file=join(dir,'listings.json');
 const attempt=async(mutated,skus=['TEST-CHILD-BLUE','TEST-CHILD-RED'])=>{await writeFile(file,JSON.stringify(mutated));return (await run(['rows','--listings',file,...skus.flatMap(s=>['--sku',s])])).json;};
 assert.equal((await attempt({...body,missingSkus:['TEST-GONE']})).reason,'sku_missing');
 assert.equal((await attempt(body,['TEST-CHILD-BLUE'])).reason,'sku_coverage');
 assert.equal((await attempt(body,['TEST-CHILD-BLUE','TEST-CHILD-RED','TEST-OTHER'])).reason,'sku_coverage');
 assert.equal((await attempt({...body,listings:[...body.listings,body.listings[0]]})).reason,'sku_duplicate');
 assert.equal((await attempt({...body,listings:[body.listings[0],{...body.listings[1],seller_id:'A2TESTSELLER02'}]})).reason,'account_mismatch');
 assert.equal((await attempt({listings:body.listings})).reason,'listings_unreadable');
}));

test('survey reports image slots, parentage and free PT slots',async()=>{
 const out=await run(['survey','--export',exportFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-PARENT-01']);
 assert.equal(out.code,0,out.stdout);assert.equal(out.json.planning_only,false);
 const [blue,parent]=out.json.skus;
 assert.equal(blue.MAIN,'https://images.example.test/main-blue.png');assert.equal(blue.SWCH,'');assert.equal(blue.PT01,'https://images.example.test/pt01-blue.png');assert.equal(blue.PT03,'https://images.example.test/pt03-blue.png');
 assert.deepEqual(blue.free_slots,['PT02','PT04','PT05','PT06','PT07','PT08','PT09']);assert.equal(blue.parentage,'child');assert.equal(blue.parent_sku,'TEST-PARENT-01');assert.equal(blue.archived,false);
 assert.equal(parent.parentage,'parent');assert.equal(parent.free_slots.length,9);
 const csv=await run(['survey','--listings',listingsFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-CHILD-RED','--format','csv']);
 const table=parseCsv(csv.stdout);assert.deepEqual(table[0].slice(0,6),['sku','asin','parentage','parent_sku','archived','MAIN']);assert.equal(table.length,3);assert.equal(table[1][4],'');
 const md=await run(['survey','--listings',listingsFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-CHILD-RED','--format','md']);
 assert.match(md.stdout,/^Planning read only/);assert.match(md.stdout,/\| TEST-CHILD-BLUE \| B0TEST0002 \|/);
});

test('gaps blocks with exit 3 on companion gaps and keeps unknown blank analysis unknown',async()=>{
 const out=await run(['gaps','--export',exportFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-CHILD-BLUE-B','--sku','TEST-SCHEMA-NA','--touch','unit_count,item_dimensions,item_weight__1__value,color']);
 assert.equal(out.code,3);assert.equal(out.json.status,'blocked');assert.equal(out.json.reason,'companion_gaps');
 assert.deepEqual(out.json.touched,['unit_count','item_dimensions','item_weight','color']);assert.deepEqual(out.json.companion_unchecked,['color']);
 const [blue,blueB,schema]=out.json.skus;
 assert.deepEqual(blue.companion_gaps,['item_dimensions[0].length.value']);
 assert.deepEqual(blueB.companion_gaps,['unit_count[0].type.value','item_weight[0].unit']);assert.deepEqual(blueB.touched_blank,['item_dimensions']);
 assert.deepEqual(blue.candidates,{status:'available',attributes:['material','special_feature']});
 assert.deepEqual(blue.free_image_slots,['PT02','PT04','PT05','PT06','PT07','PT08','PT09']);
 assert.equal(schema.candidates.status,'unknown');assert.deepEqual(schema.candidates.attributes,[]);assert.deepEqual(schema.companion_gaps,[]);
 const clean=await run(['gaps','--export',exportFile,'--sku','TEST-CHILD-BLUE','--touch','unit_count,item_weight']);
 assert.equal(clean.code,0);assert.equal(clean.json.status,'ok');
 const nothing=await run(['gaps','--listings',listingsFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-CHILD-RED']);
 assert.equal(nothing.code,0);assert.equal(nothing.json.planning_only,true);assert.equal(nothing.json.skus[0].candidates.status,'available');
});

test('listing-json emits the FFP saved backend copy in the listing-reference shape',async()=>{
 const out=await run(['listing-json','--export',exportFile,'--sku','TEST-CHILD-BLUE','--sku','TEST-PARENT-01']);
 assert.equal(out.code,0,out.stdout);assert.equal(out.json.source,'ffp-saved-backend');assert.equal(out.json.note,'FlatFilePro saved backend copy, not the live PDP');
 assert.deepEqual(out.json.listings[0],{asin:'B0TEST0002',sku:'TEST-CHILD-BLUE',title:'Test Shirt Blue',bullets:['First bullet','Second bullet, with comma','Third "quoted" bullet'],description:'A plain test description.\nSecond line.',item_highlights:'Soft cotton blend',backend:'shirt tee top'});
 assert.deepEqual(out.json.listings[1],{asin:'B0TEST0001',sku:'TEST-PARENT-01',title:'Test Shirt',bullets:[],description:'',item_highlights:'',backend:''});
});

test('usage errors are blocked JSON with exit 2',async()=>{
 for(const argv of [[],['nope'],['rows','--export'],['rows','--export',exportFile],['rows','--export',exportFile,'--listings',listingsFile,'--sku','X'],['survey','--export',exportFile,'--sku','TEST-CHILD-BLUE','--format','xml'],['resolve','--export',exportFile]]){
  const out=await run(argv);assert.equal(out.code,2,JSON.stringify(argv));assert.equal(out.json.status,'blocked');assert.equal(out.json.reason,'usage',JSON.stringify(argv));
 }
});
