#!/usr/bin/env python3
"""Plain factual held-out matrix tables; no charts."""
import argparse,csv,json
from collections import Counter
from pathlib import Path
from evaluate import load
from heldout_examples import RUN

def report(directory):
 rows=load(directory/'per-call.json');old=load(RUN.parent/'2026-11-04-full-matrix/per-call.json');meta=load(directory/'metadata.json')
 variants=[v for v in ['handbook-v3','compact-v1'] if any(r['variant']==v for r in rows)]
 models=['gpt-6.1-sol','claude-opus-5-5','deepseek-v4.1-flash','deepseek-v4-flash','glm-5.3','qwen3.8-flash']
 def score(data,model,variant,exclude):
  rs=[r for r in data if r['model']==model and r['variant']==variant and (not exclude or r['task_id'] not in ('a18','a21'))]
  correct=sum(r['ref_match'] is True for r in rs)
  return f'{correct}/{len(rs)} ({100*correct/len(rs):.2f}%)'
 text=['# Held-out demonstrations: results','',f"Stage: {meta['stage']}. Original unmodified references; reference-effect match is the reported correct metric.",'']
 selection=load(RUN/'demonstration-selection.json')
 text += ['## Demonstration selection','','The original frozen matrix used 50 benchmark examples across 84 slots. Exact recovered TF-IDF cosine selection reproduces all 21 original per-task sets. The rerun uses only non-benchmark extras: 31 originally lowered candidates, minus seven conservative renamed paraphrases, leaving 24 eligible examples; 20 appear in the resulting 84 slots.','', '| Excluded extra | Similar benchmark / executor problem | Reason |','|---|---|---|']
 for extra,v in selection['excluded_near_duplicates'].items():text.append('| '+extra+' | '+v['benchmark']+'/'+v['legacy_id']+' | '+v['rationale']+' |')
 text.append('')
 for variant in variants:
  text += [f'## {variant}','','| Model | Original 21 tasks | Held-out 21 tasks | Original 19 tasks | Held-out 19 tasks |','|---|---:|---:|---:|---:|']
  for model in models:text.append('| '+model+' | '+' | '.join(score(data,model,variant,ex) for ex in [False,True] for data in [old,rows])+' |')
  text.append('')
 if 'handbook-v3' in variants:
  text += ['## Per-task handbook-v3 correct counts','','Each cell is out of ten calls. Column order follows the model lineup above.','','| Task | Sol | Opus | DS4.1 | DS4 | GLM | Qwen |','|---|---:|---:|---:|---:|---:|---:|']
  for task in sorted({r['task_id'] for r in rows}):text.append('| '+task+' | '+' | '.join(str(sum(r['ref_match'] is True for r in rows if r['task_id']==task and r['model']==model and r['variant']=='handbook-v3')) for model in models)+' |')
  text.append('')
 attempts=load(directory/'per-attempt.json');known=sum(a['cost_usd'] for a in attempts if a['cost_source']=='reported_tokens_at_frozen_rates');reserve=sum(a['cost_usd'] for a in attempts if a['cost_source']!='reported_tokens_at_frozen_rates')
 text += ['## Accounting and failures','',f"Accounted USD: {meta['budget_accounted_usd']:.12f}; known token-priced USD: {known:.12f}; unknown-billing reserved USD: {reserve:.12f}; Anthropic USD: {meta['by_model'].get('claude-opus-5-5',0):.12f}.",'',f"Canonical statuses: {dict(Counter(r['status'] for r in rows))}; attempts: {len(attempts)}; attempt statuses: {dict(Counter(a['status'] for a in attempts))}.",'','Provider failures, pending cells, and cap-driven incompletes are separate in completion-diagnostics.csv. A 4096-token length stop is a cap outcome, not an API failure or proof of inability to translate. Known token charges plus unknown-billing reserves are accounting values, not provider invoices.','']
 (directory/'report.md').write_text('\n'.join(text))
 print('\n'.join(text))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();report(a.directory)
