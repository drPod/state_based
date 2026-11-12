#!/usr/bin/env python3
"""Held-out demonstration selection and separately budgeted resumable matrix."""
import argparse, concurrent.futures, fcntl, json, math, os, re
from collections import Counter
from pathlib import Path
import evaluate as ev
from matrix_run import Matrix
import heldout_transport as transport

RUN=ev.ROOT/'results/2026-11-12-heldout-examples'
EXCLUDED={
'a25':('a06','Same conditional file creation; renamed path and literal content.'),
'a27':('a04','Same remote file copy; destination-directory creation is an added prerequisite.'),
'a28':('a05','Same file move; renamed source/destination and explicit idempotence.'),
'a30':('a02','Same recursive directory removal; renamed directory and sibling-preservation clarification.'),
'a32':('a13','Same recursive owner-write/all-read/directory-traversal permission policy; renamed path.'),
'a46':('a17','Same password-disabling action; renamed account and preservation clarification.'),
'a65':('a11','Same append-one-line-to-profile action; renamed profile and line literal.')}

def tokens(text):
    stop={'a','an','the','to','of','and','is','in','on','for','with','it','be'}
    return Counter(w for w in re.findall(r'[a-z]+',text.lower()) if w not in stop)

def retrieve(target,pool,count=4):
    candidates=[b for b in pool if b['id']!=target['id']]
    docs=[tokens(b['natural_language']) for b in candidates];query=tokens(target['natural_language'])
    df=Counter(w for d in docs for w in d)
    def vector(d):return {w:n*(math.log((len(docs)+1)/(df[w]+1))+1) for w,n in d.items()}
    q=vector(query);qnorm=math.sqrt(sum(v*v for v in q.values()));scores=[]
    for b,doc in zip(candidates,docs):
        v=vector(doc);norm=math.sqrt(sum(x*x for x in v.values()))
        score=sum(x*q.get(w,0) for w,x in v.items())/(norm*qnorm) if norm*qnorm else 0
        scores.append((score,b))
    return sorted(scores,key=lambda item:(-item[0],item[1]['id']))[:count]

def freeze():
    private=RUN/'private';src=private/'source';originals=ev.load(ev.ROOT/'datasets/references-private.json')
    expanded=ev.load(src/'expanded.json');records=[json.loads(l) for l in (src/'fql-queries.jsonl').read_text().splitlines()]
    supported={r['task_id'] for r in records if r['source']=='authored_candidate' and r['result']['returncode']==0}
    pool=[x for x in expanded if x['id'] in supported and x['id'] not in EXCLUDED]
    assert len(pool)==24 and all(22<=int(x['id'][1:])<=70 for x in pool)
    old=ev.load(ev.ROOT/'datasets/imported-private.json');tasks=[];selection=[]
    for target in originals:
        prior=next(t for t in old['tasks'] if t['task_id']==target['id']);demos=retrieve(target,pool)
        messages=[prior['messages'][0]]
        for _,d in demos:messages.extend([{'role':'user','content':d['natural_language']},{'role':'assistant','content':d['formal_query']}])
        messages.append(prior['messages'][-1]);assert messages[-1]['content']==target['natural_language']
        ids=[d['id'] for _,d in demos];tasks.append({'task_id':target['id'],'demonstration_ids':ids,'messages':messages})
        selection.append({'task_id':target['id'],'demonstration_ids':ids,'scores':[s for s,_ in demos],'original_demonstration_ids':prior['demonstration_ids']})
    dataset=private/'heldout-private.json';ev.write_new(dataset,{'tasks':tasks})
    m=ev.freeze(dataset,None,['handbook-v3','compact-v1']);m['config'].update(prior_cost_usd=0,prior_anthropic_cost_usd=0,provider_budgets_usd={'anthropic':6},stream_deadline_s=900)
    m['cells'].sort(key=lambda c:(c['variant']!='handbook-v3',ev.digest(c['id'])))
    m['scope']='Held-out demonstration pool ablation; benchmark targets unchanged; no unseen-domain correctness claim'
    m['sources']['selector_source']=ev.digest((src/'retrieval_fql.py').read_bytes())
    ev.write_new(private/'manifest.json',m)
    audit={'review_rule':'Exclude exact concrete-object overlaps and renamed paraphrases of complete benchmark actions/constraints; retain distinct same-family examples. Review all49 before inference; no generated outcomes inspected.',
      'original_benchmark_slots':sum(int(i[1:])<=21 for t in old['tasks'] for i in t['demonstration_ids']),
      'supported_extras':sorted(supported),'excluded_near_duplicates':{k:{'benchmark':v[0],'rationale':v[1]} for k,v in EXCLUDED.items()},
      'ineligible_original_native_lowering':sorted(x['id'] for x in expanded if x['id'] not in supported),
      'eligible_pool':sorted(x['id'] for x in pool),'selection':selection,'selector':'Exact original TF-IDF cosine retrieval, reranked on restricted24-example pool; top4; descending score then ascending ID.',
      'reviewed_extras':[{'id':x['id'],'decision':'exclude_paraphrase' if x['id'] in EXCLUDED else ('eligible' if x['id'] in supported else 'ineligible_original_lowering'),'nl_sha256':ev.digest(x['natural_language'].encode())} for x in expanded]}
    ev.write_new(RUN/'demonstration-selection.json',audit)
    print(json.dumps({'planned':len(m['cells']),'pool':len(pool),'estimate':ev.estimate(m)}),flush=True)

