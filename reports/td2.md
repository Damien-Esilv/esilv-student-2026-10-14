# TD 2 Report — The Quorum and the Routing Rule

## Step 1 — The *k*-of-*n* Vote (Pair A)

### 1.1 Completed Method (`kit-td1/skeleton-multi-llm-en.py`)

```python
def vote_k_sur_n(self, traces_question: list, k: int):
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
```

### 1.2 Twenty-Question Comparison Table: 2-of-3 vs 3-of-5

* **Fixed 2-of-3 panel ($n=3, k=2$)**: `openai/gpt-oss-120b` (Groq), `cohere/north-mini-code:free` (OpenRouter), `qwen/qwen3.8-27b` (Groq).
* **3-of-5 quorum ($n=5, k=3$)**: the 3 models above + `openai/gpt-oss-20b` (Groq) + `dots-studio/dots-3-note-preview:free` (OpenRouter).

| Case | 2-of-3 Decision | 2/3 Votes | 2/3 Compliant? | 3-of-5 Decision | 3/5 Votes | 3/5 Compliant? | Decision Change / Observed Deviation |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **C01** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5) |
| **C02** | Consensus | 2/3 | Compliant | Consensus | 3/5 | Compliant | Shifted margin: 2/3 → 3/5 (Cohere & GPT-20B return 0; Dots votes 590,320) |
| **C03** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5) |
| **C04** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5) |
| **C05** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5) |
| **C06** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5; correct `COALESCE` on empty set) |
| **C07** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5) |
| **C08** | **Consensus** | **2/3** | **Compliant** | **Abstention** | **2/5** | **None** | **MAJOR CHANGE: Consensus → Abstention** (GPT-20B and Dots diverge on 25,920 and 523,000) |
| **C09** | Consensus | 2/3 | Compliant | Consensus | 3/5 | Compliant | Shifted margin: 2/3 → 3/5 (Qwen returns 0; GPT-20B secures the 3rd vote) |
| **C10** | Abstention | 1/3 | None | Abstention | 2/5 | None | Double abstention; 2 SQL errors in 2/3 (Cohere syntax, Qwen join) |
| **C11** | Consensus | 2/3 | Compliant | Consensus | 3/5 | Compliant | Shifted margin: 2/3 → 3/5 (Cohere and GPT-20B fail; Dots votes 446,690) |
| **C12** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5) |
| **C13** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5) |
| **C14** | Consensus | 3/3 | Compliant | Consensus | 5/5 | Compliant | Unchanged (Unanimity 3/3 → 5/5) |
| **C15** | Abstention | 1/3 | None | Abstention | 2/5 | None | Double abstention; dispersion (168,680 gets 2 votes < k=3) |
| **C16** | Consensus | 3/3 | Compliant | Consensus | 4/5 | Compliant | Shifted margin: 3/3 → 4/5 (Dots fails at 211,260) |
| **C17** | Abstention | 1/3 | None | Abstention | 2/5 | None | Double abstention; Dots SQL syntax error (`near "AS"`) |
| **C18** | Consensus | 3/3 | Compliant | Consensus | 4/5 | Compliant | Shifted margin: 3/3 → 4/5 (Dots fails at 39,580) |
| **C19** | Abstention | 1/3 | None | Abstention | 2/5 | None | Double abstention; 2/3 panel fails completely; GPT-20B and Dots have 1,990 (2 < 3) |
| **C20** | Consensus | 2/3 | Compliant | Consensus | 4/5 | Compliant | Shifted margin: 2/3 → 4/5; **Fault tolerance**: Qwen hit HTTP 429 |

### 1.3 Detailed Analysis of Deviations and Key Takeaways

1. **The C08 Tipping Point (Consensus Turning into Abstention):**
   - *Question*: revenue from customers aged 25 on 2026-09-24.
   - *Exact trace values*: `gpt-120b` = `605580` (correct), `cohere` = `1188090` (incorrect), `qwen` = `605580` (correct), `gpt-20b` = `25920` (incorrect), `dots-3` = `523000` (incorrect).
   - *Mechanism*: In the 2-of-3 panel, `gpt-120b` and `qwen` agree on the right date boundary, meeting $k=2$. Moving to 5 models adds `gpt-20b` and `dots-3`, which both miscalculate the age condition and return distinct wrong values. The true value `605580` only gathers 2 votes out of 5 (< $k=3$), so the 3-of-5 quorum **abstains**.
   - *Takeaway*: Expanding a quorum with weaker models increases vote dispersion on complex temporal conditions. The 3-of-5 setup favors safety over availability.

