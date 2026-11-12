#!/usr/bin/env python3
"""Free consistency/secret audit for published held-out-examples artifacts."""
import argparse,csv,json
from datetime import datetime,timezone
from collections import Counter
from pathlib import Path
from evaluate import digest,load
from export_matrix import summarize
from heldout_examples import RUN

def validate(directory):
 rows=load(directory/'per-call.json');meta=load(directory/'metadata.json');protocol=load(directory/'protocol.json')
 expected=1260 if protocol['stage']=='handbook-v3' else 2520
 assert len(rows)==expected
 keys=[(r['model'],r['variant'],r['task_id'],r['repeat']) for r in rows];assert len(set(keys))==expected
 assert all(0<=r['repeat']<10 for r in rows)
 assert len({r['model'] for r in rows})==6
 assert {r['task_id'] for r in rows}=={f'a{i:02}' for i in range(1,22)}
 assert meta['budget_accounted_usd']<=12+1e-9
 assert meta['by_model'].get('claude-opus-5-5',0)<=6+1e-9
 actual=load(RUN/'demonstration-selection.json')
 assert len(actual['eligible_pool'])==24
 assert all(int(x[1:])>=22 for s in actual['selection'] for x in s['demonstration_ids'])
 outputs=[json.loads(l) for l in (directory/'model-outputs.jsonl').read_text().splitlines()];assert len(outputs)==expected
 indexed={(x['model'],x['variant'],x['task_id'],x['repeat']):x for x in outputs}
 for r in rows:
  o=indexed[(r['model'],r['variant'],r['task_id'],r['repeat'])]
  assert o['status']==r['status']
  if r['output_sha256']:assert digest(o['text'].encode())==r['output_sha256']
  if r['status'] in ('provider_error','transport_error','pending_budget'):assert r['parsed'] is None and r['ref_match'] is None
 publicsummary=list(csv.DictReader((directory/'model-variant-summary.csv').open()))
 for actualrow,expectedrow in zip(publicsummary,summarize(rows,['model','variant'])):
  for key in ['model','variant','n','correct']:assert actualrow[key]==str(expectedrow[key])
  assert abs(float(actualrow['rate'])-expectedrow['rate'])<1e-12
 attemptrows=load(directory/'per-attempt.json');assert len(attemptrows)==sum(r['attempts'] for r in rows)
 assert abs(sum(r['cost_usd'] for r in rows)-meta['matrix_cost_usd'])<1e-8
 assert abs(sum(a['cost_usd'] for a in attemptrows)-meta['matrix_cost_usd'])<1e-8
 request_count=0;private=RUN/'private';frozen_manifest=load(private/'manifest.json');frozen_cells={c['id']:c for c in frozen_manifest['cells']}
 first_started=min(a['started_at'] for a in load(private/'state.json')['attempts'])
 frozen_at=datetime.fromtimestamp((private/'manifest.json').stat().st_mtime,timezone.utc)
 assert frozen_at<datetime.fromisoformat(first_started)
 for a in attemptrows:
  modelkey=next(k for k,v in protocol['config']['models'].items() if v['id']==a['model'])
  ident=f'{modelkey}--{a["variant"]}--{a["task_id"]}--r{a["repeat"]}'
  raw=load(private/'attempts'/(ident+f'--attempt{a["attempt"]}.json'));body=raw['request_body'];model=protocol['config']['models'][modelkey]
  assert body['model']==model['id']
  messages=frozen_cells[ident]['messages']
  if model['provider']=='openai':assert body['input']==messages
  elif model['provider']=='anthropic':assert body['system']==messages[0]['content'] and body['messages']==messages[1:]
  else:assert body['messages']==messages
  assert body.get('max_tokens',body.get('max_output_tokens'))==4096
  assert not {'temperature','top_p','seed'} & body.keys()
  effort=body.get('reasoning_effort',body.get('reasoning',{}).get('effort',body.get('output_config',{}).get('effort')))
  assert effort==model['reasoning_effort']
  request_count+=1
 sources={str(p.relative_to(RUN)):digest(p.read_bytes()) for p in [RUN/'runner-at-first-launch.py',RUN/'transport-at-first-launch.py',RUN/'demonstration-pool.json',RUN/'retrieval-targets.json',RUN/'demonstration-selection.json']}
 meta['heldout_public_source_sha256']=sources
 (directory/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
 # Scan only explicit public whitelist, never publish credentials or provider reasoning.
 secrets=list(load('/tmp/astrogator-provider-env.json').values())+[Path('/tmp/astrogator-gh-token').read_text().strip()]
 files=[p for p in directory.iterdir() if p.is_file()]
 for p in files:
  content=p.read_text()
  for value in secrets:
   if len(value)>20 and not value.startswith('https://'):assert value not in content, f'Secret audit failed for {p.name}'
 summary={'rows':len(rows),'unique_cells':len(set(keys)),'attempts':len(attemptrows),'statuses':dict(Counter(r['status'] for r in rows)),
 'reference_hash_matches_original':meta['references_sha256']==load(RUN.parent/'2026-11-04-full-matrix/metadata.json')['references_sha256'],
 'accounted_usd':meta['budget_accounted_usd'],'anthropic_usd':meta['by_model'].get('claude-opus-5-5',0),
 'manifest_frozen_at':frozen_at.isoformat(),'first_request_at':first_started,'frozen_before_generation':True,'request_settings_and_messages_audited':request_count,'duplicate_cells':False,'output_hashes_match':True,'summary_matches':True,'secret_audit_passed':True}
 assert summary['reference_hash_matches_original']
 (directory/'validation.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);args=p.parse_args();validate(args.directory)
