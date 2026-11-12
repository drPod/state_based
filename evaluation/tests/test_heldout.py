import json,sys,unittest,tempfile
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'code'))
import evaluate as ev
import heldout_examples as held
from heldout_examples import RUN,retrieve,EXCLUDED
class HeldoutProtocol(unittest.TestCase):
 def test_default_runner_pauses_before_any_compact_request(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);private=root/'private';private.mkdir()
   manifest={'cells':[{'id':'v3','variant':'handbook-v3'},{'id':'compact','variant':'compact-v1'}]}
   class FakeMatrix:
    def __init__(self,*args,**kwargs):self.state={'attempts':[]}
    def process(self,cell):
     path=private/'responses'/(cell['id']+'.json')
     if path.exists():return
     path.parent.mkdir(exist_ok=True);path.write_text('{}')
     self.state['attempts'].append({'cell_id':cell['id']})
    def spend(self,*args):return 0
    def run(self,*args):raise AssertionError('Unconditional full-matrix runner is forbidden')
   def fake_load(path):return manifest if Path(path).name=='manifest.json' else {}
   with patch.object(held,'RUN',root),patch.object(held.ev,'load',side_effect=fake_load),patch.object(held,'Matrix',FakeMatrix):held.run()
   self.assertTrue((private/'responses/v3.json').exists())
   self.assertFalse((private/'responses/compact.json').exists())
   result=json.loads((private/'v3-only-run-status.json').read_text())
   self.assertTrue(result['compact_deferred']);self.assertEqual(result['compact_paid_attempts'],0)
 def test_public_artifacts_reproduce_selection_without_private_sources(self):
  pool=ev.load(RUN/'demonstration-pool.json');targets=ev.load(RUN/'retrieval-targets.json');expected={x['task_id']:x['demonstration_ids'] for x in ev.load(RUN/'demonstration-selection.json')['selection']}
  self.assertEqual(len(pool),24)
  for t in targets:self.assertEqual([d['id'] for _,d in retrieve(t,pool)],expected[t['id']])
 def test_public_artifacts_also_reproduce_original_50_benchmark_slots(self):
  pool=ev.load(RUN/'demonstration-pool.json');targets=ev.load(RUN/'retrieval-targets.json');selection=ev.load(RUN/'demonstration-selection.json')
  pool += [{'id':ident,**value} for ident,value in selection['excluded_example_texts'].items()]+targets
  expected={x['task_id']:x['original_demonstration_ids'] for x in selection['selection']}
  for t in targets:self.assertEqual([d['id'] for _,d in retrieve(t,pool)],expected[t['id']])
 def test_lexical_retrieval_excludes_target_and_breaks_ties_by_id(self):
  target={'id':'target','natural_language':'Create directory at /neutral'}
  pool=[target,{'id':'b','natural_language':'Create directory at /neutral'}, {'id':'a','natural_language':'Create directory at /neutral'}, {'id':'c','natural_language':'Install package'}]
  result=retrieve(target,pool,2)
  self.assertEqual([d['id'] for _,d in result],['a','b'])
  self.assertEqual(result[0][0],result[1][0])
 @unittest.skipUnless((RUN/'private/source/expanded.json').exists(), 'Private recovered source artifacts unavailable')
 def test_reproduces_actual_original_selector(self):
  refs=ev.load(ev.ROOT/'datasets/references-private.json');src=RUN/'private/source'
  expanded=ev.load(src/'expanded.json');records=[json.loads(l) for l in (src/'fql-queries.jsonl').read_text().splitlines()]
  supported={r['task_id'] for r in records if r['source']=='authored_candidate' and r['result']['returncode']==0}
  pool=refs+[x for x in expanded if x['id'] in supported]
  byid={x['id']:x for x in pool}
  old=ev.load(ev.ROOT/'datasets/imported-private.json')
  self.assertEqual(sum(int(i[1:])<=21 for t in old['tasks'] for i in t['demonstration_ids']),50)
  for t in old['tasks']:
   ref=next(r for r in refs if r['id']==t['task_id'])
   self.assertEqual([d['id'] for _,d in retrieve(ref,pool)],t['demonstration_ids'])
   for index,ident in enumerate(t['demonstration_ids']):
    self.assertEqual(t['messages'][2*index+1]['content'],byid[ident]['natural_language'])
    self.assertEqual(t['messages'][2*index+2]['content'],byid[ident]['formal_query'])
 @unittest.skipUnless((RUN/'private/manifest.json').exists(), 'Private frozen manifest unavailable')
 def test_only_demo_change(self):
  m=ev.load(RUN/'private/manifest.json');old={t['task_id']:t for t in ev.load(ev.ROOT/'datasets/imported-private.json')['tasks']}
  for c in m['cells']:
   self.assertEqual(len(c['demonstration_ids']),4)
   self.assertTrue(all(int(i[1:])>=22 and i not in EXCLUDED for i in c['demonstration_ids']))
   self.assertEqual(c['messages'][-1],old[c['task_id']]['messages'][-1])
   self.assertEqual(c['messages'][0]['content'],(ev.ROOT/'prompts'/f'{c["variant"]}.txt').read_text())
  self.assertEqual(len(m['cells']),2520);self.assertEqual(m['config']['max_output_tokens'],4096)
  self.assertEqual(m['repetitions'],10)
  original=ev.load(ev.ROOT/'results/2026-11-04-full-matrix/protocol.json')
  self.assertEqual(m['config']['models'],original['config']['models'])
  self.assertEqual(m['config']['reasoning_effort'],original['config']['reasoning_effort'])
  self.assertEqual(m['config']['max_output_tokens'],original['config']['max_output_tokens'])
if __name__=='__main__':unittest.main()
