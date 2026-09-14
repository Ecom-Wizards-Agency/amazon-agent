import test from 'node:test';
import assert from 'node:assert/strict';
import {activityRequestMatch,collectActivity} from '../flatfilepro-activity.mjs';

const field='other_product_image_locator_1__1__media_location';
const account={seller_id:'SELLER',marketplace_id:'MARKET'};
const input={account,submission_id:'run-123',plan_hash:'hash',expected_rows:{SKU1:{[field]:'https://images.example/one'},SKU2:{[field]:'https://images.example/two'}}};
const summary={parentEventId:12,reflected:2,inProgress:0,rejected:0,failed:0};
const item=sku=>({sku,sellerId:'SELLER',marketplaceId:'MARKET',attributes:[{destinationPath:'other_product_image_locator_1.0.media_location',submittedValue:input.expected_rows[sku][field],liveValue:input.expected_rows[sku][field],status:'reflected'}]});
const page=(items,more=false,cursor=null)=>({summary,items,hasMore:more,nextCursor:cursor});

test('known run collector requires complete exact paginated SKU and attribute evidence',async()=>{
  const cursors=[];
  const result=await collectActivity(input,async cursor=>{cursors.push(cursor);return cursor===null?page([item('SKU1')],true,'next'):page([item('SKU2')]);});
  assert.deepEqual(cursors,[null,'next']);assert.equal(result.complete,true);
  assert.equal(result.attributes.length,2);assert.equal(result.attributes[0].field,field);
  assert.equal(result.source_id,'https://app.flatfile.pro/activity/import/run-123');
});
test('wrong account, extra/missing/duplicate SKU, field and value cannot become complete',async()=>{
  for(const mutation of [
    rows=>rows.slice(0,1),rows=>[...rows,rows[0]],rows=>[{...rows[0],sku:'OTHER'},rows[1]],
    rows=>[{...rows[0],sellerId:'OTHER'},rows[1]],
    rows=>[{...rows[0],attributes:[]},rows[1]],
    rows=>[{...rows[0],attributes:[{...rows[0].attributes[0],destinationPath:'main_product_image_locator.0.media_location'}]},rows[1]],
    rows=>[{...rows[0],attributes:[{...rows[0].attributes[0],submittedValue:'different'}]},rows[1]],
    rows=>[{...rows[0],attributes:[{...rows[0].attributes[0],liveValue:'different'}]},rows[1]],
    rows=>[{...rows[0],attributes:[{...rows[0].attributes[0],status:'complete'}]},rows[1]],
  ])await assert.rejects(collectActivity(input,async()=>page(mutation([item('SKU1'),item('SKU2')]))));
});
test('pending and rejected attributes remain explicit evidence, not Amazon verification',async()=>{
  const rows=[item('SKU1'),item('SKU2')];
  rows[0].attributes[0].status='pending';rows[0].attributes[0].liveValue='old';rows[1].attributes[0].status='rejected';
  const result=await collectActivity(input,async()=>page(rows));
  assert.deepEqual(result.attributes.map(value=>value.status),['pending','rejected']);assert.equal(result.complete,true);
  assert.equal(result.verified,undefined);
});
test('missing or contradictory pagination cannot produce complete evidence',async()=>{
  for(const value of [{summary,items:[item('SKU1')]},page([item('SKU1')],true,null),page([item('SKU1'),item('SKU2')],false,'unused')])
    await assert.rejects(collectActivity(input,async()=>value));
  await assert.rejects(collectActivity(input,async()=>page([item('SKU1')],true,'repeat')));
});
test('network matcher binds run ID, origin, seller, marketplace and cursor',()=>{
  const url='https://api.flatfile.pro/listing-update-runs/run-123/items?seller_id=SELLER&marketplace_id=MARKET&pageSize=25';
  assert.equal(activityRequestMatch(url,input,null),'items');
  for(const other of [url.replace('api.flatfile.pro','other.example'),url.replace('run-123','run-999'),url.replace('SELLER','OTHER'),url+'&seller_id=SELLER',url+'&cursor=other',url.replace('25','50')])assert.equal(activityRequestMatch(other,input,null),null);
});
