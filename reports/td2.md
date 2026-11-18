# Rapport TD 2 — Quorum et règle de routage
## Étape 1 — Vote *k*-sur-*n* (Binôme A)

### 1.1 Completed Method

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

### 1.3 Analyse détaillée des écarts et enseignements

1. **Le cas de bascule C08 (Consensus transformé en Abstention) :**
   - *Question* : chiffre d'affaires des clients ayant 25 ans révolus au 2026-09-24.
   - *Traces exactes* : `gpt-120b` = 605 580 (correct), `cohere` = 1 188 090 (incorrect), `qwen` = 605 580 (correct), `gpt-20b` = 25 920 (incorrect), `dots-3` = 523 000 (incorrect).
   - *Mécanisme* : Dans le panel 2-sur-3, `gpt-120b` et `qwen` s'accordent sur la borne de date correcte, atteignant le seuil $k=2$. En passant à 5 modèles, les deux modèles ajoutés (`gpt-20b` et `dots-3`) échouent tous deux sur le calcul d'âge et renvoient des valeurs erronées différentes. La valeur exacte `605 580` ne rassemble que 2 voix sur 5, ce qui est strictement inférieur au seuil requis $k=3$. Le quorum 3-sur-5 **s'abstient**.
   - *Enseignement* : Élargir un quorum à des modèles de moindre capacité augmente le risque de dispersion des voix sur des conditions temporelles complexes. Le quorum 3-sur-5 privilégie la prudence et la sécurité au détriment de la disponibilité.

2. **Résilience infrastructurelle sur C20 (Absorption d'une erreur HTTP 429) :**
   - *Trace* : `qwen/qwen3.8-27b` subit un dépassement de quota tokens/minute (`http_status=429`, `verdict=not_executed`).
   - *Mécanisme* : En 2-sur-3, le panel est fragilisé : seuls 2 modèles s'exécutent (`gpt-120b` et `cohere` à `1 106 090`), atteignant de justesse le seuil $k=2$. En 3-sur-5, `gpt-20b` et `dots-3` s'exécutent avec succès et votent également `1 106 090`. Le quorum atteint **4 voix sur 5**, absorbant l'indisponibilité temporaire de Qwen sans vaciller.

3. **Filtrage des requêtes SQL malformées (C10 et C17) :**
   - Sur C10, `cohere` génère une erreur de syntaxe SQLite (`syntax_error near ")"`) et `qwen` une erreur d'exécution (`runtime_error no such column: p.price` car la table `product` n'a pas été jointe).
   - Sur C17, `dots-3` produit une syntaxe invalide (`syntax_error near "AS"`).
   - Ces requêtes échouent avant résultat et ne votent pas (`verdict != "executed"`), évitant toute corruption du vote.

4. **Questions simples témoins (F1 et F3) :**
   - 100 % d'unanimité (5/5) sur les 9 questions de période pure et de liste de produits (`C01, C03, C04, C05, C06, C07, C12, C13, C14`).
   - Confirme la règle de routage du Binôme C : pour F1 et F3, un modèle gratuit rapide sans vérification lourde suffit pour les usages internes.

---

## Étape 2 — Faux consensus SQL (Binôme B)

*(À compléter par le Binôme B : cas identifié dans `traces-td1.csv` ou `DEMO-SQL-C11`, verdict des quorums 2-sur-3 et 3-sur-5, diagnostic des clauses SQL fautives et requête delta sur `data/boutique.sqlite`.)*

---

## Étape 3 — Règle de routage et simulateur (Binôme C)

### 3.1 Taux exacts de TD 1 par famille de questions

Sources : `kit-td1/model-question-comparison-en.csv` et `kit-td1/questions-td1.json` (lot de 20 questions `C01`–`C20`).

