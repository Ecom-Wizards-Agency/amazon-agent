import importlib.util
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('evidence',Path(__file__).resolve().parents[1]/'evidence.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)

class EvidenceTests(unittest.TestCase):
    def test_private_and_mixed_resolution_are_rejected(self):
        for addresses in [['127.0.0.1'],['10.0.0.1'],['8.8.8.8','127.0.0.1']]:
            with patch.object(e.socket,'getaddrinfo',return_value=[(2,1,6,'',(ip,443)) for ip in addresses]):
                with self.assertRaises(ValueError):e.public_https_target('https://example.com/image.png')
    def test_non_https_credentials_and_custom_ports_rejected(self):
        for url in ['http://example.com/a','https://user:password@example.com/a','https://example.com:444/a']:
            with self.assertRaises(ValueError):e.public_https_target(url)
    def test_image_content_requires_exact_pixels_or_bytes(self):
        from PIL import Image
        def png(color,compress):
            out=io.BytesIO();Image.new('RGB',(500,500),color).save(out,format='PNG',compress_level=compress);return out.getvalue()
        first=png('white',1);second=png('white',9);different=png('black',1)
        self.assertEqual(e.same_image_content(first,first),'sha256')
        self.assertEqual(e.same_image_content(first,second),'identical_decoded_pixels')
        self.assertIsNone(e.same_image_content(first,different))
    def test_report_maps_exact_backend_headers_and_rejects_duplicates(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'report.tsv';path.write_text('sku\tgeneric_keywords\tparent_sku\na\tbackend phrase\tPARENT\n')
            rows=e.report_rows(path);self.assertEqual(rows['a']['generic_keyword.0.value'],'backend phrase');self.assertEqual(e.field_value(rows['a'],'parent_sku'),'PARENT')
            path.write_text('sku\titem_name\na\tOne\na\tTwo\n')
            with self.assertRaises(ValueError):e.report_rows(path)
    def test_catalog_offer_preservation_needs_values_not_row_existence(self):
        plan={'body':{'stages':[{'full_update_values':{}}],'manifest':{'operation':'delete_parent','family':{'parent':{'sku':'parent'},'children':[]}},'protected_children':['child'],'protected_offer_values':{'child':{'price':'10','quantity':'5'}}}}
        partial=e.catalog_evidence(plan,{}, {'child':{'sku':'child','standard_price':'10','quantity':'4','child_parent_sku_relationship.0.parent_sku':''}})
        self.assertEqual(partial['deleted_parents'],['parent']);self.assertEqual(partial['child_offers'],{})
        preserved=e.catalog_evidence(plan,{}, {'child':{'sku':'child','standard_price':'10','quantity':'5','child_parent_sku_relationship.0.parent_sku':''}})
        self.assertEqual(preserved['child_offers'],{'child':'preserved'})

if __name__=='__main__':unittest.main()
