#!/usr/bin/env python3
"""Export held-out-example run without publishing private inputs or reasoning."""
import argparse, json, shutil, time
from collections import Counter
from pathlib import Path
import evaluate as ev
from export_matrix import export,summarize,write_csv
from heldout_examples import RUN

PUBLIC_FILES=['per-call.csv','per-call.json','per-attempt.csv','per-attempt.json','model-variant-summary.csv','task-model-variant.csv','metadata.json','run-status.json']

def publish(stage='final'):
    private=RUN/'private';snapshot=private/('export-'+stage);snapshot.mkdir(exist_ok=True)
    m=ev.load(private/'manifest.json');s=ev.load(private/'state.json')
    if stage=='handbook-v3':
        m['cells']=[c for c in m['cells'] if c['variant']=='handbook-v3'];ids={c['id'] for c in m['cells']}
        s['attempts']=[a for a in s['attempts'] if a['cell_id'] in ids]
    (snapshot/'manifest.json').write_text(json.dumps(m,indent=2)+'\n');(snapshot/'state.json').write_text(json.dumps(s,indent=2)+'\n')
    for name in ['responses','attempts']:
        p=snapshot/name
        if not p.exists():p.symlink_to(private/name,target_is_directory=True)
    if (private/'run-status.json').exists():shutil.copy(private/'run-status.json',snapshot/'run-status.json')
    export(snapshot,ev.ROOT/'datasets/references-private.json')
    dest=RUN if stage=='final' else RUN/'handbook-v3-checkpoint';dest.mkdir(exist_ok=True)
    for name in PUBLIC_FILES:
        if (snapshot/name).exists():shutil.copy(snapshot/name,dest/name)
    rows=ev.load(snapshot/'per-call.json');original=ev.load(ev.ROOT/'results/2026-11-04-full-matrix/per-call.json')
    for row in rows:
        ident=f'{row["model_key"]}--{row["variant"]}--{row["task_id"]}--r{row["repeat"]}'
        path=private/'responses'/(ident+'.json');r=ev.load(path) if path.exists() else {};raw=r.get('response',{})
        stop=raw.get('stop_reason') or ((raw.get('choices') or [{}])[0].get('finish_reason')) or (raw.get('incomplete_details') or {}).get('reason')
        row.update(stop_reason=stop,cap_limited=stop in ('length','max_tokens','max_output_tokens'),final_fql_nonempty=bool(r.get('text','').strip()))
    (dest/'per-call.json').write_text(json.dumps(rows,indent=2)+'\n');write_csv(dest/'per-call.csv',rows)
    caprows=[]
    for model,variant in sorted({(r['model'],r['variant']) for r in rows}):
        rs=[r for r in rows if r['model']==model and r['variant']==variant]
        caprows.append({'model':model,'variant':variant,'n':len(rs),'completed':sum(r['status']=='completed' for r in rs),
          'incomplete':sum(r['status']=='incomplete' for r in rs),'cap_limited':sum(r['cap_limited'] for r in rs),
          'cap_without_final_fql':sum(r['cap_limited'] and not r['final_fql_nonempty'] for r in rs),
          'completed_semantically_invalid':sum(r['status']=='completed' and r['semantic_accepted'] is False for r in rs),
          'provider_or_transport_fail':sum(r['status'] in ('provider_error','transport_error','interrupted_unknown_billing') for r in rs),
          'pending_budget':sum(r['status']=='pending_budget' for r in rs)})
    write_csv(dest/'completion-diagnostics.csv',caprows)
    summary19=summarize([r for r in rows if r['task_id'] not in ('a18','a21')],['model','variant'])
    write_csv(dest/'model-variant-summary-19tasks.csv',summary19)
    comparison=[]
    for label,data in [('original',original),('heldout',rows)]:
        if stage=='handbook-v3':data=[r for r in data if r['variant']=='handbook-v3']
        for n,rs in [(21,data),(19,[r for r in data if r['task_id'] not in ('a18','a21')])]:
            for summary in summarize(rs,['model','variant']):comparison.append({'run':label,'tasks':n,**summary})
    write_csv(dest/'original-vs-heldout.csv',comparison)
    meta=ev.load(dest/'metadata.json');meta.pop('anthropic_remaining',None)
    pending=[c for c in m['cells'] if not (private/'responses'/(c['id']+'.json')).exists()]
    meta.update(stage=stage,total_guard_usd=12,anthropic_guard_usd=6,
      pending_cells=len(pending),anthropic_pending_cells=sum(c['model']=='opus' for c in pending),
      original_unmodified_reference_hash=ev.digest((ev.ROOT/'datasets/references-private.json').read_bytes()),
      statuses=dict(Counter(r['status'] for r in rows)),
      note='Original unmodified effect references; cap4096 retained; token-based costs at frozen rates, not invoices. Provider/transport failures separated, retained in denominator but not semantically classified as wrong.')
    (dest/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    protocol={'manifest_sha256':ev.digest(m),'config':m['config'],'sources':m['sources'],'repetitions':10,
      'stage':stage,'change':'Only four demonstrations per target replaced using same original TF-IDF selector restricted to24 non-benchmark examples after duplicate review.',
      'transport':'Router SSE streaming to avoid gateway524; same model/messages/reasoning/max_tokens as original; no temperature/top_p/seed.',
      'max_attempts':8,'total_guard_usd':12,'anthropic_guard_usd':6,
      'task_ids':sorted({c['task_id'] for c in m['cells']}),'sampling':'Independent fresh API requests; temperature,top_p,seed omitted.',
      'selection':ev.load(RUN/'demonstration-selection.json')['selection']}
    (dest/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    # Public completions intentionally omit provider reasoning and raw input/reference queries.
    with (dest/'model-outputs.jsonl').open('w') as f:
        for c in m['cells']:
            p=private/'responses'/(c['id']+'.json');r=ev.load(p) if p.exists() else {'status':'pending_budget','text':''}
            f.write(json.dumps({'cell_id':c['id'],'model':m['config']['models'][c['model']]['id'],'variant':c['variant'],'task_id':c['task_id'],'repeat':c['repeat'],'status':r['status'],'text':r.get('text',''),'returned_model':r.get('returned_model')})+'\n')
    return dest

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--wait',action='store_true');p.add_argument('--stage',choices=['handbook-v3','final'],default='final');a=p.parse_args()
    sentinel=RUN/'private'/('handbook-v3-finished.json' if a.stage=='handbook-v3' else 'run-status.json')
    while a.wait and not sentinel.exists():time.sleep(15)
    print(publish(a.stage))