| Famille | Cellules TD 1 | `cohere/north-mini-code:free` | `dots-studio/dots-3-note-preview:free` | `openai/gpt-oss-120b` | `openai/gpt-oss-20b` | `qwen/qwen3.8-27b` |
|---|---|---|---|---|---|---|
| **F1** (période) | `C01, C04, C05, C06, C07, C20` | **6/6** (100 %) | **6/6** (100 %) | **6/6** (100 %) | **6/6** (100 %) | **5/6** (83 %, `C20` HTTP 429) |
| **F2** (âge révolu à une date) | `C02, C08, C09, C11` | **1/4** (25 %, err. `C02, C08, C11`) | **2/4** (50 %, err. `C08, C09`) | **4/4** (100 %) | **1/4** (25 %, err. `C02, C08, C11`) | **3/4** (75 %, err. `C09`) |
| **F2b** (âge à la commande) | `C10` | **0/1** (0 %, `sql_invalid`) | **0/1** (0 %, err. `C10`) | **1/1** (100 %) | **1/1** (100 %) | **0/1** (0 %, `sql_invalid`) |
| **F3** (liste de produits) | `C03, C12, C13, C14` | **4/4** (100 %) | **4/4** (100 %) | **4/4** (100 %) | **4/4** (100 %) | **4/4** (100 %) |
| **Combinaisons** | `C15, C16, C17, C18, C19` | **2/5** (40 %, err. `C15, C17, C19`) | **1/5** (20 %, err. `C15-C18`) | **4/5** (80 %, err. `C19`) | **5/5** (100 %) | **2/5** (40 %, err. `C15, C17, C19`) |

---

### 3.2 Règle de routage du sous-groupe (1 page)

> **Principe et limites** : les questions simples (`F1`, `F3`) sont conservées comme témoins pour comparer les choix de routage. Vingt questions soutiennent une hypothèse propre à ce lot TD 1, et non un taux d'erreur général, un classement permanent ou une garantie d'absence d'erreur du quorum.  
> **Contrainte de cohérence** : appeler un seul modèle gratuit sans vérification (`none`) n'est admissible que pour un tableau de bord interne à faible enjeu **ET** sur une famille où ce modèle a obtenu **100 %** en TD 1. Dès qu'une erreur a été observée sur la famille en TD 1, ou que le chiffre est affiché au client / gouverne un paiement, un quorum ou une vérification déterministe est exigé.

| Famille (Cellules) | 1er modèle appelé (moins cher correct en TD 1) | Tableau de bord interne | Chiffre affiché au client | Montant versé (paiement) | Repli si indisponible (HTTP 429 / quota) |
|---|---|---|---|---|---|
| **F1** (`C01, C04, C05, C06, C07, C20`) | `cohere/north-mini-code:free` (OpenRouter, gratuit — 6/6) | **none** (100 % TD 1 + faible enjeu) | **quorum 2-of-3** + exécution lecture seule | **quorum 3-of-5** + référence / revue | `dots-studio/dots-3-note-preview:free` → `openai/gpt-oss-120b` (Groq) → `defer` ou `abstain` |
| **F3** (`C03, C12, C13, C14`) | `cohere/north-mini-code:free` (OpenRouter, gratuit — 4/4) | **none** (100 % TD 1 + faible enjeu) | **quorum 2-of-3** + exécution lecture seule | **quorum 3-of-5** + référence / revue | `dots-studio/dots-3-note-preview:free` → `qwen/qwen3.8-27b` → `defer` ou `abstain` |
| **F2** (`C02, C08, C09, C11`) | `openai/gpt-oss-120b` (Groq, gratuit — 4/4) | **quorum 2-of-3** (les autres gratuits échouent sur F2) | **quorum 3-of-5** | **quorum 3-of-5** + revue humaine / référence | Abonnement (`claude-sonnet-5#claude`) → `defer` si `can_wait` → API payante (`openai/gpt-oss-120b#openrouter`) → `abstain` |
| **F2b** (`C10`) | `openai/gpt-oss-120b` (Groq, gratuit — 1/1) | **quorum 2-of-3** (1 seul cas en TD 1 ; Cohere/Dots/Qwen échouent) | **quorum 3-of-5** | **quorum 3-of-5** + revue humaine / référence | `openai/gpt-oss-20b` (1/1) → abonnement → `defer` → API payante → `abstain` |
| **Combinaisons** (`C15, C16, C17, C18, C19`) | `openai/gpt-oss-20b` (5/5) ou `claude-sonnet-5#claude` (abonnement G2) | **quorum 2-of-3** (`gpt-oss-120b` échoue sur `C19`, autres gratuits ≤ 40 %) | **quorum 3-of-5** + vérification SQL | **quorum 3-of-5** + revue humaine + référence | `defer` si `can_wait` (attente rechargement) → API payante (`openai/gpt-oss-120b#openrouter`) → `abstain` |

