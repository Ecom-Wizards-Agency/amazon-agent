import test from 'node:test';
import assert from 'node:assert/strict';
import {verifyListingIdentities} from '../image-identity.mjs';
test('final browser pre-submit check rejects changed, added and missing identity fields',()=>{
 const identity={sku:'S',asin:'B012345678','model_number.0.value':'11010040','color.0.value':'Navy','size.0.value':'86'};
 for(const key of ['model_number.0.value','color.0.value','size.0.value','part_number.0.value']){
  assert.throws(()=>verifyListingIdentities({S:identity},{S:{...identity,[key]:'Changed'}}),/identity changed/);
 }
 const missing={...identity};delete missing['size.0.value'];
 assert.throws(()=>verifyListingIdentities({S:identity},{S:missing}),/identity changed/);
 assert.throws(()=>verifyListingIdentities({S:identity},{}),/identity changed/);
 assert.doesNotThrow(()=>verifyListingIdentities({S:identity},{S:{...identity,'other_product_image_locator_1.0.media_location':'new',price:'10',observed_at:'now'}}));
});
