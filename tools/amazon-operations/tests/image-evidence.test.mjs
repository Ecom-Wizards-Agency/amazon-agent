import test from 'node:test';
import assert from 'node:assert/strict';
import {collectByAsin,readImageRecord,selectExactSlots} from '../image-evidence.mjs';

const clock=()=>Date.parse('2026-09-15T00:00:00Z');
const input={operation_id:'operation',plan_hash:'plan',account:{marketplace:'US'},targets:{
 first:{asin:'B000000001',slots:['PT01','PT02']},second:{asin:'B000000001',slots:['PT01']},third:{asin:'B000000002',slots:['PT01']}}};
const read=async(asin,slots)=>({asin,observed_at:new Date(clock()).toISOString(),source_id:`https://www.amazon.com/dp/${asin}`,
 images:slots.map(slot=>({slot,live_url:`https://m.media-amazon.com/${asin}-${slot}.jpg`}))});

test('shared ASIN read once and expanded to exact SKU slot coverage',async()=>{
 const calls=[];
 const result=await collectByAsin(input,async(...args)=>{calls.push(args);return read(...args);},clock);
 assert.equal(calls.length,2);assert.equal(result.status,'collected');assert.equal(result.images.length,4);
 assert.deepEqual(result.images.filter(x=>x.sku==='second').map(x=>x.slot),['PT01']);
});
test('timeout preserves other ASIN and retries only failed ASIN with original timestamps',async()=>{
 const first=await collectByAsin(input,async(asin,slots)=>{if(asin==='B000000002')throw new Error('timeout');return read(asin,slots);},clock);
 assert.equal(first.status,'partial');assert.equal(first.images.length,3);
 const calls=[];
 const retry=await collectByAsin({...input,previous:first},async(...args)=>{calls.push(args[0]);return read(...args);},()=>clock()+1000);
 assert.equal(retry.status,'collected');assert.deepEqual(calls,['B000000002']);
 assert.equal(retry.images[0].observed_at,first.images[0].observed_at);
});
test('expired or differently bound cached evidence never suppresses fresh reads',async()=>{
 const partial=await collectByAsin(input,async(asin,slots)=>{if(asin==='B000000002')throw new Error('timeout');return read(asin,slots);},clock);
 for(const [previous,at] of [[partial,clock()+900001],[{...partial,plan_hash:'other'},clock()+1000],[{...partial,account:{marketplace:'DE'}},clock()+1000]]){
  let calls=0;await collectByAsin({...input,previous},async(...args)=>{calls++;return read(...args);},()=>at);assert.equal(calls,2);
 }
});
test('missing slots, wrong ASIN and duplicate slots remain incomplete',async()=>{
 for(const mutate of [x=>({...x,images:x.images.slice(0,1)}),x=>({...x,asin:'B000000009'}),x=>({...x,images:[x.images[0],x.images[0]]})]){
  const result=await collectByAsin(input,async(...args)=>mutate(await read(...args)),clock);assert.notEqual(result.status,'collected');
 }
 assert.throws(()=>selectExactSlots({title:'Product',resolved_asin:'B000000001',selected_asin:'B000000002',images:[]},'B000000001',['PT01']),/variation/);
});
test('payload parser handles quoted brackets and apostrophes without rewriting JSON',()=>{
 const oldDocument=globalThis.document,oldLocation=globalThis.location;
 const data=[{variant:'PT01',hiRes:"https://m.media-amazon.com/a'[b].jpg"},{variant:'MAIN',large:'https://m.media-amazon.com/main.jpg'}];
 globalThis.document={querySelector:selector=>selector==='#productTitle'?{textContent:'Product'}:selector==='input#ASIN'?{value:'B000000001'}:null,
  querySelectorAll:()=>[{textContent:`data = {'colorImages': {'initial': ${JSON.stringify(data)}}};`}]};
 globalThis.location={pathname:'/dp/B000000001',href:'https://www.amazon.com/dp/B000000001'};
 try{const result=readImageRecord();assert.equal(result.images.length,2);assert.equal(result.images[0].url,data[0].hiRes);}
 finally{globalThis.document=oldDocument;globalThis.location=oldLocation;}
});

