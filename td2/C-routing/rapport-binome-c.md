# TD 2 — Step 3: Routing Rule and Simulator (Pair C)

## 1. Exact TD 1 Accuracy Rates by Question Family

Sources: [model-question-comparison-en.csv](../../td1/model-question-comparison-en.csv) and [questions-td1.json](../../kit-td1/questions-td1.json) (20-question batch `C01`–`C20`).

| Family | TD 1 Cells | `cohere/north-mini-code:free` | `dots-studio/dots-3-note-preview:free` | `openai/gpt-oss-120b` | `openai/gpt-oss-20b` | `qwen/qwen3.8-27b` |
|---|---|---|---|---|---|---|
| **F1** (period) | `C01, C04, C05, C06, C07, C20` | **6/6** (100%) | **6/6** (100%) | **6/6** (100%) | **6/6** (100%) | **5/6** (83%, `C20` HTTP 429) |
| **F2** (completed age at a date) | `C02, C08, C09, C11` | **1/4** (25%, err. `C02, C08, C11`) | **2/4** (50%, err. `C08, C09`) | **4/4** (100%) | **1/4** (25%, err. `C02, C08, C11`) | **3/4** (75%, err. `C09`) |
| **F2b** (age at order) | `C10` | **0/1** (0%, `sql_invalid`) | **0/1** (0%, err. `C10`) | **1/1** (100%) | **1/1** (100%) | **0/1** (0%, `sql_invalid`) |
| **F3** (product list) | `C03, C12, C13, C14` | **4/4** (100%) | **4/4** (100%) | **4/4** (100%) | **4/4** (100%) | **4/4** (100%) |
| **Combinations** | `C15, C16, C17, C18, C19` | **2/5** (40%, err. `C15, C17, C19`) | **1/5** (20%, err. `C15-C18`) | **4/5** (80%, err. `C19`) | **5/5** (100%) | **2/5** (40%, err. `C15, C17, C19`) |

---

## 2. Sub-group One-Page Routing Rule

> **Principle and limits:** simple questions (`F1`, `F3`) are kept as control cases to compare routing choices. Twenty questions support a batch-specific hypothesis for this TD 1 run, not a general error rate, a permanent ranking, or a quorum error guarantee.  
> **Consistency constraint:** calling a single free model with no check (`none`) is only admissible for a low-stakes internal dashboard **AND** on a family where that model achieved **100%** accuracy in TD 1. Whenever at least one error was observed on the family in TD 1, or whenever the figure is shown to a customer or governs a payout, a quorum or deterministic check is required.

| Family (Cells) | First Model Called (cheapest correct in TD 1) | Internal Dashboard | Figure Shown to Customer | Amount Paid Out (Payout) | Fallback if Unavailable (HTTP 429 / Quota) |
|---|---|---|---|---|---|
| **F1** (`C01, C04, C05, C06, C07, C20`) | `cohere/north-mini-code:free` (OpenRouter, free — 6/6) | **none** (100% TD 1 + low stakes) | **2-of-3 quorum** + read-only execution | **3-of-5 quorum** + reference / review | `dots-studio/dots-3-note-preview:free` → `openai/gpt-oss-120b` (Groq) → `defer` or `abstain` |
| **F3** (`C03, C12, C13, C14`) | `cohere/north-mini-code:free` (OpenRouter, free — 4/4) | **none** (100% TD 1 + low stakes) | **2-of-3 quorum** + read-only execution | **3-of-5 quorum** + reference / review | `dots-studio/dots-3-note-preview:free` → `qwen/qwen3.8-27b` → `defer` or `abstain` |
| **F2** (`C02, C08, C09, C11`) | `openai/gpt-oss-120b` (Groq, free — 4/4) | **2-of-3 quorum** (other free models fail on F2) | **3-of-5 quorum** | **3-of-5 quorum** + human review / reference | Subscription (`claude-sonnet-5#claude`) → `defer` if `can_wait` → paid API (`openai/gpt-oss-120b#openrouter`) → `abstain` |
| **F2b** (`C10`) | `openai/gpt-oss-120b` (Groq, free — 1/1) | **2-of-3 quorum** (only 1 case in TD 1; Cohere/Dots/Qwen fail) | **3-of-5 quorum** | **3-of-5 quorum** + human review / reference | `openai/gpt-oss-20b` (1/1) → subscription → `defer` → paid API → `abstain` |
| **Combinations** (`C15, C16, C17, C18, C19`) | `openai/gpt-oss-20b` (5/5) or `claude-sonnet-5#claude` (G2 subscription) | **2-of-3 quorum** (`gpt-oss-120b` fails on `C19`, other free models ≤ 40%) | **3-of-5 quorum** + SQL check | **3-of-5 quorum** + human review + reference | `defer` if `can_wait` (wait for refill) → paid API (`openai/gpt-oss-120b#openrouter`) → `abstain` |