2. **Infrastructure Resilience on C20 (Absorbing an HTTP 429 Error):**
   - *Trace*: `qwen/qwen3.8-27b` hits a tokens-per-minute rate limit (`http_status=429`, `verdict=not_executed`).
   - *Mechanism*: In 2-of-3, only two models run (`gpt-120b` and `cohere` at `1106090`), barely clearing $k=2$. In 3-of-5, `gpt-20b` and `dots-3` execute cleanly and also vote `1106090`. The quorum reaches **4 votes out of 5**, absorbing Qwen's temporary outage.

3. **Filtering Out Malformed SQL Queries (C10 and C17):**
   - On C10, `cohere` throws a SQLite syntax error (`syntax_error near ")"`), while `qwen` hits a runtime error (`runtime_error no such column: p.price` due to a missing join on `product`).
   - On C17, `dots-3` generates invalid syntax (`syntax_error near "AS"`).
   - Because these queries fail before returning a value, they do not vote (`verdict != "executed"`), preventing corrupted outputs from skewing the consensus.

4. **Simple Control Questions (F1 and F3):**
   - 100% unanimity (5/5) on the 9 pure period and product-list questions (`C01, C03, C04, C05, C06, C07, C12, C13, C14`), confirming Pair C's routing choice to use a fast free model without heavy checking for low-stakes internal dashboards.

---

## Step 2 — SQL Wrong Consensus (Pair B)

### 2.1 Case Studied and Results

Question **C02** asks for the total revenue excluding VAT, in euro cents, across **all orders placed by customers who are exactly 25 years old on 25 September 2026**. This case comes from our TD 1 batch of 21 October 2026 (`nature=real`). The stored queries were re-executed locally on `kit-td1/data/boutique.sqlite` with no new model calls.

The C02 reference value in [reference-td1.csv](../kit-td1/reference-td1.csv) is **590,320 cents**. The five retained answers are:

| Provider and Model | Value (cents) | Verdict | Source Trace in `td1/raw-traces` |
|---|---:|---|---|
| Groq / `openai/gpt-oss-120b` | 590,320 | correct | `traces-gpt120b-C01-C20.csv` |
| OpenRouter / `cohere/north-mini-code:free` | 0 | incorrect | `traces-C.csv` |
| Groq / `qwen/qwen3.8-27b` | 590,320 | correct | `traces-D.csv` |
| Groq / `openai/gpt-oss-20b` | 0 | incorrect | `traces-gpt20b-C01-C20.csv` |
| OpenRouter / `dots-studio/dots-3-note-preview:free` | 590,320 | correct | `traces-E.csv` |

All five C02 cells appear in [traces-td1.csv](../kit-td1/traces-td1.csv). For Dots, we retain the main batch `traces-E.csv`, consistent with the [TD 1 comparison table](../td1/model-question-comparison-en.csv).

**GPT-OSS 20B** and **Cohere** share the exact same wrong value, **0**, with a gap of **590,320 cents** from the reference.

### 2.2 SQL Queries and Root Causes

**GPT-OSS 20B** — cell `groq:openai/gpt-oss-20b:C02`, attempt 1, in [traces-gpt20b-C01-C20.csv](../td1/raw-traces/traces-gpt20b-C01-C20.csv). Original query:

```sql
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE c.birth_date > '2025-09-25' AND c.birth_date <= '2026-09-25';
```

The filter selects people born in the year preceding 25 September 2026 instead of customers aged 25. The correct window is **`2000-09-25 < birth_date <= 2001-09-25`**: the lower bound excludes customers already aged 26, while the upper bound includes those turning 25 on that day. No customer matches the faulty filter; the query runs without error and `COALESCE` returns **0**.

**Cohere** — cell `openrouter:cohere/north-mini-code:free:C02`, attempt 1, in [traces-C.csv](../td1/raw-traces/traces-C.csv). Original query:

```sql
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE c.birth_date <= '2026-09-25' AND c.birth_date > date('2026-09-25', '-26 years')
AND c.birth_date <= date('2026-09-25', '-25 years') AND c.birth_date > date('2026-09-25', '-26 years')
AND o.date >= '2026-09-25 00:00:00' AND o.date < '2027-09-25 00:00:00';
```

The age filter is correct despite repeated conditions. The bug is adding the two `o.date` restrictions: C02 asks for **all orders**, without a period filter. Since the latest order in the database is on **20 September 2026 at 19:24:25**, no order matches the added period and the query also returns **0**.

