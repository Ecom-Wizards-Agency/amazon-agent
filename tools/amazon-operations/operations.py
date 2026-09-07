#!/usr/bin/env python3
"""Amazon operation plans and restart-safe journals. JSON protocol version 1.

This local trusted-process boundary is not an authentication service. The caller
must validate the principal before supplying a grant or collected evidence.
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import fcntl
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
ALIASES = {'seo.apply': 'seo.update', 'flatfile.apply': 'flatfilepro.update', 'listing.images.replace': 'listing.images', 'catalog.products.create': 'catalog.change', 'catalog.family.update': 'catalog.change', 'account_health.fields.restore': 'flatfilepro.update', 'account_health.images.restore': 'listing.images'}
OPERATIONS = {'seo.update', 'flatfilepro.update', 'listing.images', 'catalog.change', 'shipment.create'} | set(ALIASES)

def operation_kind(value):
    return ALIASES.get(value, value)
TERMINAL = {'verified', 'failed'}
SEO_FIELDS = re.compile(r'^(item_name|bullet_point|product_description|generic_keyword|title_differentiation)([._]|$)|^itemName$')

class OperationError(ValueError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def require(condition, code, message):
    if not condition:
        raise OperationError(code, message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def timestamp(value):
    try:
        result = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
        require(result.tzinfo is not None, 'invalid_time', 'Timestamps require a timezone')
        return result
    except (ValueError, TypeError, AttributeError) as exc:
        raise OperationError('invalid_time', 'Expected an ISO timestamp with timezone') from exc


def atomic_json(path, value):
    path = Path(path)
    fd, name = tempfile.mkstemp(prefix='.write-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(canonical(value) + b'\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def evidence_tools():
    return load_module('merlin_operation_evidence', 'tools/amazon-operations/evidence.py')


def verify_hosted_asset(path, url):
    module = evidence_tools()
    data = module.fetch_public_image(url)
    method = module.same_image_content(Path(path).read_bytes(), data)
    require(method is not None, 'hosted_image_mismatch', 'Hosted image does not match the approved local image bytes or decoded pixels')
    return {'sha256': hashlib.sha256(data).hexdigest(), 'match_method': method, 'verified_at': now()}


def health_request(request):
    if not request['operation'].startswith('account_health.'):
        return request
    inputs, acct = request['inputs'], request['account']
    approved = inputs.get('approved_product_data')
    scoped(approved, acct, 'approved product data')
    require(approved.get('approved') is True and approved.get('verified') is True and approved.get('source_id') and approved.get('approved_by'), 'unapproved_product_data', 'Routine restoration requires approved verified product data and provenance')
    timestamp(approved.get('verified_at'))
    require(inputs.get('finding_id') and isinstance(inputs.get('required_missing'), dict) and set(inputs['required_missing']) == set(request['targets']), 'missing_health_scope', 'Account Health finding and exact required-missing field scope are required')
    live = inputs.get('live')
    scoped(live, acct, 'live missing-field evidence')
    desired = {}
    for sku, fields in inputs['required_missing'].items():
        require(isinstance(fields, list) and fields, 'missing_health_scope', 'Each affected SKU requires exact missing fields')
        desired[sku] = {}
        for field in fields:
            require(not re.search(r'^(price|standard_price|purchasable_offer|quantity|fulfillment|condition|parent|child_parent|variation|product_type|record_action|item_sku)', field, re.I), 'health_scope_violation', 'Routine restoration cannot change offers, inventory, identity or relationships')
            current = live.get('rows', {}).get(sku, {}).get(field, '__unknown__')
            value = approved.get('rows', {}).get(sku, {}).get(field)
            require(value is not None and as_text(value).strip(), 'missing_approved_value', 'Approved source lacks a required nonempty restoration value')
            require(current != '__unknown__', 'missing_live_field', 'Current field absence must be positively observed')
            require(not as_text(current).strip() or as_text(current) == as_text(value), 'health_conflict', 'Routine restoration cannot overwrite a nonempty conflicting field')
            desired[sku][field] = value
    if inputs.get('desired_rows') is not None:
        require(inputs['desired_rows'] == desired, 'health_source_mismatch', 'Requested restoration differs from approved product facts')
    inputs['desired_rows'] = desired
    inputs['scope_fields'] = list(dict.fromkeys(field for fields in inputs['required_missing'].values() for field in fields))
    if request['operation'] == 'account_health.images.restore':
        approved_images = {(x.get('sku'), x.get('slot')): x for x in approved.get('images', [])}
        for image in inputs.get('images', []):
            source = approved_images.get((image.get('sku'), image.get('slot')), {})
            require(source.get('url') == image.get('url') and source.get('sha256') == image.get('artifact', {}).get('sha256'), 'health_source_mismatch', 'Image restoration must use the exact approved hosted asset')
            field = inputs.get('image_fields', {}).get(image.get('slot'))
            require(desired.get(image.get('sku'), {}).get(field) == image.get('url'), 'health_source_mismatch', 'Approved image and approved field restoration values differ')
    return request


def account(value):
    require(isinstance(value, dict), 'missing_account', 'account is required')
    for key in ('client_slug', 'profile_key', 'marketplace'):
        require(isinstance(value.get(key), str) and value[key].strip(), 'missing_account', f'account.{key} is required')
    return value


def scoped(document, expected, label):
    require(isinstance(document, dict) and document.get('account') == expected,
            'identity_mismatch', f'{label} account must exactly match the operation account')


def input_artifact(spec, directory, name):
    require(isinstance(spec, dict) and spec.get('path') and spec.get('sha256'), 'missing_artifact', f'{name} needs path and sha256')
    source = Path(spec['path']).expanduser().resolve()
    require(source.is_file(), 'missing_artifact', f'{name} file is missing')
    require(file_hash(source) == spec['sha256'], 'artifact_changed', f'{name} checksum mismatch')
    target = directory / (name + source.suffix.lower())
    shutil.copyfile(source, target)
    require(file_hash(target) == spec['sha256'], 'artifact_changed', f'{name} changed while copied')
    return target


def as_text(value):
    require(value is None or isinstance(value, (str, int, float)) and not isinstance(value, bool), 'invalid_value', 'Field values must be text or numbers')
    if isinstance(value, float):
        require(math.isfinite(value), 'invalid_value', 'Field values must be finite')
    return '' if value is None else str(value)


def changed_fields(desired, live, targets, fields):
    require(isinstance(fields, list) and fields and len(set(fields)) == len(fields), 'missing_scope', 'scope_fields must be a nonempty unique list')
    require(set(desired) <= set(targets), 'scope_violation', 'Desired rows include unrequested SKUs')
    result = []
    for sku in targets:
        require(sku in desired and sku in live, 'missing_live_row', f'Both desired and current rows are required for {sku}')
        require(set(desired[sku]) <= set(fields), 'scope_violation', f'Unrequested fields for {sku}')
        for field, value in desired[sku].items():
            require(field in live[sku], 'missing_live_field', f'Current {sku}/{field} is unknown')
            before, after = as_text(live[sku][field]), as_text(value)
            if before != after:
                result.append({'sku': sku, 'field': field, 'before': before, 'after': after})
    return result


def prepare_copy(request, directory):
    inputs, acct = request['inputs'], request['account']
    live = inputs.get('live')
    scoped(live, acct, 'live listing evidence')
    timestamp(live.get('observed_at'))
    require(timestamp(live['observed_at']) <= timestamp(now()) + dt.timedelta(minutes=5), 'invalid_time', 'Live evidence cannot be future dated')
    if operation_kind(request['operation']) == 'seo.update':
        approved = inputs.get('approved_seo')
        if not approved:
            return {'status': 'awaiting_input', 'required_inputs': ['approved_seo'], 'handoff': {'skill': 'amazon-seo', 'reason': 'Run existing product-facts, research and SEO workflow; return reviewed copy and source provenance'}}
        scoped(approved, acct, 'approved SEO')
        require(approved.get('approved') is True and approved.get('source_id') and approved.get('approved_by'), 'unapproved_copy', 'SEO requires approved copy with source_id and approved_by')
        timestamp(approved.get('approved_at'))
        require(approved.get('superseded') is not True, 'superseded_copy', 'Do not apply superseded SEO')
        desired = approved.get('rows', {})
        require(all(SEO_FIELDS.search(field) for row in desired.values() for field in row), 'scope_violation', 'SEO cannot modify offer, inventory, image or relationship fields')
    else:
        desired = inputs.get('desired_rows', {})
    changes = changed_fields(desired, live.get('rows', {}), request['targets'], inputs.get('scope_fields'))
    if not changes:
        return {'status': 'verified', 'no_changes': True, 'changes': [], 'expected_rows': desired, 'verification': 'Current supplied listing evidence already matches requested fields', 'observed_at': live['observed_at'], 'source_id': live.get('source_id', 'supplied-live-listing-evidence')}
    source = input_artifact(inputs.get('source_export'), directory, 'source-export')
    prep = load_module('merlin_ffp_prep', 'skills/amazon-flatfilepro/scripts/prepare_flatfilepro_upload.py')
    headers = prep.read_source_headers(source)
    source_rows = prep.read_source_rows(source, headers)
    require(len(headers) == len(set(headers)), 'ambiguous_headers', 'Source export has duplicate headers')
    canon = [prep.canonical_attribute(h) for h in headers]
    require(len(canon) == len(set(canon)), 'ambiguous_headers', 'Source headers canonicalize to duplicate attributes')
    for item in changes:
        require(item['field'] in headers, 'unknown_field', f"Exact source header unavailable: {item['field']}")
        require(item['sku'] in source_rows, 'missing_source_row', f"Source export missing SKU: {item['sku']}")
        require(as_text(source_rows[item['sku']].get(item['field'])) == item['before'], 'stale_source', 'Source export does not match current listing evidence')
    transmitted = list(dict.fromkeys(c['field'] for c in changes))
    companions = {'unit_count.0.value': ['unit_count.0.type.value'], 'unit_count.0.type.value': ['unit_count.0.value']}
    for prefix in ('item_weight', 'item_package_weight', 'item_display_weight'):
        companions[prefix + '.0.value'] = [prefix + '.0.unit']
        companions[prefix + '.0.unit'] = [prefix + '.0.value']
    for field in list(transmitted):
        for required in companions.get(field, []):
            require(required in headers and required in inputs['scope_fields'], 'missing_companion', f'Exact scoped companion field required: {required}')
            if required not in transmitted:
                transmitted.append(required)
    expected_skus = {c['sku'] for c in changes}
    for sku in expected_skus:
        for field in transmitted:
            require(field in live['rows'][sku] and as_text(source_rows[sku].get(field)) == as_text(live['rows'][sku][field]), 'stale_source', f'Carried field {sku}/{field} does not match live evidence')
    changes_path = directory / 'changes.csv'
    with changes_path.open('w', newline='', encoding='utf-8') as stream:
        writer = csv.DictWriter(stream, fieldnames=['sku', 'attribute', 'value'])
        writer.writeheader()
        writer.writerows({'sku': c['sku'], 'attribute': c['field'], 'value': c['after']} for c in changes)
        first_sku = changes[0]['sku']
        writer.writerows({'sku': first_sku, 'attribute': field, 'value': source_rows[first_sku][field]} for field in transmitted if field not in {c['field'] for c in changes})
    output = directory / 'upload.xlsx'
    with contextlib.redirect_stdout(io.StringIO()):
        result = prep.main(['--source', str(source), '--changes', str(changes_path), '--output', str(output), '--fill-unchanged'])
    require(result == 0, 'preparation_failed', 'FlatFilePro preparation failed')
    upload_headers = prep.read_source_headers(output)
    upload_rows = prep.read_source_rows(output, upload_headers)
    expected_skus = {c['sku'] for c in changes}
    require(set(upload_rows) == expected_skus, 'artifact_mismatch', 'Upload row coverage differs from changed SKUs')
    expected = {sku: {prep.canonical_attribute(field): as_text(source_rows[sku].get(field)) for field in transmitted} for sku in expected_skus}
    for c in changes:
        expected[c['sku']][prep.canonical_attribute(c['field'])] = c['after']
    for sku, row in expected.items():
        require({k: v for k, v in upload_rows[sku].items() if k != 'sku'} == row, 'artifact_mismatch', 'Reopened upload does not match full-grid expected values')
    return {'status': 'prepared', 'changes': changes, 'expected_rows': expected, 'upload': str(output), 'mapping': [h for h in upload_headers if h != 'sku'], 'adapter': 'flatfilepro.cdp', 'requires_live_canary': True, 'sku_asins': inputs.get('sku_asins', {}), 'restore_missing_only': request['operation'].startswith('account_health.'), 'finding_id': inputs.get('finding_id')}


def prepare_images(request, directory):
    inputs = request['inputs']
    manifest = inputs.get('images')
    require(isinstance(manifest, list) and manifest, 'missing_images', 'images manifest is required')
    changes, seen = [], set()
    for image in manifest:
        sku, slot = image.get('sku'), image.get('slot')
        require(sku in request['targets'] and isinstance(slot, str) and re.fullmatch(r'MAIN|PT0[1-9]|SWCH', slot), 'scope_violation', 'Image needs a requested SKU and MAIN/PT01..PT09/SWCH slot')
        require((sku, slot) not in seen, 'duplicate_image', 'Duplicate SKU/image slot')
        seen.add((sku, slot))
        path = input_artifact(image.get('artifact'), directory, f'image-{len(changes)}')
        from PIL import Image
        with Image.open(path) as im:
            require(im.format in {'JPEG', 'PNG'} and min(im.size) >= 500, 'invalid_image', 'Images must be JPEG/PNG with both dimensions at least 500px')
            dimensions = list(im.size)
            im.verify()
        url = image.get('url', '')
        parsed = urlsplit(url)
        require(parsed.scheme == 'https' and parsed.hostname and not parsed.username and not parsed.password, 'invalid_image_url', 'Image upload URLs must be HTTPS without embedded credentials')
        hosted = verify_hosted_asset(path, url)
        changes.append({'hosted_verification': hosted, 'sku': sku, 'slot': slot, 'sha256': file_hash(path), 'path': str(path), 'url': url, 'dimensions': dimensions})
    require({c['sku'] for c in changes} == set(request['targets']), 'missing_images', 'Every target requires an image')
    fields = inputs.get('image_fields', {})
    require(all(image['slot'] in fields for image in changes), 'missing_image_mapping', 'image_fields must map each slot to an exact source-export header')
    require(all(re.fullmatch(r'(main_product_image_locator|other_product_image_locator(_[0-9]+)?|swatch_product_image_locator)([._].*)?', field) for field in fields.values()), 'scope_violation', 'Image mapping must use image attributes')
    copy_request = json.loads(json.dumps(request))
    copy_request['operation'] = 'flatfilepro.update'
    desired = {}
    for image in changes:
        desired.setdefault(image['sku'], {})[fields[image['slot']]] = image['url']
    copy_request['inputs']['desired_rows'] = desired
    copy_request['inputs']['scope_fields'] = list(dict.fromkeys(fields[image['slot']] for image in changes))
    prepared = prepare_copy(copy_request, directory)
    if prepared['status'] == 'verified':
        prepared.update(status='prepared', adapter='image.verify', no_changes=True, requires_live_canary=False)
    prepared['images'] = changes
    prepared['restore_missing_only'] = request['operation'].startswith('account_health.')
    prepared['sku_asins'] = inputs.get('sku_asins', {})
    return prepared


def prepare_catalog(request, directory):
    manifest = json.loads(json.dumps(request['inputs'].get('manifest', {})))
    acct = request['account']
    seller_account = acct.get('seller_account') or acct.get('seller_central_name')
    merchant_id = acct.get('merchant_id') or acct.get('seller_id')
    require(manifest.get('marketplace') == acct['marketplace'] and manifest.get('client') == acct['client_slug'], 'identity_mismatch', 'Catalog manifest client/marketplace mismatch')
    require(seller_account and manifest.get('seller_account') == seller_account, 'identity_mismatch', 'Catalog seller account mismatch')
    require(merchant_id, 'missing_merchant_id', 'Verified merchant_id is required for template ownership')
    sources = request['inputs'].get('source_artifacts', {})
    for key in ('category_listings_report', 'blank_template'):
        copied = input_artifact(sources.get(key), directory, key)
        manifest.setdefault('source', {})[key] = str(copied)
    import openpyxl
    book = openpyxl.load_workbook(manifest['source']['blank_template'], read_only=True, keep_vba=False)
    try:
        settings = str(book['Template']['A1'].value)
        match = re.search(r'contributorId=amzn1\.cr\.o\.([^;,&\s]+)', settings)
        require(match and match.group(1) == merchant_id, 'template_owner_mismatch', 'Template contributorId does not match verified merchant_id')
    finally:
        book.close()
    module = load_module('merlin_catalog_pack', 'tools/amazon-catalog-change-pack/catalog_change_pack.py')
    manifest['output_dir'] = str(directory / 'catalog-pack')
    manifest['_manifest_path'] = str(directory / 'catalog-manifest.json')
    if manifest.get('operation') == 'create_products':
        return prepare_standalone_products(request, directory, manifest, module)
    specs = module.build_specs(manifest)
    # Exact scope includes every affected parent and child, including indirectly detached children.
    family = manifest.get('family', {})
    affected = {str(c['sku']) for c in family.get('children', [])}
    affected.update(family.get('removed_child_skus', []))
    affected.update(filter(None, [family.get('old_parent_sku'), family.get('parent', {}).get('sku')]))
    if manifest['operation'] in {'delete_parent', 'rebuild_family', 'detach_children', 'reparent_children'}:
        current_family = request['inputs'].get('existing_family')
        scoped(current_family, acct, 'current family evidence')
        timestamp(current_family.get('observed_at'))
        old_parent = family.get('old_parent_sku') or family['parent']['sku']
        actual_children = {sku for sku, parent in current_family.get('relationships', {}).items() if parent == old_parent}
        declared_children = {c['sku'] for c in family.get('children', [])} | set(family.get('removed_child_skus', []))
        require(actual_children <= declared_children, 'undeclared_children', 'Parent deletion would detach children missing from the explicit plan')
    require(affected <= set(request['targets']), 'scope_violation', 'Catalog plan touches an unrequested parent or child')
    atomic_json(directory / 'catalog-manifest.json', manifest)
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            pack = module.build(manifest)
    except module.CatalogError as exc:
        raise OperationError('invalid_catalog', str(exc)) from exc
    files = sorted((pack / '03-upload-ready').glob('*.xlsm'))
    require(len(files) == len(specs), 'artifact_mismatch', 'Catalog stage coverage mismatch')
    report = evidence_tools().report_rows(manifest['source']['category_listings_report'])
    protected = sorted({c['sku'] for c in family.get('children', []) if c.get('status') == 'existing'} | set(family.get('removed_child_skus', [])))
    offer_baseline = {sku: {field: value for field in ('price', 'quantity', 'fulfillment_channel', 'condition') if (value := evidence_tools().field_value(report.get(sku, {}), field)) is not None} for sku in protected}
    return {'status': 'prepared', 'manifest': manifest, 'protected_offer_values': offer_baseline, 'stages': [{'index': i + 1, 'upload': str(path), 'requires_prior_verified': i > 0, 'skus': [row['sku'] for row in specs[i][1]], 'full_update_values': {row['sku']: {k: v for k, v in row.items() if k not in {'sku', 'action'} and v is not None} for row in specs[i][1] if row.get('action') == module.FULL_UPDATE}} for i, path in enumerate(files)], 'protected_children': sorted({c['sku'] for c in family.get('children', []) if c.get('status') == 'existing'} | set(family.get('removed_child_skus', []))), 'adapter': 'catalog.cdp', 'requires_live_canary': True}


def prepare_standalone_products(request, directory, manifest, module):
    """Full-update new standalone rows using the established template machinery."""
    products = manifest.get('products', [])
    require(isinstance(products, list) and products, 'missing_products', 'create_products requires products')
    skus = [p.get('sku') for p in products]
    require(len(skus) == len(set(skus)) and set(skus) == set(request['targets']), 'scope_violation', 'New products must exactly match requested unique SKUs')
    existing = module.read_report_skus(Path(manifest['source']['category_listings_report']))
    require(not set(skus) & existing, 'existing_product', 'Full updates cannot replace existing products')
    require(len({p.get('product_type') for p in products}) == 1, 'mixed_templates', 'Create separate packs for different product types')
    rows = []
    for product in products:
        require(product.get('product_type') and product.get('title') and product.get('fields'), 'missing_product_fields', 'New products require product_type, title and exact template fields')
        fields = product['fields']
        require(not any(re.search(r'parent|variation|record_action|item_sku|contribution_sku', k, re.I) for k in fields), 'scope_violation', 'Standalone fields cannot override identity, action or relationships')
        row = {**fields, 'sku': product['sku'], 'product_type': product['product_type'], 'action': module.FULL_UPDATE, 'title': product['title']}
        if product.get('gtin_exempt') is True:
            require(not product.get('product_id'), 'invalid_gtin', 'GTIN exemption requires a blank product ID')
            row.update(external_product_id=None, external_product_id_type='GTIN Exempt')
        else:
            require(product.get('product_id') and product.get('product_id_type'), 'missing_gtin', 'A product ID/type or evidenced GTIN exemption is required')
            row.update(external_product_id=product['product_id'], external_product_id_type=product['product_id_type'])
        rows.append(row)
    output = directory / '01-create-products.xlsm'
    try:
        module.write_workbook(Path(manifest['source']['blank_template']), output, rows)
        info = module.load_template(output)
        try:
            for offset, row in enumerate(rows):
                for field, value in row.items():
                    column = module.resolve_column(info, field)
                    require(info.sheet.cell(info.data_row + offset, column).value == value, 'artifact_mismatch', 'New-product workbook differs from intended full update')
            require(not any(cell.value is not None for row in info.sheet.iter_rows(min_row=info.data_row + len(rows)) for cell in row), 'artifact_mismatch', 'Unexpected extra populated template rows')
        finally:
            module.close_workbook(info.workbook)
    except module.CatalogError as exc:
        raise OperationError('invalid_catalog', str(exc)) from exc
    return {'status': 'prepared', 'manifest': manifest, 'products': products, 'stages': [{'index': 1, 'upload': str(output), 'skus': skus, 'requires_prior_verified': False, 'full_update_values': {row['sku']: {k: v for k, v in row.items() if k not in {'sku', 'action'} and v is not None} for row in rows}}], 'protected_children': [], 'adapter': 'catalog.cdp', 'requires_live_canary': True}


def positive_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def prepare_shipment(request, directory):
    inputs = request['inputs']
    required = ['shipment_reference', 'ship_from', 'lines', 'cartons', 'carrier', 'currency', 'estimated_cost', 'client_limits', 'existing_shipments', 'ship_date', 'ship_mode', 'carrier_mode', 'packing_templates', 'label_format']
    missing = [name for name in required if inputs.get(name) is None or inputs.get(name) == '']
    if missing:
        return {'status': 'awaiting_input', 'required_inputs': missing}
    limits = inputs['client_limits']
    scoped(limits, request['account'], 'client shipment limits')
    missing_limits = [f'client_limits.{key}' for key in ('max_units', 'max_cost', 'currency', 'carriers') if limits.get(key) is None]
    if missing_limits:
        return {'status': 'awaiting_input', 'required_inputs': missing_limits}
    lines = inputs['lines']
    require(isinstance(lines, list) and lines, 'missing_lines', 'Shipment lines are required')
    quantities = {}
    for line in lines:
        sku, qty = line.get('sku'), line.get('quantity')
        require(sku in request['targets'] and sku not in quantities, 'scope_violation', 'Shipment lines require unique requested SKUs')
        require(isinstance(qty, int) and not isinstance(qty, bool) and qty > 0, 'invalid_quantity', 'Shipment quantities must be positive integers')
        quantities[sku] = qty
    require(set(quantities) == set(request['targets']), 'missing_lines', 'Every target requires a shipment quantity')
    require(positive_number(limits['max_units']) and sum(quantities.values()) <= limits['max_units'], 'quantity_limit', 'Shipment exceeds client unit limit')
    cost = inputs['estimated_cost']
    require(isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost) and cost >= 0 and positive_number(limits['max_cost']), 'invalid_cost', 'Cost and saved maximum must be finite nonnegative values')
    require(cost <= limits['max_cost'] and inputs['currency'] == limits['currency'], 'cost_limit', 'Shipment exceeds saved cost or currency limit')
    require(inputs['carrier'] in limits['carriers'], 'carrier_limit', 'Carrier is outside saved client choices')
    require(isinstance(inputs['ship_from'], dict) and all(inputs['ship_from'].get(key) for key in ('address_line1', 'city', 'postal_code', 'country')), 'missing_address', 'Complete ship-from address is required')
    packed, boxes = {sku: 0 for sku in quantities}, set()
    for carton in inputs['cartons']:
        require(carton.get('id') and carton['id'] not in boxes, 'duplicate_carton', 'Carton IDs must be unique')
        boxes.add(carton['id'])
        require(positive_number(carton.get('weight')) and carton.get('weight_unit') in {'kg', 'lb'}, 'invalid_carton', 'Carton weight and unit required')
        dims = carton.get('dimensions', [])
        require(len(dims) == 3 and all(positive_number(x) for x in dims) and carton.get('dimension_unit') in {'cm', 'in'}, 'invalid_carton', 'Three positive carton dimensions and unit required')
        for sku, qty in carton.get('contents', {}).items():
            require(sku in packed and isinstance(qty, int) and not isinstance(qty, bool) and qty > 0, 'invalid_carton', 'Carton content is outside shipment scope')
            packed[sku] += qty
    require(boxes and packed == quantities, 'carton_coverage', 'Carton quantities must exactly cover shipment lines')
    existing = inputs['existing_shipments']
    scoped(existing, request['account'], 'existing shipment evidence')
    timestamp(existing.get('observed_at'))
    for shipment in existing.get('shipments', []):
        if shipment.get('shipment_reference') == inputs['shipment_reference'] and shipment.get('status') != 'cancelled':
            raise OperationError('duplicate_shipment', 'Existing shipment already uses this shipment_reference; reconcile it instead')
    return {'status': 'prepared', 'shipment': {k: v for k, v in inputs.items() if k not in {'existing_shipments', 'client_limits'}}, 'limits': limits, 'adapter': 'shipment.cdp', 'requires_live_canary': True}


class Operations:
    def __init__(self, state_dir):
        self.root = Path(state_dir).expanduser().resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def directory(self, operation_id):
        require(isinstance(operation_id, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,99}', operation_id), 'invalid_id', 'operation_id must be a simple 1..100 character identifier')
        path = self.root / operation_id
        path.mkdir(exist_ok=True)
        require(path.resolve().parent == self.root, 'unsafe_state', 'Operation directory must not be a symlink outside state root')
        return path

    @contextlib.contextmanager
    def lock(self, directory):
        with (directory / '.lock').open('a') as stream:
            fcntl.flock(stream, fcntl.LOCK_EX)
            yield

    def view(self, directory):
        return json.loads((directory / 'journal.json').read_text())

    def persist(self, directory, state, status, **extra):
        state.update(extra, status=status, verified=status == 'verified', updated_at=now())
        state.setdefault('events', []).append({'status': status, 'at': state['updated_at']})
        atomic_json(directory / 'journal.json', state)
        return state

    def prepare(self, request):
        require(request.get('schema_version') == 1 and request.get('operation') in OPERATIONS, 'invalid_request', 'schema_version 1 and a supported operation are required')
        account(request.get('account'))
        request = json.loads(json.dumps(request))
        raw_targets = request.get('targets')
        require(isinstance(raw_targets, list), 'invalid_targets', 'targets must be a list')
        targets = [x.get('sku') if isinstance(x, dict) else x for x in raw_targets]
        request['targets'] = targets
        target_asins = {x['sku']: x['asin'] for x in raw_targets if isinstance(x, dict) and x.get('sku') and x.get('asin')}
        if target_asins:
            request.setdefault('inputs', {}).setdefault('sku_asins', target_asins)
        require(isinstance(targets, list) and targets and all(isinstance(x, str) and x for x in targets) and len(targets) == len(set(targets)), 'invalid_targets', 'targets must be unique nonempty SKU strings')
        require(isinstance(request.get('inputs'), dict), 'missing_inputs', 'inputs object required')
        request = health_request(request)
        directory = self.directory(request.get('operation_id'))
        with self.lock(directory):
            fingerprint = digest(request)
            if (directory / 'plan.json').exists():
                old = json.loads((directory / 'plan.json').read_text())
                require(old['request_hash'] == fingerprint, 'immutable_request', 'An operation ID cannot be reused with different inputs; create a new revision ID')
                return self.view(directory)
            handlers = {'seo.update': prepare_copy, 'flatfilepro.update': prepare_copy, 'listing.images': prepare_images, 'catalog.change': prepare_catalog, 'shipment.create': prepare_shipment}
            body = handlers[operation_kind(request['operation'])](request, directory)
            artifacts = [{'path': str(p), 'sha256': file_hash(p)} for p in sorted(directory.rglob('*')) if p.is_file() and p.name != '.lock']
            plan = {'schema_version': 1, 'operation_id': request['operation_id'], 'operation': request['operation'], 'account': request['account'], 'targets': targets, 'request_hash': fingerprint, 'prepared_at': now(), 'body': body, 'artifacts': artifacts}
            atomic_json(directory / 'plan.json', plan)
            initial = {'schema_version': 1, 'operation_id': request['operation_id'], 'operation': request['operation'], 'plan_hash': digest(plan), 'plan_path': str(directory / 'plan.json'), 'account': request['account'], 'targets': targets, 'required_inputs': body.get('required_inputs', []), 'capability': {'adapter': body.get('adapter'), 'requires_live_canary': body.get('requires_live_canary', False)}}
            if body['status'] == 'verified':
                evidence = {'schema_version': 1, 'account': plan['account'], 'plan_hash': digest(plan), 'source_id': body['source_id'], 'observed_at': body['observed_at'], 'processing_status': 'live_observed', 'no_changes': True, 'rows': body['expected_rows']}
                path = directory / f'evidence-{digest(evidence)}.json'
                atomic_json(path, evidence)
                initial.update(no_changes=True, effects_started=False, evidence_path=str(path))
            return self.persist(directory, initial, body['status'])

    def bound(self, directory, request):
        state = self.view(directory)
        plan = json.loads((directory / 'plan.json').read_text())
        require(request.get('schema_version') == 1 and request.get('plan_hash') == state['plan_hash'] == digest(plan), 'plan_mismatch', 'Plan hash mismatch')
        for artifact in plan['artifacts']:
            path = Path(artifact['path'])
            require(path.is_file() and file_hash(path) == artifact['sha256'], 'artifact_changed', 'Prepared artifact changed or disappeared')
        return state, plan

    def execute(self, request):
        directory = self.directory(request.get('operation_id'))
        with self.lock(directory):
            state, plan = self.bound(directory, request)
            grant = request.get('grant', {})
            require(grant.get('execute') is True and grant.get('account') == plan['account'] and grant.get('operation') == plan['operation'] and grant.get('plan_hash') == state['plan_hash'] and set(x.get('sku') if isinstance(x, dict) else x for x in grant.get('targets', [])) == set(plan['targets']), 'grant_mismatch', 'Execution grant must bind exact account, operation, targets and plan hash')
            if plan['body'].get('no_changes') and state['status'] == 'prepared':
                return self.persist(directory, state, 'processing', phase='verification', effects_started=False, next_action='reconcile', reason='live_image_verification_required')
            if state['status'] in TERMINAL or state['status'] in {'processing', 'uncertain'} or (state['status'] == 'partial' and not state.get('next_stage') and state.get('next_action') != 'execute'):
                return state
            require(state['status'] in {'prepared', 'blocked', 'partial'}, 'not_ready', 'Operation requires inputs before execution')
            adapters = {'flatfilepro.cdp': 'flatfilepro.mjs', 'catalog.cdp': 'catalog.mjs', 'shipment.cdp': 'shipments.mjs'}
            adapter_script = adapters.get(plan['body'].get('adapter'))
            if not adapter_script or not (ROOT / 'tools/amazon-operations' / adapter_script).is_file():
                return self.persist(directory, state, 'blocked', reason='adapter_unavailable', message='Preparation is complete. No verified submission adapter is installed for this operation.')
            require(grant.get('allow_live_canary') is True or grant.get('allow_validated_adapter') is True, 'canary_required', 'This adapter needs an explicitly scoped live canary before production enablement')
            if plan['body'].get('restore_missing_only'):
                receipt = state.get('preflight_receipt')
                if receipt and timestamp(now()) - timestamp(receipt['report_generated_at']) <= dt.timedelta(minutes=5):
                    require(file_hash(receipt['path']) == receipt['sha256'], 'artifact_changed', 'Fresh preflight report changed')
                    fresh = {**receipt, 'rows': evidence_tools().report_rows(receipt['path'])}
                else:
                    fresh = self.collect_export(directory, state, plan, purpose='preflight')
                if fresh is None:
                    return self.persist(directory, state, 'processing', phase='preflight', effects_started=False, reason='fresh_report_pending', next_action='execute', retry_after_seconds=60)
                self.health_preflight(plan, fresh)
                changes = plan['body'].get('changes', [])
                if all(evidence_tools().field_value(fresh['rows'].get(c['sku'], {}), c['field']) == c['after'] for c in changes):
                    return self.verified_health_noop(directory, state, plan, fresh)
            for image in plan['body'].get('images', []):
                verify_hosted_asset(image['path'], image['url'])
            # Journal intent before spawning; loss of response can never cause blind replay.
            self.persist(directory, state, 'uncertain', execution_started_at=now(), reason='submission_attempt_started', execution_stage=state.pop('next_stage', state.get('execution_stage', 1)), submission_id=None, effects_started=True, phase='executing', next_action=None)
            envelope = {'schema_version': 1, 'plan': plan, 'plan_path': str(directory / 'plan.json'), 'plan_hash': state['plan_hash'], 'receipt_path': str(directory / 'adapter-receipt.json'), 'stage': state['execution_stage']}
            atomic_json(directory / 'adapter-input.json', envelope)
            try:
                result = subprocess.run(['node', str(ROOT / 'tools/amazon-operations' / adapter_script), '--request', str(directory / 'adapter-input.json')], capture_output=True, text=True, timeout=1800, check=False, env={**os.environ, 'CDP_PORT': '9222'})
                response = json.loads(result.stdout)
                require(response.get('plan_hash') == state['plan_hash'], 'adapter_identity', 'Adapter result is not bound to this plan')
                status = response.get('status')
                require(status in {'processing', 'blocked', 'failed', 'uncertain'}, 'adapter_status', 'Adapter cannot claim verified completion')
                return self.persist(directory, state, status, adapter_result=response, submission_id=response.get('submission_id'), reason=response.get('reason'))
            except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError, OperationError) as exc:
                return self.persist(directory, state, 'uncertain', reason='adapter_result_uncertain', message=str(exc))

    def verified_health_noop(self, directory, state, plan, fresh):
        evidence = {'schema_version': 1, 'account': plan['account'], 'plan_hash': state['plan_hash'], 'source_id': fresh.get('source_id', fresh['path']), 'observed_at': now(), 'processing_status': 'live_observed', 'no_changes': True, 'report_artifact': {key: fresh[key] for key in ('path', 'sha256', 'report_generated_at') if key in fresh}, 'rows': {sku: {field: evidence_tools().field_value(fresh['rows'].get(sku, {}), field) for field in fields} for sku, fields in plan['body'].get('expected_rows', {}).items()}}
        path = directory / f'evidence-{digest(evidence)}.json'
        atomic_json(path, evidence)
        return self.persist(directory, state, 'verified', no_changes=True, effects_started=False, reason='already_restored', evidence_path=str(path))

    def health_preflight(self, plan, fresh):
        changes = plan['body'].get('changes', [])
        evidence = evidence_tools()
        values = [evidence.field_value(fresh['rows'].get(c['sku'], {}), c['field']) for c in changes]
        if changes and all(value == change['after'] for value, change in zip(values, changes)):
            return
        require(changes and all(value is not None and not value.strip() for value in values), 'health_conflict', 'Fresh live fields are no longer all missing; automatic restoration stopped')
        changed_cells = {(c['sku'], evidence.canonical_header(c['field'])) for c in changes}
        for sku, fields in plan['body'].get('expected_rows', {}).items():
            for field, expected in fields.items():
                if (sku, evidence.canonical_header(field)) in changed_cells:
                    continue
                current = evidence.field_value(fresh['rows'].get(sku, {}), field)
                require(current is not None and current == as_text(expected), 'health_conflict', f'Carried field {sku}/{field} is missing or changed; automatic restoration stopped')

    def run_collector(self, directory, script, request, timeout=180):
        require(script in {'catalog-export.mjs', 'image-evidence.mjs'}, 'invalid_collector', 'Unknown fixed collector')
        input_path = directory / (script.replace('.mjs', '') + '-input.json')
        atomic_json(input_path, request)
        try:
            result = subprocess.run(['node', str(ROOT / 'tools/amazon-operations' / script), '--request', str(input_path)], capture_output=True, text=True, timeout=timeout, check=False, env={**os.environ, 'CDP_PORT': '9222'})
            data = json.loads(result.stdout)
            if data.get('status') == 'collected':
                require(data.get('account') == request['account'] and data.get('plan_hash') == request['plan_hash'], 'collector_identity', 'Collector account or plan mismatch')
            return data
        except (OSError, ValueError, subprocess.TimeoutExpired):
            return {'status': 'blocked', 'reason': 'collector_result_unavailable'}

    def collect_export(self, directory, state, plan, purpose='verification'):
        minimum = plan['prepared_at'] if purpose == 'preflight' else state.get('execution_started_at', plan['prepared_at'])
        request = {'schema_version': 1, 'operation_id': plan['operation_id'], 'account': plan['account'], 'plan_hash': state['plan_hash'], 'minimum_after': minimum, 'output_dir': str(directory / f"backend-{purpose}-{state.get('execution_stage', 1)}")}
        response = self.run_collector(directory, 'catalog-export.mjs', request)
        state['last_collection'] = {k: v for k, v in response.items() if k not in {'account', 'plan_hash'}}
        if response.get('status') != 'collected':
            return None
        require(response.get('complete_report') is True and timestamp(response.get('report_generated_at')) >= timestamp(minimum), 'stale_report', 'Verification requires a complete freshly generated report')
        path = Path(response['path'])
        require(path.is_file() and file_hash(path) == response.get('sha256'), 'artifact_changed', 'Downloaded report checksum mismatch')
        response['rows'] = evidence_tools().report_rows(path)
        return response

    def collect_images(self, directory, state, plan):
        body = plan['body']
        mapping = body.get('sku_asins', {})
        if not all(image['sku'] in mapping for image in body['images']):
            return None
        targets = {}
        for image in body['images']:
            targets.setdefault(image['sku'], {'asin': mapping[image['sku']], 'slots': []})['slots'].append(image['slot'])
        response = self.run_collector(directory, 'image-evidence.mjs', {'schema_version': 1, 'operation_id': plan['operation_id'], 'account': plan['account'], 'plan_hash': state['plan_hash'], 'targets': targets}, timeout=300)
        if response.get('status') != 'collected':
            state['last_collection'] = response
            return None
        approved = {(image['sku'], image['slot']): image for image in body['images']}
        observed = []
        for image in response.get('images', []):
            source = approved.get((image['sku'], image['slot']))
            require(source is not None, 'scope_violation', 'Image collector returned an unrequested slot')
            try:
                content = evidence_tools().fetch_public_image(image['live_url'])
                match = evidence_tools().same_image_content(Path(source['path']).read_bytes(), content)
            except (OSError, ValueError):
                match = None
            observed.append({**image, 'source_sha256': source['sha256'], 'visually_verified': bool(match), 'content_match': match})
        return {'account': plan['account'], 'plan_hash': state['plan_hash'], 'source_id': 'amazon-live-imageblock', 'observed_at': now(), 'submission_id': state.get('submission_id'), 'processing_status': 'live_observed', 'images': observed}

    def collect(self, directory, state, plan):
        """Read-only live PDP collector using the established listing-capture runner.

        Public title/bullet/description fields can be verified here. Hidden fields
        and seller contributions require fresh export evidence; never substitute
        staged import values for live values.
        """
        if state['status'] in {'verified', 'failed'}:
            return None
        body = plan['body']
        driver_evidence = state.get('adapter_result', {}).get('evidence')
        if isinstance(driver_evidence, dict):
            return driver_evidence
        kind = operation_kind(plan['operation'])
        if kind == 'listing.images' and (state.get('submission_id') or body.get('no_changes')):
            return self.collect_images(directory, state, plan)
        if not state.get('submission_id'):
            return None
        if kind == 'catalog.change':
            exported = self.collect_export(directory, state, plan)
            if exported is None:
                return None
            return {'account': plan['account'], 'plan_hash': state['plan_hash'], 'source_id': exported['source_id'], 'observed_at': now(), 'submission_id': state['submission_id'], 'processing_status': 'live_observed', **evidence_tools().catalog_evidence(plan, state, exported['rows'])}
        if kind not in {'seo.update', 'flatfilepro.update'}:
            return None
        expected = body.get('expected_rows', {})
        hidden_fields = any(not re.fullmatch(r'item_name.0.value|itemName|bullet_point.[0-9]+.value|product_description.0.value', field) for row in expected.values() for field in row)
        if hidden_fields or not body.get('sku_asins'):
            exported = self.collect_export(directory, state, plan)
            if exported is None:
                return None
            rows = {sku: {field: value for field in fields if (value := evidence_tools().field_value(exported['rows'].get(sku, {}), field)) is not None} for sku, fields in expected.items()}
            return {'account': plan['account'], 'plan_hash': state['plan_hash'], 'source_id': exported['source_id'], 'observed_at': now(), 'submission_id': state['submission_id'], 'processing_status': 'live_observed', 'rows': rows}
        mapping = body.get('sku_asins', {})
        expected = body.get('expected_rows', {})
        if not expected or not set(expected) <= set(mapping):
            return None
        require(all(re.fullmatch(r'[A-Z0-9]{10}', mapping[sku]) for sku in expected), 'invalid_asin', 'Live collector requires valid ASINs')
        market = {'US': ('com', 'en_US'), 'DE': ('de', 'de_DE'), 'AU': ('com.au', 'en_AU'), 'UK': ('co.uk', 'en_GB'), 'IT': ('it', 'it_IT'), 'FR': ('fr', 'fr_FR'), 'ES': ('es', 'es_ES'), 'CA': ('ca', 'en_CA')}.get(plan['account']['marketplace'])
        if not market:
            return None
        output = directory / ('live-listings-' + str(len(state.get('events', []))) + '.json')
        try:
            result = subprocess.run(['node', str(ROOT / 'tools/listing-capture/capture-cdp.mjs'), ','.join(sorted(set(mapping[sku] for sku in expected))), str(output), *market], capture_output=True, text=True, timeout=300, check=False, env={**os.environ, 'CDP_PORT': '9222'})
            if result.returncode or not output.is_file():
                return None
            captured = json.loads(output.read_text())
            listings = {x['asin']: x for x in captured.get('listings', []) if x.get('status') == 'ok' and x.get('resolvedAsin') == x.get('asin')}
            rows = {}
            for sku, fields in expected.items():
                listing = listings.get(mapping[sku])
                if not listing:
                    continue
                rows[sku] = {}
                for field in fields:
                    if field in {'itemName', 'item_name.0.value'} and listing.get('title'):
                        rows[sku][field] = listing['title']
                    elif field == 'product_description.0.value' and listing.get('description'):
                        rows[sku][field] = listing['description']
                    elif re.fullmatch(r'bullet_point.[0-9]+.value', field):
                        index = int(field.split('.')[1])
                        if index < len(listing.get('bullets', [])):
                            rows[sku][field] = listing['bullets'][index]
            return {'account': plan['account'], 'plan_hash': state['plan_hash'], 'source_id': str(output), 'observed_at': now(), 'submission_id': state['submission_id'], 'processing_status': 'live_observed', 'rows': rows, 'collection': 'Live retail content; feed processing status is not inferred'}
        except (OSError, subprocess.TimeoutExpired, ValueError, KeyError):
            return None

    def reconcile(self, request):
        directory = self.directory(request.get('operation_id'))
        with self.lock(directory):
            state, plan = self.bound(directory, request)
            if state.get('phase') == 'preflight' and state.get('effects_started') is False:
                require(plan['body'].get('restore_missing_only'), 'invalid_preflight', 'Unexpected preflight state')
                fresh = self.collect_export(directory, state, plan, purpose='preflight')
                if fresh is None:
                    return self.persist(directory, state, 'processing', phase='preflight', effects_started=False, next_action='execute', reason='fresh_report_pending', retry_after_seconds=60)
                self.health_preflight(plan, fresh)
                changes = plan['body']['changes']
                if all(evidence_tools().field_value(fresh['rows'].get(c['sku'], {}), c['field']) == c['after'] for c in changes):
                    return self.verified_health_noop(directory, state, plan, fresh)
                receipt = {key: fresh[key] for key in ('path', 'sha256', 'report_generated_at', 'observed_at')}
                return self.persist(directory, state, 'partial', phase='preflight', effects_started=False, next_action='execute', reason='fresh_missing_fields_verified', preflight_receipt=receipt)
            evidence = request.get('evidence')
            if not evidence:
                evidence = self.collect(directory, state, plan)
                if evidence is None:
                    return self.persist(directory, state, state['status'], evidence_required=['Fresh operation-scoped Amazon processing result and final live state'], reason='verification_evidence_required')
            scoped(evidence, plan['account'], 'reconciliation evidence')
            require(evidence.get('plan_hash') == state['plan_hash'] and evidence.get('source_id'), 'evidence_mismatch', 'Evidence requires exact plan_hash and source_id')
            require(timestamp(evidence.get('observed_at')) >= timestamp(state.get('execution_started_at', plan['prepared_at'])), 'stale_evidence', 'Evidence predates this operation')
            require(timestamp(evidence['observed_at']) <= timestamp(now()) + dt.timedelta(minutes=5), 'invalid_time', 'Evidence cannot be future dated')
            if state.get('submission_id'):
                require(evidence.get('submission_id') == state['submission_id'], 'submission_mismatch', 'Evidence submission ID mismatch')
            op, body = operation_kind(plan['operation']), plan['body']
            require(body.get('status') not in {'awaiting_input'}, 'not_ready', 'Cannot reconcile an incomplete plan')
            if state['status'] == 'verified':
                return state
            require(evidence.get('submission_id') or body.get('no_changes'), 'missing_submission', 'Submission evidence requires its external ID')
            processing = evidence.get('processing_status')
            require(processing in {'processing', 'complete', 'failed', 'live_observed'}, 'invalid_processing', 'processing_status must be processing, complete, failed, or live_observed')
            evidence_path = directory / f'evidence-{digest(evidence)}.json'
            atomic_json(evidence_path, evidence)
            if processing == 'processing':
                return self.persist(directory, state, 'processing', submission_id=evidence['submission_id'], evidence_path=str(evidence_path))
            if processing == 'failed':
                return self.persist(directory, state, 'failed', submission_id=evidence['submission_id'], evidence_path=str(evidence_path), failures=evidence.get('errors', ['Submission failed']))
            matched, pending = [], []
            if op in {'seo.update', 'flatfilepro.update'}:
                observed = evidence.get('rows', {})
                for sku, row in body.get('expected_rows', {}).items():
                    for field, value in row.items():
                        (matched if sku in observed and field in observed[sku] and as_text(observed[sku][field]) == value else pending).append(f'{sku}/{field}')
            elif op == 'listing.images':
                observed = {(x.get('sku'), x.get('slot')): x for x in evidence.get('images', [])}
                for image in body['images']:
                    item = observed.get((image['sku'], image['slot']), {})
                    # Amazon may transform files: collector must explicitly establish visual identity.
                    ok = item.get('source_sha256') == image['sha256'] and item.get('visually_verified') is True and item.get('live_url', '').startswith('https://')
                    (matched if ok else pending).append(f"{image['sku']}/{image['slot']}")
            elif op == 'catalog.change':
                stage = evidence.get('stage')
                require(isinstance(stage, int) and 1 <= stage <= len(body['stages']), 'invalid_stage', 'Catalog evidence requires a valid stage')
                require(not state.get('execution_stage') or stage == state['execution_stage'], 'stage_mismatch', 'Evidence stage differs from current submission stage')
                previous = state.get('verified_stages', [])
                require(stage == 1 or stage - 1 in previous, 'stage_order', 'Verify the preceding stage before reconciling the next')
                for sku, fields in body['stages'][stage - 1].get('full_update_values', {}).items():
                    observed = evidence.get('catalog_rows', {}).get(sku, {})
                    for field, value in fields.items():
                        (matched if field in observed and as_text(observed[field]) == as_text(value) else pending).append(f'{sku}/{field}')
                manifest = body['manifest']
                family = manifest.get('family', {})
                offers = evidence.get('child_offers', {})
                for sku in body['protected_children']:
                    (matched if offers.get(sku) == 'preserved' else pending).append(f'{sku}/offer')
                if manifest['operation'] == 'create_products':
                    for product in body['products']:
                        live = evidence.get('products', {}).get(product['sku'], {})
                        ok = re.fullmatch(r'[A-Z0-9]{10}', str(live.get('asin', ''))) and live.get('product_type') == product['product_type'] and live.get('title') == product['title'] and live.get('parent_sku') in {'', None}
                        (matched if ok else pending).append(product['sku'])
                    status = 'verified' if matched and not pending and not evidence.get('errors') else ('partial' if matched else ('processing' if processing == 'live_observed' else 'failed'))
                    return self.persist(directory, state, status, matched=matched, pending=pending, evidence_path=str(evidence_path))
                parent = family['parent']['sku']
                deletion = len(body['stages']) > 1 and stage == 1 or manifest['operation'] == 'delete_parent'
                if deletion:
                    delete_sku = family.get('old_parent_sku') or parent
                    (matched if evidence.get('deleted_parents') == [delete_sku] else pending).append(f'{delete_sku}/deleted')
                    for sku in body['protected_children']:
                        (matched if evidence.get('relationships', {}).get(sku) == '' else pending).append(f'{sku}/detached')
                else:
                    for child in family.get('children', []):
                        sku = child['sku']
                        (matched if evidence.get('relationships', {}).get(sku) == parent else pending).append(f'{sku}/parent')
                if not pending and not evidence.get('errors'):
                    previous = sorted(set(previous + [stage]))
                    state['verified_stages'] = previous
                    if stage < len(body['stages']):
                        return self.persist(directory, state, 'partial', next_stage=stage + 1, evidence_path=str(evidence_path), message='Stage verified; next upload remains unsubmitted')
            elif op == 'shipment.create':
                expected = body['shipment']
                require(evidence.get('shipment_reference') == expected['shipment_reference'], 'shipment_mismatch', 'Shipment reference mismatch')
                require(evidence.get('carrier') == expected['carrier'] and evidence.get('currency') == expected['currency'], 'shipment_mismatch', 'Shipment carrier/currency mismatch')
                actual_cost = evidence.get('actual_cost')
                require(isinstance(actual_cost, (int, float)) and not isinstance(actual_cost, bool) and math.isfinite(actual_cost) and 0 <= actual_cost <= body['limits']['max_cost'], 'cost_limit', 'Actual shipment cost exceeds saved limit or is invalid')
                expected_qty = {x['sku']: x['quantity'] for x in expected['lines']}
                require(evidence.get('quantities') == expected_qty, 'shipment_mismatch', 'Confirmed quantities differ from shipment request')
                labels = evidence.get('labels', [])
                expected_boxes = {x['id'] for x in expected['cartons']}
                require(len(labels) == len(expected_boxes) and {x.get('carton_id') for x in labels} == expected_boxes, 'label_coverage', 'Every carton requires exactly one label record')
                shipment_ids = evidence.get('submission_ids', [evidence['submission_id']])
                require(isinstance(shipment_ids, list) and shipment_ids and len(set(shipment_ids)) == len(shipment_ids), 'invalid_label', 'Shipment IDs must be a unique nonempty list')
                verification_input = directory / 'label-verification-input.json'
                outputs = list({(x.get('path'), x.get('shipment_id')): {key: x.get(key) for key in ('path', 'sha256', 'shipment_id')} for x in labels}.values())
                atomic_json(verification_input, {'outputs': outputs, 'cartons': expected['cartons']})
                checked = subprocess.run(['node', str(ROOT / 'tools/amazon-operations/verify-shipment-labels.mjs'), '--request', str(verification_input)], capture_output=True, text=True, timeout=60, check=False)
                checked_result = json.loads(checked.stdout)
                require(checked.returncode == 0 and checked_result.get('status') == 'verified', 'invalid_label', 'Independent PDF content/page/thermal-size verification failed')
                checked_labels = {x['carton_id']: x for x in checked_result['labels']}
                require(set(checked_labels) == expected_boxes, 'label_coverage', 'Independent PDF carton coverage differs')
                for label in labels:
                    require(all(checked_labels[label['carton_id']].get(key) == label.get(key) for key in ('path', 'sha256', 'shipment_id')), 'invalid_label', 'Declared label identity differs from parsed PDF content')
                    path = Path(label.get('path', ''))
                    require(path.is_file() and file_hash(path) == label.get('sha256'), 'invalid_label', 'Label file checksum mismatch')
                    with path.open('rb') as stream:
                        require(stream.read(5) == b'%PDF-', 'invalid_label', 'Shipment labels must be PDF files')
                    require(label.get('shipment_id') in shipment_ids, 'invalid_label', 'Label shipment identity mismatch')
                    matched.append(label['carton_id'])
            errors = evidence.get('errors', [])
            status = 'verified' if matched and not pending and not errors else ('partial' if matched else ('processing' if processing == 'live_observed' else 'failed'))
            return self.persist(directory, state, status, submission_id=evidence.get('submission_id'), matched=matched, pending=pending, failures=errors, evidence_path=str(evidence_path))


def capabilities():
    return {'schema_version': 1, 'operations': {name: {'prepare': True, 'reconcile': True, 'execute_adapter': {'seo.update':'flatfilepro.cdp','flatfilepro.update':'flatfilepro.cdp','catalog.change':'catalog.cdp','shipment.create':'shipment.cdp','listing.images':'flatfilepro.cdp'}.get(operation_kind(name)), 'production_ready': False, 'requires_live_canary': True, 'limitation': 'Live selector contracts require scoped canary' if operation_kind(name) in {'seo.update', 'flatfilepro.update', 'catalog.change', 'shipment.create', 'listing.images'} else 'No observed submission adapter installed'} for name in sorted(OPERATIONS)}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['capabilities', 'prepare', 'execute', 'advance', 'reconcile', 'status'])
    parser.add_argument('--request', type=Path)
    parser.add_argument('--state-dir', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == 'capabilities':
            result = capabilities()
        else:
            require(args.request is not None and args.state_dir is not None, 'missing_argument', '--request and --state-dir are required')
            request = json.loads(args.request.read_text())
            service = Operations(args.state_dir)
            command = 'execute' if args.command == 'advance' else args.command
            result = service.view(service.directory(request.get('operation_id'))) if command == 'status' else getattr(service, command)(request)
        print(json.dumps(result, ensure_ascii=False, allow_nan=False))
        return 0
    except (OperationError, OSError, ValueError, KeyError, TypeError, ImportError, SystemExit) as exc:
        print(json.dumps({'schema_version': 1, 'status': 'blocked', 'reason': getattr(exc, 'code', 'invalid_input'), 'message': str(exc)}))
        return 2


if __name__ == '__main__':
    sys.exit(main())
