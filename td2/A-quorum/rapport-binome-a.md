# Rapport TD 2 — Quorum et règle de routage
**Policy:** the written rules that the code applies, version 2.0 (esilv-td-skeleton/2). Attempt: one call to one resource.

The implemented policy. At most 2 attempts on the same resource. 3 seconds of pacing between requests, 5 seconds on temporary errors, and up to 60 seconds on HTTP 429 if Retry-After permits. Then the next resource that is good enough. If there is none: defer or abstain. Never deliver without the required check.

A busy provider answers HTTP 429 for a few minutes: you saw it in TD 1 (retried once if delay ≤ 60 s, otherwise recorded as not executed).
A question has a timeout limit of 45 seconds: a shorter limit kills valid reasoning.
Every attempt is one line in the trace (column attempts).
A stronger model is one more attempt. It is not a proof.
A quorum requires a strict majority (k>n/2). Without consensus, it abstains. It never invents a value.

## Étape 1 — Vote *k*-sur-*n* (Binôme A)

### 1.1 Completed Method



**def vote_k_sur_n(self, traces_question: list, k: int):**

         """TD 2 contract. `traces_question` holds the proposals of the panel for one
        question, as built by `atelier-vote.py`. Each proposal carries `provider`,
        `model_requested`, `value` (integer cents or None) and `verdict`
        (`executed` or `error`). No reference is passed in: the vote decides
        first, the comparison with your reference comes after.

          1. Only executed proposals that carry a value vote. An error or an
             unavailable member stays in n and casts no vote.
          2. k is a strict majority: n // 2 < k <= n, otherwise raise ValueError.
          3. Two proposals with the same (provider, model_requested) are refused
             with a ValueError: a duplicate is not a second vote.
          4. If a value reaches k votes, return
             {"consensus": True, "value": v, "votes": count, "models": [...]}
             where models lists "provider:model_requested" of the agreeing
             members.
          5. Otherwise return {"consensus": False, "value": None,
             "votes": largest count, "models": []}. Never invent a value.

        Seen in lecture 2: models trained on close data are wrong together, so a
        consensus is not a proof of correctness. Keep the panel to distinct model
        families, and look in your traces for a case where several models agree
        on a wrong value.
        """
        n = len(traces_question)
        if not (isinstance(k, int) and (n // 2) < k <= n):
            raise ValueError(f"k must be a strict majority: {n // 2} < k <= {n}, got {k}")

        seen_models = set()
        for item in traces_question:
            provider = getattr(item, "provider", None) if not isinstance(item, dict) else item.get("provider")
            model = getattr(item, "model_requested", None) if not isinstance(item, dict) else item.get("model_requested")
            key = (provider, model)
            if key in seen_models:
                raise ValueError(f"Duplicate proposal from the same provider and model pair: {key}")
            seen_models.add(key)

        from collections import defaultdict
        votes_by_value = defaultdict(list)

        for item in traces_question:
            provider = getattr(item, "provider", None) if not isinstance(item, dict) else item.get("provider")
            model = getattr(item, "model_requested", None) if not isinstance(item, dict) else item.get("model_requested")
            verdict = getattr(item, "verdict", None) if not isinstance(item, dict) else item.get("verdict")
            val = getattr(item, "value", None) if not isinstance(item, dict) else item.get("value")

            if verdict == "executed" and val is not None and not isinstance(val, bool):
                try:
                    val = int(val)
                except (ValueError, TypeError):
                    continue
                votes_by_value[val].append(f"{provider}:{model}")

        max_votes = 0
        winner_val = None
        winner_models = []

        for val, models in votes_by_value.items():
            count = len(models)
            if count > max_votes:
                max_votes = count
            if count >= k:
                winner_val = val
                winner_models = models

        if winner_val is not None:
            return {"consensus": True, "value": winner_val,"votes": len(winner_models),"models": winner_models,}
        else:
            return {"consensus": False,"value": None,"votes": max_votes,"models": [],}

### 1.2 Comparison table : 2-3 vs 3-5

* **Fixed panel 2-3 ($n=3, k=2$)** : `openai/gpt-oss-120b` (Groq), `cohere/north-mini-code:free` (OpenRouter), `qwen/qwen3.8-27b` (Groq).
* **Quorum 3-5 ($n=5, k=3$)** : 3 last models + `openai/gpt-oss-20b` (Groq) + `dots-studio/dots-3-note-preview:free` (OpenRouter).

| Case | 2-of-3 Decision | 2/3 Votes | 2/3 Compliant? | 3-of-5 Decision | 3/5 Votes | 3/5 Compliant? | Decision Change / Observed Deviation |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **C01** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5) |
| **C02** | Consensus | 2/3 | Compliant | Consensus | 3/5 | Compliant | Shifted margin: 2/3 $\to$ 3/5 (Cohere & GPT-20b return 0; Dots votes 590,320) |
| **C03** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5) |
| **C04** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5) |
| **C05** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5) |
| **C06** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5; correct `COALESCE` on empty set) |
| **C07** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5) |
| **C08** | **Consensus** | **2/3** | **Compliant** | **Abstention** | **2/5** | **None** | **MAJOR CHANGE: Consensus $\to$ Abstention** (GPT-20b and Dots diverge on 25,920 and 523,000) |
| **C09** | Consensus | 2/3 | Compliant | Consensus | 3/5 | Compliant | Shifted margin: 2/3 $\to$ 3/5 (Qwen returns 0; GPT-20b secures the 3rd vote) |
| **C10** | Abstention | 1/3 | None | Abstention | 2/5 | None | Double abstention; 2 SQL errors in 2/3 (Cohere syntax, Qwen join) |
| **C11** | Consensus | 2/3 | Compliant | Consensus | 3/5 | Compliant | Shifted margin: 2/3 $\to$ 3/5 (Cohere and GPT-20b fail; Dots votes 446,690) |
| **C12** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5) |
| **C13** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5) |
| **C14** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 $\to$ 5/5) |
| **C15** | Abstention | 1/3 | None | Abstention | 2/5 | None | Double abstention; multiple dispersion (168,680 gets 2 votes < k=3) |
| **C16** | Consensus | 3/3 | Compliant | Consensus | 4/5 | Compliant | Shifted margin: 3/3 $\to$ 4/5 (Dots fails at 211,260) |
| **C17** | Abstention | 1/3 | None | Abstention | 2/5 | None | Double abstention; Dots SQL syntax error (`near "AS"`) |
| **C18** | Consensus | 3/3 | Compliant | Consensus | 4/5 | Compliant | Shifted margin: 3/3 $\to$ 4/5 (Dots fails at 39,580) |
| **C19** | Abstention | 1/3 | None | Abstention | 2/5 | None | Double abstention; 2/3 panel fails completely; GPT-20b and Dots have 1,990 (2 < 3) |
| **C20** | Consensus | 2/3 | Compliant | Consensus | 4/5 | Compliant | Shifted margin: 2/3 $\to$ 4/5; **Fault tolerance**: Qwen hit HTTP 429 |

