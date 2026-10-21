# TD1 trace analysis

AI-assisted analysis of the retained TD1 batches, 21 October 2026.
No additional model calls were made for this analysis. References were computed
locally using SQL; peer and instructor validation is still pending.

## Results

The primary comparison contains 100 real model/question results: 20 for each
required model, with 76 correct answers, 20 incorrect answers, 3 invalid SQL
results, and 1 cell still not executed. The last attempt determines the final
status; retries remain in the raw traces. This is a small batch, not a general
model ranking.

The 20-call GPT-OSS 120B Groq batch has 19 correct answers and one incorrect
answer (C19). The other primary batches are summarized by family in
`five-model-summary-en.csv`. Qwen C20 remains not executed after HTTP 429 rate
limits on both attempts; that is a failed access, not a wrong answer.

An additional 20-call Dots3 run is retained separately in
`traces-dots3-C01-C20.csv` and `state-dots3-C01-C20.jsonl`. It differs from the
primary Dots3 run and is not substituted into the primary comparison or merged
as if it were a retry. Both runs remain available for inspection.

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
This identifies the prompt used for that question. The five primary model batches
share the same fingerprint for each question, so their prompts match case by case.

For C19, latency is 1616.1 ms, prompt tokens 662, completion tokens 413 and
reasoning tokens 290. Native cost was not reported and remains empty; it is not
replaced with zero. Reasoning tokens are not added to completion tokens here.
For retry and access-failure examples, inspect Qwen's attempts for C16-C20 in
`traces-D.csv`; the first four were completed on retry, while C20 remained
unavailable after HTTP 429 responses.

## Portfolio and next steps

The summary uses the supplied historical portfolio and the dated sources recorded
in `five-model-summary-en.csv`. These are historical kit values, not verified live
prices. Missing entries and undocumented exact-model paid routes remain N/A. The
required model identifiers follow `modeles-autorises.json`, including Cohere
North Mini Code rather than the stale Ling row in the original summary template.

This batch suggests checking completed-age SQL carefully, especially when age,
period and product restrictions are combined. Results support only a routing
hypothesis for these questions, prompts and access routes. Validate references
with another member and the instructor, and replace historical portfolio data if
current sources are required for presentation.