Both models return the same wrong value for **two different reasons**: a wrong birth-date window and a spurious order-date filter.

### 2.3 Delta Diagnostic SQL Query and Independent Check

Both faulty queries select zero rows, so the missed amounts correspond to all orders of customers truly aged 25 on `2026-09-25`. The [delta diagnostic query](../td2/B-consensus/diagnostic-c02.sql), executed on `kit-td1/data/boutique.sqlite`, lists these customers and their revenue excluding VAT:

```sql
SELECT c.customer_id,
       c.birth_date,
       SUM(o.quantity_product * p.price) AS revenue_cents
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE c.birth_date > '2000-09-25'
  AND c.birth_date <= '2001-09-25'
GROUP BY c.customer_id, c.birth_date
ORDER BY c.customer_id;
```

| Customer | Birth Date | Revenue Missed by Both Models (cents) |
|---|---|---:|
| `C001` | `2001-09-25` | 135,000 |
| `C002` | `2001-09-24` | 25,920 |
| `C005` | `2000-09-26` | 150,240 |
| `C007` | `2000-11-30` | 118,740 |
| `C008` | `2001-05-15` | 99,090 |
| `C009` | `2001-03-10` | 61,330 |
| **Total** | | **590,320** |

These six customers account for the exact gap for both models: **590,320 - 0 = 590,320 cents**. No rows are wrongly added by either query; all differences are omissions.

**Independent check:** a Python calculation directly over `customers.csv`, `orders.csv`, and `product.csv`, without running SQL, reproduces the exact same per-customer amounts and total.

### 2.4 Quorums and Verification with Pair A

| Declared Panel | Threshold | Votes for `590,320` | Votes for `0` | Decision Confirmed with Pair A's Code |
|---|---:|---:|---:|---|
| `gpt-oss-120b`, `cohere`, `qwen` | 2 of 3 | 2 | 1 | Consensus on `590,320`, correct |
| All five TD 1 models above | 3 of 5 | 3 | 2 | Consensus on `590,320`, correct |

In 2-of-3, `gpt-oss-120b` and `qwen` vote for the right value; in 3-of-5, `dots-3` provides the third vote. **The wrong agreement between `gpt-oss-20b` and `cohere` is outvoted in both configurations.**

**Verification with Pair A (18 November 2026):** running `atelier-vote.py --traces traces-td1.csv --case C02 --panel 3` and `--panel 5` reproduces our manual counts (`consensus: true`, `value: 590320`, `votes: 2` for 2-of-3; `votes: 3` for 3-of-5; `matches_reference: true`). This demonstrates that two models can agree on the same wrong value from completely different SQL mistakes, and why independent data/filter checks remain essential.

---

## Step 3 — Routing Rule and Simulator (Pair C)

### 3.1 Exact TD 1 Accuracy Rates by Question Family

Sources: [model-question-comparison-en.csv](../td1/model-question-comparison-en.csv) and [questions-td1.json](../kit-td1/questions-td1.json) (20-question batch `C01`–`C20`).

| Family | TD 1 Cells | `cohere/north-mini-code:free` | `dots-studio/dots-3-note-preview:free` | `openai/gpt-oss-120b` | `openai/gpt-oss-20b` | `qwen/qwen3.8-27b` |
|---|---|---|---|---|---|---|
| **F1** (period) | `C01, C04, C05, C06, C07, C20` | **6/6** (100%) | **6/6** (100%) | **6/6** (100%) | **6/6** (100%) | **5/6** (83%, `C20` HTTP 429) |
| **F2** (completed age at a date) | `C02, C08, C09, C11` | **1/4** (25%, err. `C02, C08, C11`) | **2/4** (50%, err. `C08, C09`) | **4/4** (100%) | **1/4** (25%, err. `C02, C08, C11`) | **3/4** (75%, err. `C09`) |
| **F2b** (age at order) | `C10` | **0/1** (0%, `sql_invalid`) | **0/1** (0%, err. `C10`) | **1/1** (100%) | **1/1** (100%) | **0/1** (0%, `sql_invalid`) |
| **F3** (product list) | `C03, C12, C13, C14` | **4/4** (100%) | **4/4** (100%) | **4/4** (100%) | **4/4** (100%) | **4/4** (100%) |
| **Combinations** | `C15, C16, C17, C18, C19` | **2/5** (40%, err. `C15, C17, C19`) | **1/5** (20%, err. `C15-C18`) | **4/5** (80%, err. `C19`) | **5/5** (100%) | **2/5** (40%, err. `C15, C17, C19`) |

