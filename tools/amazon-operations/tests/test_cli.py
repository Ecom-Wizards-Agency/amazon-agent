"""Real subprocess protocol smoke tests. No browser execution or network calls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone

CLI=Path(__file__).resolve().parents[1]/'operations.py'

def stamp():return datetime.now(timezone.utc).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

class CliTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.account={'client_slug':'synthetic','profile_key':'synthetic-us','marketplace':'US','seller_id':'SELLER','marketplace_id':'MARKET','seller_central_name':'Synthetic Seller','marketplace_label':'United States','flatfilepro_display_name':'Synthetic - US','context_binding':{'seller_id':'SELLER','marketplace_id':'MARKET','unique_label_mapping':True}}
    def call(self,command,request):
        path=self.root/f'{command}-request.json';path.write_text(json.dumps(request))
        result=subprocess.run([sys.executable,str(CLI),command,'--request',str(path),'--state-dir',str(self.root/'state')],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertEqual(len(result.stdout.strip().splitlines()),1)
        return json.loads(result.stdout)
    def check_plan(self,result):
        self.assertEqual(result['account'],self.account)
        plan=json.loads(Path(result['plan_path']).read_text())
        serialized=json.dumps(plan,sort_keys=True,separators=(',', ':'),ensure_ascii=False,allow_nan=False).encode()
        self.assertEqual(result['plan_hash'],hashlib.sha256(serialized).hexdigest())
        self.assertEqual(plan['account'],self.account)
        return plan
    def test_public_seo_alias_prepare_and_external_evidence_reconcile(self):
        source=self.root/'source.csv';source.write_text('sku,item_name.0.value\nEXAMPLE,Old title\n')
        request={'schema_version':1,'operation_id':'cli-seo-r1','operation':'seo.apply','account':self.account,'targets':[{'sku':'EXAMPLE','asin':'B000000001'}],'inputs':{'scope_fields':['item_name.0.value'],'source_export':{'path':str(source),'sha256':sha(source)},'live':{'account':self.account,'observed_at':stamp(),'rows':{'EXAMPLE':{'item_name.0.value':'Old title'}}},'approved_seo':{'account':self.account,'approved':True,'approved_by':'synthetic-reviewer','approved_at':stamp(),'source_id':'synthetic-seo-revision','rows':{'EXAMPLE':{'item_name.0.value':'Approved title'}}}}}
        prepared=self.call('prepare',request);plan=self.check_plan(prepared)
        self.assertEqual(prepared['operation'],'seo.apply');self.assertEqual(prepared['targets'],['EXAMPLE']);self.assertEqual(plan['body']['sku_asins'],{'EXAMPLE':'B000000001'})
        evidence={'account':self.account,'plan_hash':prepared['plan_hash'],'source_id':'synthetic-live-export','observed_at':stamp(),'submission_id':'synthetic-submission','processing_status':'complete','rows':{'EXAMPLE':{'item_name.0.value':'Approved title'}}}
        reconciled=self.call('reconcile',{'schema_version':1,'operation_id':'cli-seo-r1','plan_hash':prepared['plan_hash'],'evidence':evidence})
        self.assertEqual(reconciled['status'],'verified');self.assertTrue(reconciled['verified'])
        saved=json.loads(Path(reconciled['evidence_path']).read_text());self.assertEqual(saved,evidence)
        self.assertEqual(Path(reconciled['evidence_path']).parent,Path(prepared['plan_path']).parent)
    def test_shipment_cli_label_evidence_paths_are_exact(self):
        request={'schema_version':1,'operation_id':'cli-shipment-r1','operation':'shipment.create','account':self.account,'targets':['EXAMPLE'],'inputs':{'shipment_reference':'synthetic-order-1','ship_from':{'address_line1':'1 Example','city':'Example','postal_code':'12345','country':'US'},'lines':[{'sku':'EXAMPLE','quantity':4}],'cartons':[{'id':'box-1','weight':2,'weight_unit':'kg','dimensions':[10,20,30],'dimension_unit':'cm','contents':{'EXAMPLE':4}}],'carrier':'Example Carrier','currency':'USD','estimated_cost':10,'ship_date':'2026-09-08','ship_mode':'SPD','carrier_mode':'non_partnered','packing_templates':{'EXAMPLE':{'name':'Saved box','units_per_box':4}},'label_format':'thermal_4x6','client_limits':{'account':self.account,'max_units':10,'max_cost':20,'currency':'USD','carriers':['Example Carrier']},'existing_shipments':{'account':self.account,'observed_at':stamp(),'shipments':[]}}}
        prepared=self.call('prepare',request);self.check_plan(prepared)
        label=Path(prepared['plan_path']).parent/'synthetic-label.pdf'
        # Valid one-page thermal PDF with parseable Amazon carton/SKU/quantity text.
        stream=b'BT /F1 12 Tf 20 380 Td (FBAEXAMPLEU000001) Tj 0 -20 Td (Single SKU EXAMPLE) Tj 0 -20 Td (Qty 4) Tj ET'
        objects=[b'<</Type/Catalog/Pages 2 0 R>>',b'<</Type/Pages/Count 1/Kids[3 0 R]>>',b'<</Type/Page/Parent 2 0 R/MediaBox[0 0 288 432]/Resources<</Font<</F1 4 0 R>>>>/Contents 5 0 R>>',b'<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>',b'<</Length '+str(len(stream)).encode()+b'>>\nstream\n'+stream+b'\nendstream']
        content=b'%PDF-1.4\n';offsets=[]
        for index,obj in enumerate(objects,1):offsets.append(len(content));content+=str(index).encode()+b' 0 obj\n'+obj+b'\nendobj\n'
        xref=len(content);content+=b'xref\n0 6\n0000000000 65535 f \n'+b''.join(f'{offset:010} 00000 n \n'.encode() for offset in offsets)+b'trailer<</Size 6/Root 1 0 R>>\nstartxref\n'+str(xref).encode()+b'\n%%EOF\n';label.write_bytes(content)
        evidence={'account':self.account,'plan_hash':prepared['plan_hash'],'source_id':'synthetic-sta-label-readback','observed_at':stamp(),'submission_id':'synthetic-workflow','submission_ids':['FBAEXAMPLE'],'processing_status':'complete','shipment_reference':'synthetic-order-1','carrier':'Example Carrier','currency':'USD','actual_cost':10,'quantities':{'EXAMPLE':4},'labels':[{'carton_id':'box-1','path':str(label),'sha256':sha(label),'shipment_id':'FBAEXAMPLE'}]}
        result=self.call('reconcile',{'schema_version':1,'operation_id':'cli-shipment-r1','plan_hash':prepared['plan_hash'],'evidence':evidence})
        self.assertEqual(result['status'],'verified');self.assertEqual(result['matched'],['box-1'])
        saved=json.loads(Path(result['evidence_path']).read_text())
        self.assertEqual(saved['labels'][0]['path'],str(label));self.assertEqual(saved['labels'][0]['sha256'],sha(label))
        self.assertEqual(Path(result['evidence_path']).parent,Path(prepared['plan_path']).parent)

if __name__=='__main__':unittest.main()
