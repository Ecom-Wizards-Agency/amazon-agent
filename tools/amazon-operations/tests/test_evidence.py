import importlib.util
import copy
import hashlib
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
    def test_review_receipt_binds_source_rendition_account_and_slot(self):
        from PIL import Image, ImageDraw
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)/'source.png'; live=Path(directory)/'live.jpg'
            picture=Image.new('RGB',(500,500),'white');ImageDraw.Draw(picture).text((50,50),'Dose 25 mg',fill='black')
            picture.save(source);picture.save(live,quality=75)
            image={'sku':'a','slot':'PT01','path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
            plan={'account':{'seller_id':'A','marketplace':'US'},'operation_id':'op','body':{'images':[image],'sku_asins':{'a':'B000000001'}}}
            review={'sku':'a','slot':'PT01','asin':'B000000001','source_sha256':image['sha256'],
                    'observed_path':str(live),'observed_sha256':hashlib.sha256(live.read_bytes()).hexdigest(),
                    'source_id':'https://www.amazon.com/dp/B000000001','decision':'match'}
            receipt=e.build_image_review(plan,[review],{'kind':'attended_agent','id':'test','context':'test-review'},'2026-09-15T00:00:00Z')
            original,observed=source.read_bytes(),live.read_bytes()
            self.assertIsNone(e.same_image_content(original,observed))
            self.assertIsNone(e.verify_public_rendition(plan,image,original,observed)['content_match'])
            self.assertEqual(e.verify_public_rendition(plan,image,original,observed,[receipt])['content_match'],'attended_visual_review')
            for mutated in [dict(plan,operation_id='another'),dict(plan,account={'seller_id':'B','marketplace':'US'})]:
                self.assertIsNone(e.verify_public_rendition(mutated,image,original,observed,[receipt])['content_match'])
            wrong_slot=dict(image,slot='PT02')
            self.assertIsNone(e.verify_public_rendition(plan,wrong_slot,original,observed,[receipt])['content_match'])
            corrupt=copy.deepcopy(receipt);corrupt['pairs'][0]['slot']='PT02'
            with self.assertRaisesRegex(ValueError,'checksum'):
                e.verify_public_rendition(plan,image,original,observed,[corrupt])
            for variant in ('tiny_text','crop','color'):
                altered=Image.open(live).copy()
                if variant=='tiny_text':ImageDraw.Draw(altered).text((50,50),'26',fill='red')
                elif variant=='crop':altered=altered.crop((1,0,500,500))
                else:altered.putpixel((400,400),(0,255,0))
                out=io.BytesIO();altered.save(out,format='PNG')
                self.assertIsNone(e.verify_public_rendition(plan,image,original,out.getvalue(),[receipt])['content_match'])
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
