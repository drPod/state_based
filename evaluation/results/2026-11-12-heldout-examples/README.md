# Held-out demonstrations: NL-to-FQL matrix

This run changes the four in-context demonstrations per benchmark target. The target requests, compact-v1 and handbook-v3 system prompts, alternating user/assistant demonstration format, six model IDs, HIGH effort (Qwen XHIGH), 4096 output-token limit, omitted temperature/top_p/seed, and ten repeats remain as in the November 4 full matrix. This is a demonstration-pool ablation on the same development benchmark, not a claim of unseen-domain generalization.

The prior matrix used 21 different four-example sets: 50 of 84 example slots came from other benchmark tasks a01–a21. Its imported dataset SHA256 `49c4ed9f5766505aa09fa47704cebd6ecd89d716fe6574abc78f16632b8801c8` matches the frozen original protocol. `test_heldout.py` reproduces every historical selection from the recovered original selector and original pool.

## Original and revised selection

The original `research/astrogator/scripts/retrieval_fql.py:retrieve` uses lowercase `[a-z]+` term counts, excluding `a an the to of and is in on for with it be`; smoothed inverse document frequency `log((N+1)/(df+1))+1`; cosine similarity; descending score and ascending example-ID tie breaking; top four. The original pool was 21 benchmark tasks plus 31 authored extras whose queries passed native lowering. The target itself was excluded. Selection is lexical, deterministic, per target, and uses only the NL for similarity.

All 49 extras a22–a70 were reviewed before inference for exact concrete-object overlap or renamed paraphrases of a complete benchmark operation and constraint. None uses an identical benchmark path/package/user. Conservative additional paraphrase exclusions:

| Extra | Benchmark | Reason |
|---|---|---|
| a25 | a06 | Conditional create-if-absent file; renamed path and literal |
| a27 | a04 | Remote file copy, with destination-directory prerequisite |
| a28 | a05 | File move with renamed paths and explicit idempotence |
| a30 | a02 | Recursive directory removal with renamed path and preservation clarification |
| a32 | a13 | Same recursive owner-write/all-read/directory-traversal permissions |
| a46 | a17 | Disable password on renamed account |
| a65 | a11 | Append one literal line to a renamed profile |

The 18 extras that did not pass the original authored-candidate native-lowering gate remain ineligible: a33–a39, a41, a48–a51, a55–a60. The final pool has 24 extras. Other shared action families remain eligible when their concrete objects and requested behavior differ. This documented manual review is conservative, not an automated proof of absence of semantic similarity.

`demonstration-pool.json` publishes all 24 eligible authored NL/FQL pairs; `retrieval-targets.json` publishes the 21 target NL/IDs. Reproduce selection without private VPS artifacts or API calls: `python3 evaluation/code/heldout_examples.py select-public`.

`demonstration-selection.json` lists all exclusions, eligible/ineligible IDs, all 49 review decisions, per-target four IDs and retrieval scores, and original four IDs. Restricted-pool TF-IDF is recomputed; it does not merely remove benchmark IDs from the previous top four.

## Execution and scoring

`evaluation/code/heldout_examples.py freeze` freezes private source-derived inputs; `run` executes handbook-v3 first, compact-v1 second, sharing this job's separate ledger. Router calls use SSE streaming to avoid the earlier nonstreaming gateway 524 failures; payload model/messages/effort/output cap are unchanged. Eight-attempt transient retry maximum with exponential backoff; gateway failures and unknown billing reservations remain in per-attempt history. Nontransient errors and exhausted retries are reported separately, never silently deleted or called semantic failures. The job has $12 total/$6 Anthropic guards, including in-flight reservations; budget-skipped cells remain resumable. Dataset-validity spending is separate.

Free native scoring is exactly `export_matrix.py`: raw response text without repair/fence removal; lexer/parser; semantic processing; native `query_interp`; structural normalized effect-tree equality against the **original unmodified** references. References a03/a20 remain disputed and are flagged. a18/a21 are also excluded in the separate requested 19-task view. No corrected references or task-local matching policies are used. No LLM judge, VM, container, or generated program execution is involved.

Build the native components with the installed OCaml switch: `opam exec --switch=/home/user/workspaces/state_based -- dune build evaluation/native/effects.exe bin/query_interp.exe bin/verify.exe`. The free `verify.exe` diagnostic symbolically checks supplied reference playbooks as in the previous export; this is not runtime testing or the primary correctness metric.

## Exports

- `per-call.csv`/`.json`: one row for every planned cell, including API/budget failures.
- `per-attempt.csv`/`.json`: all paid attempts, retries, tokens, costs, errors.
- `model-variant-summary.csv`: 21-task original-reference scores and Wilson intervals.
- `model-variant-summary-19tasks.csv`: excludes a18/a21.
- `original-vs-heldout.csv`: original and rerun scores, both prompts and both task sets.
- `task-model-variant.csv`: per-task counts for all six models and both prompts.
- `model-outputs.jsonl`: canonical generated FQL text, with no private reasoning.
- `completion-diagnostics.csv`: completed invalid outputs, 4096-token length stops, cap stops without final FQL, API errors and pending cells separately.
- `report.md`, `validation.json`: plain result tables and consistency/request/secret audits.
- `protocol.json`, `metadata.json`, `run-status.json`: frozen settings/hashes, exact token accounting, status totals, guard and pending-cell accounting.
- `handbook-v3-checkpoint/`: first-completed v3 report, published while compact-v1 runs.

Costs are token-accounted estimates at frozen rates, not provider invoices. Unknown-billing attempts retain full conservative reservation. Router catalog does not itself label currency/denominator; USD per million tokens remains the original assumption. Only this project's authored demonstration pool and target NL are public. No third-party AnsibleDataset data, target reference FQL, or private provider reasoning is published.
