# TD 2 — Step 2: SQL Wrong Consensus (Pair B)

## Case Studied and Results

Question **C02** asks for the total revenue excluding VAT, in euro cents, across **all orders placed by customers who are exactly 25 years old on 25 September 2026**. This case comes from our TD 1 batch of 21 October 2026, whose traces are labelled `real`. The stored queries were re-executed locally on `kit-td1/data/boutique.sqlite`, with no new calls to the models.

The C02 reference value in [reference-td1.csv](../../kit-td1/reference-td1.csv) is **590,320 cents**. The five retained answers are:

| Provider and Model | Value (cents) | Verdict | Source Trace in `td1/raw-traces` |
|---|---:|---|---|
| Groq / `openai/gpt-oss-120b` | 590,320 | correct | `traces-gpt120b-C01-C20.csv` |
| OpenRouter / `cohere/north-mini-code:free` | 0 | incorrect | `traces-C.csv` |
| Groq / `qwen/qwen3.8-27b` | 590,320 | correct | `traces-D.csv` |
| Groq / `openai/gpt-oss-20b` | 0 | incorrect | `traces-gpt20b-C01-C20.csv` |
| OpenRouter / `dots-studio/dots-3-note-preview:free` | 590,320 | correct | `traces-E.csv` |

All five C02 cells appear in [traces-td1.csv](../../kit-td1/traces-td1.csv). For Dots, we retain the main batch `traces-E.csv`, consistent with the [TD 1 comparison table](../../td1/model-question-comparison-en.csv).

**GPT-OSS 20B** and **Cohere** therefore share the exact same wrong value, **0**, with a gap of **590,320 cents** from the reference.

---

## SQL Queries and Root Causes

**GPT-OSS 20B** — cell `groq:openai/gpt-oss-20b:C02`, attempt 1, in [traces-gpt20b-C01-C20.csv](../../td1/raw-traces/traces-gpt20b-C01-C20.csv). Original query:

```sql
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE c.birth_date > '2025-09-25' AND c.birth_date <= '2026-09-25';
```

The filter selects people born in the year preceding 25 September 2026, instead of customers aged 25. The correct birth-date window is **`2000-09-25 < birth_date <= 2001-09-25`**: the lower bound excludes customers who have already turned 26, while the upper bound includes those turning 25 on that day. No customer matches the faulty filter. The query runs without error, and `COALESCE` turns the empty sum into **0**.

**Cohere** — cell `openrouter:cohere/north-mini-code:free:C02`, attempt 1, in [traces-C.csv](../../td1/raw-traces/traces-C.csv). Original query:

```sql
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE c.birth_date <= '2026-09-25' AND c.birth_date > date('2026-09-25', '-26 years')
AND c.birth_date <= date('2026-09-25', '-25 years') AND c.birth_date > date('2026-09-25', '-26 years')
AND o.date >= '2026-09-25 00:00:00' AND o.date < '2027-09-25 00:00:00';
```

The age filter is correct despite redundant conditions. The mistake is adding the two `o.date` period restrictions: C02 asks for **all orders**, with no date filter. The latest order in the database is dated **20 September 2026 at 19:24:25**, so no order matches the extra period filter. This query also returns **0**.

Both models return the same wrong value for **two different reasons**: an invalid birth-date window and a spurious order-date filter.

---

## Delta Diagnostic SQL Query and Independent Check

Both faulty queries select zero rows. The missed amounts therefore correspond to all orders of the customers who are truly aged 25 on `2026-09-25`. The [delta diagnostic query](diagnostic-c02.sql), executed on `kit-td1/data/boutique.sqlite`, lists these exact customers and their revenue excluding VAT:

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

**Independent check:** a Python calculation directly over `customers.csv`, `orders.csv`, and `product.csv`, without running SQL, reproduces the exact same per-customer amounts and total. It computes completed age from year difference adjusted by whether the birthday has passed, then sums `quantity * price` over all orders of 25-year-old customers.

---

## Quorums and Verification with Pair A

The vote count uses the retained model answers without filtering out `incorrect` verdicts. The reference is used only after the decision to evaluate correctness.

| Declared Panel | Threshold | Votes for `590,320` | Votes for `0` | Decision Confirmed with Pair A's Code |
|---|---:|---:|---:|---|
| `gpt-oss-120b`, `cohere`, `qwen` | 2 of 3 | 2 | 1 | Consensus on `590,320`, correct |
| All five TD 1 models above | 3 of 5 | 3 | 2 | Consensus on `590,320`, correct |

In the 2-of-3 panel, `gpt-oss-120b` and `qwen` return the right value. In the 3-of-5 quorum, `dots-3` provides the third vote for that value. **The wrong agreement between `gpt-oss-20b` and `cohere` is therefore outvoted in both configurations.** Moving from 2-of-3 to 3-of-5 does not change the selected value on C02.

**Verification with Pair A completed on 18 November 2026.** `Orchestrateur.vote_k_sur_n` was run on C02 for both panels from `kit-td1/`:

```bash
python3 atelier-vote.py --traces traces-td1.csv --case C02 --panel 3
python3 atelier-vote.py --traces traces-td1.csv --case C02 --panel 5
```

Both outputs match our manual count: `consensus: true`, `value: 590320`, `votes: 2` for 2-of-3; `consensus: true`, `value: 590320`, `votes: 3` for 3-of-5, with `matches_reference: true`.

This case shows that two models can agree on the exact same wrong value without even sharing the same SQL bug. Here both quorums recover the right answer, but consensus alone never guarantees correctness on other questions; independent data and filter checks remain necessary.
