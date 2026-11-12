# Held-out demonstrations: results

Stage: handbook-v3. Original unmodified references; reference-effect match is the reported correct metric. Compact-v1 is deferred by Darsh; zero compact calls were made.

## Demonstration selection

The original frozen matrix used 50 benchmark examples across 84 slots. Exact recovered TF-IDF cosine selection reproduces all 21 original per-task sets. The rerun uses only non-benchmark extras: 31 originally lowered candidates, minus seven conservative renamed paraphrases, leaving 24 eligible examples; 20 appear in the resulting 84 slots.

| Excluded extra | Similar benchmark / executor problem | Reason |
|---|---|---|
| a25 | a06/p13 | Same conditional file creation; renamed path and literal content. |
| a27 | a04/p03 | Same remote file copy; destination-directory creation is an added prerequisite. |
| a28 | a05/p12 | Same file move; renamed source/destination and explicit idempotence. |
| a30 | a02/p05 | Same recursive directory removal; renamed directory and sibling-preservation clarification. |
| a32 | a13/p04 | Same recursive owner-write/all-read/directory-traversal permission policy; renamed path. |
| a46 | a17/p10 | Same password-disabling action; renamed account and preservation clarification. |
| a65 | a11/p09 | Same append-one-line-to-profile action; renamed profile and line literal. |

## handbook-v3

| Model | Original 21 tasks | Held-out 21 tasks | Original 19 tasks | Held-out 19 tasks |
|---|---:|---:|---:|---:|
| gpt-6.1-sol | 180/210 (85.71%) | 155/210 (73.81%) | 180/190 (94.74%) | 155/190 (81.58%) |
| claude-opus-5-5 | 181/210 (86.19%) | 165/210 (78.57%) | 181/190 (95.26%) | 165/190 (86.84%) |
| deepseek-v4.1-flash | 165/210 (78.57%) | 144/210 (68.57%) | 165/190 (86.84%) | 144/190 (75.79%) |
| deepseek-v4-flash | 165/210 (78.57%) | 146/210 (69.52%) | 165/190 (86.84%) | 146/190 (76.84%) |
| glm-5.3 | 149/210 (70.95%) | 131/210 (62.38%) | 149/190 (78.42%) | 131/190 (68.95%) |
| qwen3.8-flash | 154/210 (73.33%) | 136/210 (64.76%) | 154/190 (81.05%) | 136/190 (71.58%) |

## Per-task handbook-v3 correct counts

Each cell is out of ten calls. Column order follows the model lineup above.

| Task | Sol | Opus | DS4.1 | DS4 | GLM | Qwen |
|---|---:|---:|---:|---:|---:|---:|
| a01 | 10 | 10 | 10 | 10 | 10 | 10 |
| a02 | 10 | 10 | 10 | 10 | 10 | 10 |
| a03 | 10 | 10 | 9 | 9 | 9 | 10 |
| a04 | 10 | 10 | 10 | 10 | 7 | 8 |
| a05 | 10 | 10 | 9 | 10 | 9 | 9 |
| a06 | 10 | 10 | 9 | 10 | 1 | 9 |
| a07 | 10 | 10 | 10 | 10 | 9 | 10 |
| a08 | 10 | 10 | 10 | 10 | 9 | 10 |
| a09 | 10 | 10 | 9 | 8 | 6 | 8 |
| a10 | 10 | 9 | 10 | 10 | 10 | 10 |
| a11 | 10 | 10 | 10 | 10 | 10 | 9 |
| a12 | 10 | 10 | 9 | 10 | 10 | 10 |
| a13 | 10 | 10 | 2 | 0 | 6 | 0 |
| a14 | 10 | 10 | 10 | 10 | 10 | 9 |
| a15 | 0 | 3 | 3 | 5 | 0 | 3 |
| a16 | 5 | 3 | 0 | 4 | 1 | 0 |
| a17 | 10 | 10 | 10 | 10 | 10 | 9 |
| a18 | 0 | 0 | 0 | 0 | 0 | 0 |
| a19 | 0 | 0 | 0 | 0 | 0 | 0 |
| a20 | 0 | 10 | 4 | 0 | 4 | 2 |
| a21 | 0 | 0 | 0 | 0 | 0 | 0 |

## Accounting and failures

Accounted USD: 5.600944764488; known token-priced USD: 5.104792150617; unknown-billing reserved USD: 0.496152613871; Anthropic USD: 3.761715000000.

Canonical statuses: {'completed': 1206, 'incomplete': 53, 'transport_error': 1}; attempts: 1334; attempt statuses: {'completed': 1206, 'transport_error': 73, 'incomplete': 53, 'interrupted_unknown_billing': 1, 'provider_error': 1}.

Provider failures, pending cells, and cap-driven incompletes are separate in completion-diagnostics.csv. A 4096-token length stop is a cap outcome, not an API failure or proof of inability to translate. Known token charges plus unknown-billing reserves are accounting values, not provider invoices.