---

## 3. Simulator Outputs (`kit-td1/atelier-routage.py`)

### Before Adaptation (`python3 atelier-routage.py`)
```json
{"scenario": "simple", "nature": "simulation", "request": {"difficulty": 1, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "small-free", "cash": 0, "checks": "read-only execution and value check", "reason": "eligible included capacity"}}
{"scenario": "complex", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "senior-subscription", "cash": 0, "checks": "read-only execution and value check", "reason": "eligible included capacity"}}
{"scenario": "deferrable", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "defer", "resource": "senior-subscription", "cash": 0, "checks": "read-only execution and value check", "reason": "recheck availability at wake-up", "wake_in_minutes": 60}}
{"scenario": "urgent", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 5, "budget": 0.3}, "result": {"action": "run", "resource": "senior-api", "cash": 0.3, "checks": "read-only execution and value check", "reason": "available route within the authorised budget"}}
{"scenario": "budget exhausted", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 120, "budget": 0}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "read-only execution and value check", "reason": "no eligible resource within deadline and budget"}}
{"scenario": "high impact", "nature": "simulation", "request": {"difficulty": 3, "high_impact": true, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "senior-subscription", "cash": 0, "checks": "source verification and human review", "reason": "eligible included capacity"}}
{"scenario": "unknown capability", "nature": "simulation", "request": {"difficulty": 4, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "read-only execution and value check", "reason": "no eligible resource within deadline and budget"}}
```

### After Adaptation (`kit-td1/atelier-routage.py` with adapted `RESOURCES` and `choose`)
```json
{"scenario": "simple", "nature": "simulation", "request": {"difficulty": 1, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "cohere/north-mini-code:free", "cash": 0, "checks": "none (100% TD1 on F1/F3 for internal dashboard) or read-only value check", "reason": "eligible included capacity [F1 6/6 (C01,C04-C07,C20), F3 4/4 (C03,C12-C14)]"}}
{"scenario": "complex", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "claude-sonnet-5#claude", "cash": 0, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "eligible included capacity [G2 subscription fallback for Combinaisons (C15-C19 where free models fail)]"}}
{"scenario": "deferrable", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "defer", "resource": "claude-sonnet-5#claude", "cash": 0, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "recheck availability at wake-up [G2 subscription fallback for Combinaisons (C15-C19 where free models fail)]", "wake_in_minutes": 60}}
{"scenario": "urgent", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 5, "budget": 0.3}, "result": {"action": "run", "resource": "openai/gpt-oss-120b#openrouter", "cash": 0.3, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "available route within authorised budget [Paid OpenRouter fallback when Groq/subscription unavailable (C15-C19)]"}}
{"scenario": "budget exhausted", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 120, "budget": 0}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "no eligible resource within deadline and budget (TD1: no free model 100% on C15-C19)"}}
{"scenario": "high impact", "nature": "simulation", "request": {"difficulty": 3, "high_impact": true, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "claude-sonnet-5#claude", "cash": 0, "checks": "quorum 3-of-5 + source verification and human review", "reason": "eligible included capacity [G2 subscription fallback for Combinaisons (C15-C19 where free models fail)]"}}
{"scenario": "unknown capability", "nature": "simulation", "request": {"difficulty": 4, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "quorum 2-of-3 + read-only SQL execution", "reason": "no eligible resource within deadline and budget (TD1: no free model 100% on C15-C19)"}}
```

---

## 4. Priority Order Analysis in `choose`

1. **Why an immediately available subscription resource (`cash == 0`, `allocation > 0`) is selected before deferring (`defer`) to wait for an exhausted free resource (`cash == 0`, `allocation == 0`) whose refill occurs before `deadline_minutes`:**  
   In `choose`, the first filter `included = [r for r in eligible if r["available"] and r["cash"] == 0]` groups all available resources with no direct cash spend (`cash == 0`), without separating free routes (`allocation == 0`) from subscriptions (`allocation > 0`). As soon as `included` is non-empty, the function returns `"action": "run"` immediately and never evaluates the `waiting` block that handles `defer`.
2. **Operational condition to reverse this priority:**  
   This priority should be reversed when the subscription quota (`allocation > 0`) is a **scarce resource to preserve for urgent or high-stakes requests** (`can_wait=False`, high impact) and the current request **can wait** (`can_wait=True`) for a free route (`allocation == 0`) to refill before `deadline_minutes`. Deferring non-urgent requests avoids burning limited subscription allowance unnecessarily.
