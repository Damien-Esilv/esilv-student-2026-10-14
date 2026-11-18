# Rapport TD 2 — Quorum et règle de routage

> **Dépôt** : `reports/td2.md`  
> **Sous-groupe** : Binôme A (Étape 1) · Binôme B (Étape 2) · Binôme C (Étape 3)

---

## Étape 1 — Vote *k*-sur-*n* (Binôme A)

*(À compléter par le Binôme A : méthode `Orchestrateur.vote_k_sur_n`, tableau comparatif sur les 20 questions `C01`–`C20` entre le panel 2-sur-3 et le quorum 3-sur-5, et commentaires sur chaque écart.)*

---

## Étape 2 — Faux consensus SQL (Binôme B)

*(À compléter par le Binôme B : cas identifié dans `traces-td1.csv` ou `DEMO-SQL-C11`, verdict des quorums 2-sur-3 et 3-sur-5, diagnostic des clauses SQL fautives et requête delta sur `data/boutique.sqlite`.)*

---

## Étape 3 — Règle de routage et simulateur (Binôme C)

### 3.1 Taux exacts de TD 1 par famille de questions

Sources : `td1/model-question-comparison-en.csv` et `kit-td1/questions-td1.json` (lot de 20 questions `C01`–`C20`).

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

- **Binôme A** : *(à compléter)*
- **Binôme B** : *(à compléter)*
- **Binôme C** : Calcul des taux TD 1 par famille (`F1`, `F2`, `F2b`, `F3`, `Combinaisons`), rédaction de la règle de routage, adaptation de `kit-td1/atelier-routage.py` et analyse de l'ordre de priorité de `choose`.
