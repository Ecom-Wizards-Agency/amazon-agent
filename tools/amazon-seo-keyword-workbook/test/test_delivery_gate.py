import importlib.util,io,json,tempfile,unittest
from contextlib import redirect_stderr,redirect_stdout
from pathlib import Path
from unittest import mock
spec=importlib.util.spec_from_file_location('builder',Path(__file__).resolve().parents[1] / 'build_keyword_workbook.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
FAIL=[{'check':'row counts','pass':False,'detail':''}]
class DeliveryGateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name)
  self.args=dict(b.DEFAULTS,out=str(self.p/'wb.xlsx'),manifest=str(self.p/'wb_summary.json'))
 def tearDown(self):self.tmp.cleanup()
 def run_delivery(self,all_pass=True,checks=()):
  d=b.delivery_decision(self.args,all_pass);manifest={'outputs':{},'validations_all_pass':all_pass};warnings=[];out=io.StringIO()
  with mock.patch.object(b.subprocess,'run',return_value=b.subprocess.CompletedProcess([],1,'','')) as run,redirect_stdout(out),redirect_stderr(io.StringIO()):b.run_drive_delivery(d,self.args,manifest,list(checks),warnings)
  return d,run,out.getvalue(),warnings
 def test_target_without_deliver_makes_no_drive_call(self):
  self.args.update(drive_sheet_id='1AbC',artifact_run='run_1')
  d,run,out,_=self.run_delivery()
  self.assertEqual((d['action'],d['status'],d['mode']),('skip','not_requested','in-place update'));run.assert_not_called()
  self.assertIn('rerun with --deliver 1',out);self.assertIn('--dry-run',out);self.assertIn('Artifact run run_1 stays open',out)
 def test_config_cannot_enable_delivery(self):
  warnings=[];b.apply_config_inputs(self.args,{'inputs':{'deliver':'1','drive_folder':'1FolderId'}},set(),warnings)
  self.assertEqual(self.args['deliver'],'');self.assertEqual(self.args['drive_folder'],'1FolderId')
  self.assertTrue(any('inputs.deliver ignored' in w for w in warnings))
  d,run,_,_=self.run_delivery();self.assertEqual((d['action'],d['status']),('skip','not_requested'));run.assert_not_called()
 def test_no_deliver_wins_over_deliver(self):
  self.args.update(drive_folder='1FolderId',deliver='1',no_deliver='1')
  d,run,_,_=self.run_delivery();self.assertEqual((d['action'],d['status']),('skip','skipped_no_deliver'));run.assert_not_called()
 def test_failed_validation_is_never_delivered(self):
  self.args.update(drive_folder='1FolderId',deliver='1')
  d,run,out,warnings=self.run_delivery(all_pass=False,checks=FAIL)
  self.assertEqual((d['action'],d['status']),('skip','skipped_validation_fail'));run.assert_not_called()
  self.assertIn('skipped because the build has FAIL checks',out);self.assertTrue(any('validation FAIL' in w for w in warnings))
 def test_confirmed_passing_build_delivers(self):
  self.args.update(drive_folder='1FolderId',deliver='1')
  d,run,_,_=self.run_delivery();self.assertEqual((d['action'],d['mode'],d['target']),('deliver','delivery','1FolderId'))
  cmd=run.call_args.args[0];self.assertTrue(cmd[1].endswith('deliver.py'));self.assertEqual(cmd[3],'1FolderId')
 def test_deliver_zero_is_not_a_confirmation(self):
  self.args.update(drive_folder='1FolderId',deliver='0');self.assertEqual(b.delivery_decision(self.args,True)['status'],'not_requested')
 def test_template_placeholders_read_as_unset(self):
  tpl=json.loads((Path(b.__file__).parent/'config.TEMPLATE.json').read_text(encoding='utf-8'))['inputs']
  b.apply_config_inputs(self.args,{'inputs':{'drive_folder':tpl['drive_folder'],'drive_sheet_id':tpl['drive_sheet_id']}},set(),[])
  self.args['deliver']='1';self.assertEqual((self.args['drive_folder'],self.args['drive_sheet_id']),('',''))
  self.assertEqual(b.delivery_decision(self.args,True)['action'],'none')
if __name__=='__main__':unittest.main()