function parseScripts(scripts){
 const oldDocument=globalThis.document,oldLocation=globalThis.location;
 globalThis.document={querySelector:selector=>selector==='#productTitle'?{textContent:'Product'}:selector==='input#ASIN'?{value:'B000000001'}:null,
  querySelectorAll:()=>scripts.map(textContent=>({textContent}))};
 globalThis.location={pathname:'/dp/B000000001',href:'https://www.amazon.com/dp/B000000001'};
 try{return readImageRecord();}finally{globalThis.document=oldDocument;globalThis.location=oldLocation;}
}
const singleLiteral=value=>"'"+value.replace(/\\/g,'\\\\').replace(/'/g,"\\'").replace(/\n/g,'\\n').replace(/\r/g,'\\r')+"'";
const scriptFor=expression=>`data = {'colorImages': {'initial': ${expression}}};`;

test('observed A.$.parseJSON literal returns MAIN plus eight precise image variants',()=>{
 const images=Array.from({length:9},(_,index)=>({variant:index?`PT0${index}`:'MAIN',
  hiRes:`https://m.media-amazon.com/images/I/approved${index}._AC_SL1500_.jpg`,main:{'https://example.com/preview.jpg':[355,355]},
  altText:"It's 25 mg, not 26 mg. Path \\draft\\image; quoted [text] and Ω."}));
 const expression=`A.$.parseJSON(${singleLiteral(JSON.stringify(images))})`;
 const result=parseScripts([scriptFor(expression),'var other = {"colorImages":{},"other":{"initial":[]}};']);
 assert.equal(result.images.length,9);
 assert.deepEqual(result.images,images.map(image=>({variant:image.variant,url:image.hiRes})));
});

test('literal decoding preserves escaped apostrophes, backslashes, unicode and small text',()=>{
 const url="https://m.media-amazon.com/dose-25mg-It's-\\folder-Ω.jpg";
 const payload=JSON.stringify([{variant:'PT01',hiRes:url}]);
 const literal=singleLiteral(payload).replace('25mg','\\x32\\u0035mg').replace('Ω','\\u03a9');
 assert.equal(parseScripts([scriptFor(`A.$.parseJSON(${literal})`)]).images[0].url,url);
 const changed=singleLiteral(payload.replace('25mg','26mg'));
 assert.notEqual(parseScripts([scriptFor(`A.$.parseJSON(${changed})`)]).images[0].url,url);
});

test('custom expressions, concatenation and extra parseJSON arguments are rejected without execution',()=>{
 globalThis.imageParserExecuted=false;
 const data=JSON.stringify([{variant:'PT01',hiRes:'https://example.com/image.jpg'}]);
 const literal=singleLiteral(data);
 for(const expression of [
  `(globalThis.imageParserExecuted=true, ${data})`,
  `A.$.parseJSON(${literal} + (globalThis.imageParserExecuted=true))`,
  `A.$.parseJSON(${literal}, (globalThis.imageParserExecuted=true))`,
  `A.$.parseJSON(${literal}) || (globalThis.imageParserExecuted=true)`,
  `${data}.map(()=>globalThis.imageParserExecuted=true)`,
  `JSON.parse(${literal})`,
  `A.$.parseJSON('\\q')`,
 ])assert.throws(()=>parseScripts([scriptFor(expression)]));
 assert.equal(globalThis.imageParserExecuted,false);
 delete globalThis.imageParserExecuted;
});

test('identical duplicate arrays are accepted and conflicting arrays fail closed',()=>{
 const first=JSON.stringify([{variant:'PT01',hiRes:'https://example.com/one.jpg'}]);
 const second=JSON.stringify([{variant:'PT01',hiRes:'https://example.com/two.jpg'}]);
 assert.equal(parseScripts([scriptFor(first),scriptFor(`A.$.parseJSON(${singleLiteral(first)})`)]).images.length,1);
 assert.throws(()=>parseScripts([scriptFor(first),scriptFor(second)]),/Conflicting/);
 assert.throws(()=>parseScripts([`data={'colorImages':{'initial':${first},'initial':${second}}};`]),/Conflicting/);
});