### 3.2 Sub-group One-Page Routing Rule

> **Principle and limits:** simple questions (`F1`, `F3`) are kept as control cases to compare routing choices. Twenty questions support a batch-specific hypothesis for this TD 1 run, not a general error rate, a permanent ranking, or a quorum error guarantee.  
> **Consistency constraint:** calling a single free model with no check (`none`) is only admissible for a low-stakes internal dashboard **AND** on a family where that model achieved **100%** accuracy in TD 1. Whenever at least one error was observed on the family in TD 1, or whenever the figure is shown to a customer or governs a payout, a quorum or deterministic check is required.

| Family (Cells) | First Model Called (cheapest correct in TD 1) | Internal Dashboard | Figure Shown to Customer | Amount Paid Out (Payout) | Fallback if Unavailable (HTTP 429 / Quota) |
|---|---|---|---|---|---|
| **F1** (`C01, C04, C05, C06, C07, C20`) | `cohere/north-mini-code:free` (OpenRouter, free — 6/6) | **none** (100% TD 1 + low stakes) | **2-of-3 quorum** + read-only execution | **3-of-5 quorum** + reference / review | `dots-studio/dots-3-note-preview:free` → `openai/gpt-oss-120b` (Groq) → `defer` or `abstain` |
| **F3** (`C03, C12, C13, C14`) | `cohere/north-mini-code:free` (OpenRouter, free — 4/4) | **none** (100% TD 1 + low stakes) | **2-of-3 quorum** + read-only execution | **3-of-5 quorum** + reference / review | `dots-studio/dots-3-note-preview:free` → `qwen/qwen3.8-27b` → `defer` or `abstain` |
| **F2** (`C02, C08, C09, C11`) | `openai/gpt-oss-120b` (Groq, free — 4/4) | **2-of-3 quorum** (other free models fail on F2) | **3-of-5 quorum** | **3-of-5 quorum** + human review / reference | Subscription (`claude-sonnet-5#claude`) → `defer` if `can_wait` → paid API (`openai/gpt-oss-120b#openrouter`) → `abstain` |
| **F2b** (`C10`) | `openai/gpt-oss-120b` (Groq, free — 1/1) | **2-of-3 quorum** (only 1 case in TD 1; Cohere/Dots/Qwen fail) | **3-of-5 quorum** | **3-of-5 quorum** + human review / reference | `openai/gpt-oss-20b` (1/1) → subscription → `defer` → paid API → `abstain` |
| **Combinations** (`C15, C16, C17, C18, C19`) | `openai/gpt-oss-20b` (5/5) or `claude-sonnet-5#claude` (G2 subscription) | **2-of-3 quorum** (`gpt-oss-120b` fails on `C19`, other free models ≤ 40%) | **3-of-5 quorum** + SQL check | **3-of-5 quorum** + human review + reference | `defer` if `can_wait` (wait for refill) → paid API (`openai/gpt-oss-120b#openrouter`) → `abstain` |

### 3.3 Simulator Outputs (`kit-td1/atelier-routage.py`)

#### Before Adaptation (`python3 atelier-routage.py`)
```json
{"scenario": "simple", "nature": "simulation", "request": {"difficulty": 1, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "small-free", "cash": 0, "checks": "read-only execution and value check", "reason": "eligible included capacity"}}
{"scenario": "complex", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "senior-subscription", "cash": 0, "checks": "read-only execution and value check", "reason": "eligible included capacity"}}
{"scenario": "deferrable", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "defer", "resource": "senior-subscription", "cash": 0, "checks": "read-only execution and value check", "reason": "recheck availability at wake-up", "wake_in_minutes": 60}}
{"scenario": "urgent", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 5, "budget": 0.3}, "result": {"action": "run", "resource": "senior-api", "cash": 0.3, "checks": "read-only execution and value check", "reason": "available route within the authorised budget"}}
{"scenario": "budget exhausted", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 120, "budget": 0}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "read-only execution and value check", "reason": "no eligible resource within deadline and budget"}}
{"scenario": "high impact", "nature": "simulation", "request": {"difficulty": 3, "high_impact": true, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "senior-subscription", "cash": 0, "checks": "source verification and human review", "reason": "eligible included capacity"}}
{"scenario": "unknown capability", "nature": "simulation", "request": {"difficulty": 4, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "read-only execution and value check", "reason": "no eligible resource within deadline and budget"}}
```

