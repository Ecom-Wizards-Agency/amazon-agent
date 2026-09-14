import importlib.util,json,tempfile,unittest
from pathlib import Path
from openpyxl import Workbook
spec=importlib.util.spec_from_file_location('builder',Path(__file__).resolve().parents[1] / 'build_keyword_workbook.py');b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class RankingContextTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.p=Path(self.tmp.name);(self.p/'catalog.json').write_text('{}');self.ev=self.p/'evidence.json'
  self.cfg={'product_anchor':{'asin':'','marketplace':'US','client':'Example'},'ranking_context':{'mode':'unavailable','reason':'No published ASIN','evidence_file':str(self.ev)},'triage':{'brand_tokens':[],'form_tokens':[],'claim_tokens':[],'negative_tokens':[],'match':'word','categories_order':[],'semantic_opportunity':{'min_relevancy':.3,'min_search_volume':1,'include_if_anchor_not_ranking':False}},'final_action':{'by_classification':{},'allowed':['Ignore']}}
  self.evidence={'asin':'','marketplace':'US','status':'prelaunch','verified_at':'2026-09-09','evidence_files':[str(self.p/'catalog.json')]};self.ev.write_text(json.dumps(self.evidence))
 def tearDown(self):self.tmp.cleanup()
 def test_default_still_requires_real_tracked_anchor(self):
  c={'product_anchor':{'asin':'B012345678'}};self.assertFalse(b.ranking_context_status(c,[])['valid']);self.assertTrue(b.ranking_context_status(c,['B012345678'])['valid'])
 def test_prelaunch_requires_matching_readable_evidence(self):
  self.assertTrue(b.ranking_context_status(self.cfg,['B087654321'])['valid']);self.evidence['marketplace']='DE';self.ev.write_text(json.dumps(self.evidence));self.assertFalse(b.ranking_context_status(self.cfg,[])['valid'])
 def test_synthetic_anchor_column_rejected(self):
  self.cfg['product_anchor']['asin']='B012345678';self.evidence.update(asin='B012345678',status='inactive-untracked');self.ev.write_text(json.dumps(self.evidence));self.assertTrue(b.ranking_context_status(self.cfg,[])['valid']);self.assertFalse(b.ranking_context_status(self.cfg,['B012345678'])['valid'])
 def test_unavailable_cannot_enable_missing_rank_opportunities(self):
  self.cfg['triage']['semantic_opportunity']['include_if_anchor_not_ranking']=True;self.assertFalse(b.ranking_context_status(self.cfg,[])['valid'])
 def test_unknown_mode_fails(self):
  self.cfg['ranking_context']['mode']='skip';self.assertFalse(b.ranking_context_status(self.cfg,[])['valid'])
 def test_missing_ranks_never_become_opportunities(self):
  self.cfg['triage']['semantic_opportunity']['include_if_anchor_not_ranking']=True
  self.cfg['triage']['claim_tokens']=['anemia'];self.cfg['final_action']['by_classification']={'Unsupported claim/health-risk':'Ignore'}
  ws=Workbook().active
  b.build_outlier(ws,[['Search Terms','SV','Relev.','B087654321'],['iron',1000,1,1],['anemia',500,1,2]],[['Search Terms','SV','Relev.','B087654321'],['ferritin',100,.6,3]],set(),self.cfg,{},[])
  rows=list(ws.values);self.assertEqual(len(rows),2);self.assertEqual(rows[1][0],'anemia');self.assertEqual(rows[1][3],'Not available');self.assertNotEqual(rows[1][7],'Semantic opportunity')
if __name__=='__main__':unittest.main()
