"""Read-only evidence parsing and public approved-image content verification."""
from __future__ import annotations
import csv
import hashlib
import http.client
import io
import ipaddress
import json
from pathlib import Path
import re
import socket
import ssl
from urllib.parse import urljoin, urlsplit

MAX_IMAGE_BYTES = 25 * 1024 * 1024


def public_https_target(url):
    parsed = urlsplit(url)
    if parsed.scheme != 'https' or not parsed.hostname or parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ValueError('Image URLs require public HTTPS on port 443 without credentials')
    host = parsed.hostname.encode('idna').decode('ascii')
    addresses = sorted({item[4][0] for item in socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)})
    if not addresses or any(not ipaddress.ip_address(ip).is_global for ip in addresses):
        raise ValueError('Image host must resolve exclusively to public IP addresses')
    return parsed, host, addresses[0]


def fetch_public_image(url):
    """Pin each connection to a checked public IP; validate SNI using original host."""
    for _ in range(4):
        parsed, host, ip = public_https_target(url)
        connection = http.client.HTTPSConnection(host, port=443, timeout=30, context=ssl.create_default_context())
        connection._create_connection = lambda address, timeout=30, source_address=None, **kw: socket.create_connection((ip, 443), timeout, source_address)
        try:
            connection.request('GET', parsed.path + ('?' + parsed.query if parsed.query else ''), headers={'Accept': 'image/png,image/jpeg', 'User-Agent': 'AmazonAgent-AssetVerifier/1'})
            response = connection.getresponse()
            if response.status in {301, 302, 303, 307, 308}:
                destination = response.getheader('Location')
                if not destination:
                    raise ValueError('Image redirect has no destination')
                url = urljoin(url, destination)
                continue
            if response.status != 200:
                raise ValueError(f'Image download returned HTTP {response.status}')
            length = response.getheader('Content-Length')
            if length and int(length) > MAX_IMAGE_BYTES:
                raise ValueError('Image exceeds 25 MB')
            data = response.read(MAX_IMAGE_BYTES + 1)
            if len(data) > MAX_IMAGE_BYTES:
                raise ValueError('Image exceeds 25 MB')
            from PIL import Image
            with Image.open(io.BytesIO(data)) as image:
                if image.format not in {'PNG', 'JPEG'}:
                    raise ValueError('Hosted asset must be JPEG or PNG')
                image.verify()
            return data
        finally:
            connection.close()
    raise ValueError('Too many image redirects')


def same_image_content(approved, observed):
    if hashlib.sha256(approved).digest() == hashlib.sha256(observed).digest():
        return 'sha256'
    from PIL import Image, ImageOps
    with Image.open(io.BytesIO(approved)) as left, Image.open(io.BytesIO(observed)) as right:
        left, right = ImageOps.exif_transpose(left).convert('RGBA'), ImageOps.exif_transpose(right).convert('RGBA')
        if left.size == right.size and left.tobytes() == right.tobytes():
            return 'identical_decoded_pixels'
    return None


def canonical_header(value):
    value = str(value or '').strip()
    value = re.sub(r'__(\d+)__', lambda m: f'.{int(m[1])-1}.', value)
    value = re.sub(r'#(\d+)', lambda m: f'.{int(m[1])-1}', value)
    aliases = {
        'Parent SKU': 'child_parent_sku_relationship.0.parent_sku', 'ASIN': 'asin',
        'item_sku': 'sku', 'contribution_sku.0.value': 'sku', 'seller-sku': 'sku', 'seller_sku': 'sku',
        'item_name': 'item_name.0.value', 'itemName': 'item_name.0.value',
        'product_description': 'product_description.0.value', 'generic_keywords': 'generic_keyword.0.value',
        'brand_name': 'brand.0.value', 'main_image_url': 'main_product_image_locator.0.media_location',
        'parent_sku': 'child_parent_sku_relationship.0.parent_sku',
        'parent_child': 'parentage_level.0.value', 'parentage': 'parentage_level.0.value',
        'variation_theme': 'variation_theme.0.name', 'condition_type': 'condition_type.0.value',
    }
    if re.fullmatch(r'bullet_point[1-5]', value):
        return f'bullet_point.{int(value[-1])-1}.value'
    if re.fullmatch(r'other_image_url[1-9]', value):
        return f'other_product_image_locator_{value[-1]}.0.media_location'
    if value.strip().lower() == 'sku':
        return 'sku'
    return aliases.get(value, value)