#### After Adaptation (`kit-td1/atelier-routage.py` with adapted `RESOURCES` and `choose`)
```json
{"scenario": "simple", "nature": "simulation", "request": {"difficulty": 1, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "cohere/north-mini-code:free", "cash": 0, "checks": "none (100% TD1 on F1/F3 for internal dashboard) or read-only value check", "reason": "eligible included capacity [F1 6/6 (C01,C04-C07,C20), F3 4/4 (C03,C12-C14)]"}}
{"scenario": "complex", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "claude-sonnet-5#claude", "cash": 0, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "eligible included capacity [G2 subscription fallback for Combinaisons (C15-C19 where free models fail)]"}}
{"scenario": "deferrable", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "defer", "resource": "claude-sonnet-5#claude", "cash": 0, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "recheck availability at wake-up [G2 subscription fallback for Combinaisons (C15-C19 where free models fail)]", "wake_in_minutes": 60}}
{"scenario": "urgent", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 5, "budget": 0.3}, "result": {"action": "run", "resource": "openai/gpt-oss-120b#openrouter", "cash": 0.3, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "available route within authorised budget [Paid OpenRouter fallback when Groq/subscription unavailable (C15-C19)]"}}
{"scenario": "budget exhausted", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 120, "budget": 0}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "no eligible resource within deadline and budget (TD1: no free model 100% on C15-C19)"}}
{"scenario": "high impact", "nature": "simulation", "request": {"difficulty": 3, "high_impact": true, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "claude-sonnet-5#claude", "cash": 0, "checks": "quorum 3-of-5 + source verification and human review", "reason": "eligible included capacity [G2 subscription fallback for Combinaisons (C15-C19 where free models fail)]"}}
{"scenario": "unknown capability", "nature": "simulation", "request": {"difficulty": 4, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "no eligible resource within deadline and budget (TD1: no free model 100% on C15-C19)"}}
```

### 3.4 Priority Order Analysis in `choose`

1. **Why an immediately available subscription resource (`cash == 0`, `allocation > 0`) is selected before deferring (`defer`) to wait for an exhausted free resource (`cash == 0`, `allocation == 0`) whose refill occurs before `deadline_minutes`:**  
   In `choose`, the first filter `included = [r for r in eligible if r["available"] and r["cash"] == 0]` groups all available resources with no direct cash spend (`cash == 0`), without separating free routes (`allocation == 0`) from subscriptions (`allocation > 0`). As soon as `included` is non-empty, the function returns `"action": "run"` immediately and never evaluates the `waiting` block that handles `defer`.
2. **Operational condition to reverse this priority:**  
   This priority should be reversed when the subscription quota (`allocation > 0`) is a **scarce resource to preserve for urgent or high-stakes requests** (`can_wait=False`, high impact) and the current request **can wait** (`can_wait=True`) for a free route (`allocation == 0`) to refill before `deadline_minutes`. Deferring non-urgent requests avoids burning limited subscription allowance unnecessarily.

---

## Prompts, Limitations, Contributions, and Next Steps

* **Prompts:** unchanged since TD 1 (`SYSTEM_PROMPT` and `USER_PROMPT_TEMPLATE` in `kit-td1/skeleton-multi-llm-en.py`).
* **Limitations:** all measurements come from the 20-question TD 1 batch (`traces-td1.csv`), which supports batch-specific hypotheses rather than general error rates or permanent rankings; `atelier-routage.py` uses simulated availability scenarios.
* **Pair A:** implemented strict $k$-of-$n$ voting in `skeleton-multi-llm-en.py`, added multi-panel support to `atelier-vote.py`, built the 20-question 2-of-3 vs 3-of-5 comparison table, and analysed deviations (`C08`, `C20` HTTP 429, `C10`/`C17` SQL errors, `F1`/`F3` unanimity).
* **Pair B:** identified the `C02` wrong agreement between `gpt-oss-20b` and `cohere`, diagnosed both distinct SQL root causes, ran the delta query on `data/boutique.sqlite` with an independent CSV check, and verified 2-of-3 / 3-of-5 quorums with Pair A's code.
* **Pair C:** computed exact TD 1 accuracy rates per family (`F1`, `F2`, `F2b`, `F3`, `Combinations`), wrote the one-page routing rule, adapted `kit-td1/atelier-routage.py`, and analysed the priority order in `choose`.
* **Next steps (TD 3):** price each configuration (single model, 2-of-3, 3-of-5, escalation) using dated portfolio rates and select the final architecture for a named use case.