### 1.3 Detailed Analysis of Deviations and Key Takeaways

1. **The C08 Tipping Point (Consensus Turning into Abstention):**
   - *Prompt*: Revenue from customers aged 25 or older as of 2026-09-24.
   - *Exact outputs*: `gpt-120b` = 605,580 (correct), `cohere` = 1,188,090 (incorrect), `qwen` = 605,580 (correct), `gpt-20b` = 25,920 (incorrect), `dots-3` = 523,000 (incorrect).
   - *Mechanism*: In the 2-of-3 panel, `gpt-120b` and `qwen` agree on the right date boundary, meeting the $k=2$ threshold. Scaling up to 5 models introduces two weaker models (`gpt-20b` and `dots-3`), both of which miscalculate the age condition and output different wrong numbers. As a result, the true value (`605,580`) only secures 2 out of 5 votes—falling short of the required k=3 threshold—forcing the 3-of-5 quorum to abstain.
   - *Takeaway*: Expanding a quorum with lower-capacity models increases the risk of vote splitting on complex temporal logic. The 3-of-5 setup favors safety and caution over availability.

2. **Infrastructure Resilience on C20 (Absorbing an HTTP 429 Error):**
   - *Trace*: `qwen/qwen3.8-27b` hits a tokens-per-minute rate limit (`http_status=429`, `verdict=not_executed`).
   - *Mechanism*: In the 2-of-3 setup, this leaves the panel vulnerable: only two models actually run (`gpt-120b` and `cohere`, both outputting `1,106,090`), barely clearing the $k=2$ threshold. In the 3-of-5 setup, `gpt-20b` and `dots-3` execute cleanly and also return `1,106,090`. The quorum reaches **4 out of 5 votes**, seamlessly absorbing Qwen's temporary outage.

3. **Filtering Out Malformed SQL Queries (C10 and C17):**
   - On C10, `cohere` throws a SQLite syntax error (`syntax_error near ")"`), while `qwen` hits a runtime error (`runtime_error no such column: p.price` due to a missing join on the `product` table).
   - On C17, `dots-3` generates invalid syntax (`syntax_error near "AS"`).
   - Because these queries fail prior to returning a result, they are excluded from voting (`verdict != "executed"`), preventing corrupted outputs from skewing the consensus.
---