def report_rows(path):
    path = Path(path)
    datasets = []
    if path.read_bytes()[:2] == b'PK':
        import openpyxl
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=False)
        try:
            datasets = [list(sheet.iter_rows(values_only=True)) for sheet in workbook.worksheets]
        finally:
            workbook.close()
    else:
        raw = path.read_text(encoding='utf-8-sig')
        delimiter = '\t' if '\t' in raw.splitlines()[0] else ','
        datasets = [list(csv.reader(io.StringIO(raw), delimiter=delimiter))]
    result = {}
    for rows in datasets:
        for index, row in enumerate(rows[:25]):
            headers = [canonical_header(x) for x in row]
            if 'sku' not in headers:
                continue
            keys = [h for h in headers if h]
            if len(keys) != len(set(keys)):
                raise ValueError('Ambiguous duplicate report headers')
            sku_index = headers.index('sku')
            # Modern reports include preferences/examples above their declared dataRow.
            settings = str(rows[0][0] or '') if rows and rows[0] else ''
            match = re.search(r'dataRow[=:](\d+)', settings)
            start = int(match[1]) - 1 if match else index + 1
            for values in rows[start:]:
                if sku_index >= len(values) or values[sku_index] in (None, ''):
                    continue
                sku = str(values[sku_index])
                if sku in result:
                    raise ValueError('Duplicate SKU across Category Listings Report rows')
                result[sku] = {key: '' if i >= len(values) or values[i] is None else str(values[i]) for i, key in enumerate(headers) if key}
            break
    if not result:
        raise ValueError('Fresh report contains no unambiguous SKU rows')
    return result


LOGICAL_FIELDS = {
    'product_type': ['product_type'], 'title': ['item_name.0.value'],
    'parentage': ['parentage_level.0.value'], 'parent_sku': ['child_parent_sku_relationship.0.parent_sku'],
    'variation_theme': ['variation_theme.0.name'], 'external_product_id': ['externally_assigned_product_identifier.0.value'],
    'external_product_id_type': ['externally_assigned_product_identifier.0.type'],
    'price': ['purchasable_offer.0.our_price.0.schedule.0.value_with_tax', 'standard_price'],
    'quantity': ['fulfillment_availability.0.quantity', 'quantity'],
    'fulfillment_channel': ['fulfillment_availability.0.fulfillment_channel_code', 'fulfillment_channel'],
    'condition': ['condition_type.0.value'],
    'lead_time': ['fulfillment_availability.0.lead_time_to_ship_max_days', 'fulfillment_latency'],
}


def field_value(row, field):
    keys = LOGICAL_FIELDS.get(field, [canonical_header(field)])
    present = [row[k] for k in keys if k in row]
    return present[0] if present and len(set(present)) == 1 else None


def catalog_evidence(plan, state, rows):
    body = plan['body']
    stage_index = state.get('execution_stage', 1)
    stage = body['stages'][stage_index-1]
    manifest = body['manifest']
    result = {'stage': stage_index, 'catalog_rows': {}, 'relationships': {}, 'child_offers': {}}
    for sku, expected in stage.get('full_update_values', {}).items():
        row = rows.get(sku, {})
        result['catalog_rows'][sku] = {field: value for field in expected if (value := field_value(row, field)) is not None}
    for sku in body.get('protected_children', []):
        row = rows.get(sku)
        if row is None:
            continue
        parent = field_value(row, 'parent_sku')
        if parent is not None:
            result['relationships'][sku] = parent
        baseline = body.get('protected_offer_values', {}).get(sku)
        # Mere row existence cannot establish an unchanged offer.
        if baseline and all(field_value(row, field) == value for field, value in baseline.items()):
            result['child_offers'][sku] = 'preserved'
    if manifest['operation'] == 'create_products':
        result['products'] = {}
        for product in body['products']:
            row = rows.get(product['sku'], {})
            result['products'][product['sku']] = {
                'asin': row.get('asin') or row.get('ASIN'), 'title': field_value(row, 'title'),
                'product_type': field_value(row, 'product_type'), 'parent_sku': field_value(row, 'parent_sku')}
    else:
        family = manifest['family']
        deletion = len(body['stages']) > 1 and stage_index == 1 or manifest['operation'] == 'delete_parent'
        if deletion:
            parent = family.get('old_parent_sku') or family['parent']['sku']
            result['deleted_parents'] = [parent] if parent not in rows else []
        for child in family.get('children', []):
            if child['sku'] in rows:
                parent = field_value(rows[child['sku']], 'parent_sku')
                if parent is not None:
                    result['relationships'][child['sku']] = parent
    return result
