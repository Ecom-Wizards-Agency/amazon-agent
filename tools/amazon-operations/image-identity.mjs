/** Exact pre-submit identity comparison; additions and omissions both matter. */
const aliases=new Set(['sku','asin','mpn','color','color_code','size','parentage','parent_sku',
 'listing_relationship_evidence','product_type','archived','itemName','model_name','model_number']);
const attributes=/^(?:item_name|model_name|model_number|part_number|color|size|parentage_level|child_parent_sku_relationship|externally_assigned_product_identifier|merchant_suggested_asin)\./;
export function listingIdentity(row){
 return Object.fromEntries(Object.entries(row).filter(([key])=>aliases.has(key)||attributes.test(key)).sort(([a],[b])=>a<b?-1:a>b?1:0));
}
export function verifyListingIdentities(expected,rows){
 for(const [sku,identity] of Object.entries(expected||{})){
  if(JSON.stringify(listingIdentity(rows[sku]||{}))!==JSON.stringify(listingIdentity(identity)))
   throw new Error('Pre-submit listing model, color, size or identity changed: '+sku);
 }
}