def run(include_compact=False):
    os.environ.update(ev.load('/tmp/astrogator-provider-env.json'));private=RUN/'private';m=ev.load(private/'manifest.json')
    with (private/'.matrix.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        matrix=Matrix(m,private,total=12,anthropic=6,max_attempts=8,request_fn=transport.request,build_fn=transport.build)
        for variant in (['handbook-v3','compact-v1'] if include_compact else ['handbook-v3']):
            cells=[c for c in m['cells'] if c['variant']==variant]
            while True:
                before=len(matrix.state['attempts'])
                with concurrent.futures.ThreadPoolExecutor(max_workers=24) as pool:
                    jobs=[pool.submit(matrix.process,c) for c in cells]
                    for j in concurrent.futures.as_completed(jobs):j.result()
                if before==len(matrix.state['attempts']):break
            print(json.dumps({'variant_finished':variant,'terminal':sum((private/'responses'/(c['id']+'.json')).exists() for c in cells),'accounted_usd':matrix.spend(),'anthropic_usd':matrix.spend('anthropic')}),flush=True)
            (private/(variant+'-finished.json')).write_text(json.dumps({'variant':variant,'accounted_usd':matrix.spend()}))
        terminal=sum((private/'responses'/(c['id']+'.json')).exists() for c in m['cells'])
        result={'planned':len(m['cells']),'terminal':terminal,'pending':len(m['cells'])-terminal,
          'attempts':len(matrix.state['attempts']),'accounted_usd':matrix.spend(),'anthropic_accounted_usd':matrix.spend('anthropic'),
          'total_limit_usd':12,'anthropic_limit_usd':6,'compact_deferred':not include_compact,
          'compact_paid_attempts':sum('--compact-v1--' in a['cell_id'] for a in matrix.state['attempts'])}
        (private/('run-status.json' if include_compact else 'v3-only-run-status.json')).write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['freeze','run','select-public','select-original-public']);p.add_argument('--include-compact',action='store_true',help='Requires renewed user approval; default pauses after v3');a=p.parse_args()
    if a.command in ('select-public','select-original-public'):
        pool=ev.load(RUN/'demonstration-pool.json');targets=ev.load(RUN/'retrieval-targets.json')
        if a.command=='select-original-public':
            excluded=ev.load(RUN/'demonstration-selection.json')['excluded_example_texts']
            pool=pool+[{'id':ident,**value} for ident,value in excluded.items()]+targets
        print(json.dumps([{'task_id':t['id'],'demonstration_ids':[d['id'] for _,d in retrieve(t,pool)]} for t in targets],indent=2))
    else:freeze() if a.command=='freeze' else run(a.include_compact)