---

### 3.3 Sorties du simulateur (`atelier-routage.py`)

#### Avant adaptation (`python atelier-routage.py`)
```json
{"scenario": "simple", "nature": "simulation", "request": {"difficulty": 1, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "small-free", "cash": 0, "checks": "read-only execution and value check", "reason": "eligible included capacity"}}
{"scenario": "complex", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "senior-subscription", "cash": 0, "checks": "read-only execution and value check", "reason": "eligible included capacity"}}
{"scenario": "deferrable", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "defer", "resource": "senior-subscription", "cash": 0, "checks": "read-only execution and value check", "reason": "recheck availability at wake-up", "wake_in_minutes": 60}}
{"scenario": "urgent", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 5, "budget": 0.3}, "result": {"action": "run", "resource": "senior-api", "cash": 0.3, "checks": "read-only execution and value check", "reason": "available route within the authorised budget"}}
{"scenario": "budget exhausted", "nature": "simulation", "request": {"difficulty": 3, "high_impact": false, "can_wait": false, "deadline_minutes": 120, "budget": 0}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "read-only execution and value check", "reason": "no eligible resource within deadline and budget"}}
{"scenario": "high impact", "nature": "simulation", "request": {"difficulty": 3, "high_impact": true, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "run", "resource": "senior-subscription", "cash": 0, "checks": "source verification and human review", "reason": "eligible included capacity"}}
{"scenario": "unknown capability", "nature": "simulation", "request": {"difficulty": 4, "high_impact": false, "can_wait": true, "deadline_minutes": 120, "budget": 0.3}, "result": {"action": "abstain", "resource": null, "cash": 0, "checks": "read-only execution and value check", "reason": "no eligible resource within deadline and budget"}}
```

#### Après adaptation (`kit-td1/atelier-routage.py` avec `RESOURCES` et `choose` adaptés)
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

### 3.4 Analyse de l'ordre de priorité dans `choose`

1. **Pourquoi une ressource d'abonnement immédiatement disponible (`cash == 0`, `allocation > 0`) est choisie avant de différer (`defer`) sur une ressource gratuite épuisée (`cash == 0`, `allocation == 0`) dont le rechargement a lieu avant `deadline_minutes` :**  
   Dans `choose`, le premier filtre `included = [r for r in eligible if r["available"] and r["cash"] == 0]` regroupe toutes les ressources disponibles sans dépense directe (`cash == 0`), sans séparer les routes gratuites (`allocation == 0`) des abonnements (`allocation > 0`). Dès que `included` est non vide, la fonction exécute un `return` immédiat (`"action": "run"`) et n'évalue jamais le bloc `waiting` qui gère le `defer`.
2. **Condition opérationnelle pour inverser cette priorité :**  
   Cette priorité doit être inversée lorsque le quota d'abonnement (`allocation > 0`) est une **ressource rare à préserver pour des requêtes urgentes ou complexes** (`can_wait=False`, fort enjeu) et que la requête courante **peut attendre** (`can_wait=True`) le rechargement d'une route gratuite (`allocation == 0`) prévu avant `deadline_minutes`. Dans ce cas, différer la requête non urgente évite de consommer inutilement l'enveloppe d'abonnement.

---

## Contributions et suite

- **Binôme A** : Implémentation du vote strict $k$-sur-$n$ dans `skeleton-multi-llm-en.py`, support multi-panel dans `atelier-vote.py`, tableau comparatif complet 2-sur-3 vs 3-sur-5 sur les 20 questions TD 1, analyse détaillée des écarts (bascule C08, résilience HTTP 429 sur C20, gestion des erreurs SQL C10/C17).
- **Binôme B** : *(à compléter)*
- **Binôme C** : Calcul des taux TD 1 par famille (`F1`, `F2`, `F2b`, `F3`, `Combinaisons`), rédaction de la règle de routage, adaptation de `kit-td1/atelier-routage.py` et analyse de l'ordre de priorité de `choose`.
