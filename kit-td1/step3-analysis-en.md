# TD1 trace analysis

AI-assisted analysis of the retained GPT-OSS 120B batch, 21 October 2026.
No additional model calls were made for this analysis. References were computed
locally using SQL; peer and instructor validation is still pending.

## Results

The retained experiment contains 20 real first attempts on Groq, temperature 0,
for `openai/gpt-oss-120b`. Nineteen match the reference; C19 differs. No access
failure, retry, rejected SQL or invalid SQL appears in this batch.
The other four models have no retained traces and are marked `not_executed`.
This is an incomplete five-model comparison, not a comparative ranking.

The comparison CSV is the source for `model-question-pivot-en.md`. Individual
period, age and product views include combined questions, so their counts overlap.
The combined view counts questions whose type contains `+`.

## C19

Raw trace: `traces-gpt120b-C01-C20.csv`, cell
`groq:openai/gpt-oss-120b:C19`, attempt 1, HTTP 200, nature `real`.
The query runs successfully but returns 0 cents instead of 1990 cents.

Its age condition is:

```sql
c.birth_date = date('2026-09-25', '-25 years')
```

This selects only customers born on 2001-09-25. The question asks for everyone
aged 25 on 2026-09-25: birth dates strictly after 2000-09-25 and up to and
including 2001-09-25. The product and period filters in this trace match the
question. The observed error is a semantic age-filter error, not an access error.
An appropriate replacement for this case is:

```sql
c.birth_date > '2000-09-25' AND c.birth_date <= '2001-09-25'
```

The original trace is retained unchanged; this explanation does not turn the
failed answer into a successful attempt.

## Fingerprint and measurements

Each trace records `prompt_sha256`. C19 has fingerprint
`e5396619f946e273f11d2baf48666f84d8a817fde9f7189579c96ce2c2a14119`.
This identifies the prompt used for that question. With only one retained model,
equality of fingerprints across models cannot yet be demonstrated.

For C19, latency is 1616.1 ms, prompt tokens 662, completion tokens 413 and
reasoning tokens 290. Native cost was not reported and remains empty; it is not
replaced with zero. Reasoning tokens are not added to completion tokens here.
There is no retry to analyse in this batch. An instructor-supplied identified
access-failure example is still needed to demonstrate that part of the exercise.

## Portfolio and next steps

The summary uses the supplied historical portfolio, with index observation date
2026-09-28 and paid-price observation date 2026-09-29 as documented in
`portefeuille-modeles-en.md`. These are historical kit values, not verified live
prices. Missing entries and undocumented exact-model paid routes remain N/A.
The required model identifiers follow `modeles-autorises.json`, including Cohere
North Mini Code rather than the stale Ling row in the original summary template.

This batch suggests checking completed-age SQL carefully, especially when age,
period and product restrictions are combined. No routing advantage over other
models can be inferred until their retained traces are supplied. Complete the
remaining 80 cells from group evidence, validate references with another member
and the instructor, and replace historical portfolio data if current sources are
required for presentation.
