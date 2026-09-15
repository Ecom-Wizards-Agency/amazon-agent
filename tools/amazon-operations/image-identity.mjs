/** Exact pre-submit identity comparison; additions and omissions both matter. */
export const IMAGE_IDENTITY_KEYS=Object.freeze([
    'sku',
    'asin',
    'mpn',
    'color',
    'color_code',
    'size',
    'parentage',
    'parent_sku',
    'listing_relationship_evidence',
    'product_type',
    'archived',
    'itemName',
    'model_name',
    'model_number',
    'item_name.0.value',
    'model_name.0.value',
    'model_number.0.value',
    'part_number.0.value',
    'color.0.value',
    'size.0.value',
    'parentage_level.0.value',
    'child_parent_sku_relationship.0.parent_sku',
    'externally_assigned_product_identifier.0.value',
    'merchant_suggested_asin.0.value',
]);
const aliases=new Set(IMAGE_IDENTITY_KEYS);
const attributes=/^(?:item_name|model_name|model_number|part_number|color|size|parentage_level|child_parent_sku_relationship|externally_assigned_product_identifier|merchant_suggested_asin)\./;
export function listingIdentity(row){
 return Object.fromEntries(Object.entries(row).filter(([key])=>aliases.has(key)||attributes.test(key)).sort(([a],[b])=>a<b?-1:a>b?1:0));
}
export function verifyListingIdentities(expected,rows,targets=[...new Set([...Object.keys(expected||{}),...Object.keys(rows||{})])]){
 const missing=[];
 for(const sku of targets){
  const identity=expected&&Object.hasOwn(expected,sku)?expected[sku]:null;
  if(!identity||typeof identity!=='object'||Array.isArray(identity)||!Object.keys(listingIdentity(identity)).length){
   missing.push(sku);continue;
  }
  const fields=[...new Set([...IMAGE_IDENTITY_KEYS,...Object.keys(listingIdentity(rows[sku]||{}))])].filter(field=>!Object.hasOwn(identity,field));
  if(fields.length)missing.push(sku+' (missing fields: '+fields.join(', ')+')');
 }
 if(!targets.length||missing.length){
  const legacy=expected==null?'Plan predates identity capture; ':'';
  throw Object.assign(new Error('IDENTITY_MAP_INCOMPLETE: '+legacy+'missing or incomplete identity for SKUs: '+missing.join(', ')+'; re-prepare the plan'),{code:'IDENTITY_MAP_INCOMPLETE'});
 }
 for(const sku of targets){
  const identity=expected[sku];
  if(JSON.stringify(listingIdentity(rows[sku]||{}))!==JSON.stringify(listingIdentity(identity)))
   throw new Error('Pre-submit listing model, color, size or identity changed: '+sku);
 }
}
