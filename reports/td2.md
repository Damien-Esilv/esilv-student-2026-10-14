# Rapport TD 2 — Quorum et règle de routage

> **Dépôt** : `reports/td2.md`  
> **Sous-groupe** : Binôme A (Étape 1) · Binôme B (Étape 2) · Binôme C (Étape 3)

---

## Étape 1 — Vote *k*-sur-*n* (Binôme A)

### 1.1 Contrat et implémentation de `vote_k_sur_n`

La méthode `Orchestrateur.vote_k_sur_n(self, traces_question, k)` a été implémentée dans [`kit-td1/skeleton-multi-llm-en.py`](file:///c:/Users/gerva/Desktop/esilv-student-2026-10-14/kit-td1/skeleton-multi-llm-en.py#L606-L658) conformément au contrat du TD 2 :

1. **Seules les propositions exécutées votent** : seuls les éléments avec `verdict == "executed"` et une valeur entière non nulle (`value is not None`) participent au vote. Les erreurs (`sql_invalid`, `not_executed`, `access_error`, HTTP 429) et indisponibilités restent comptabilisées dans le dénominateur $n$ mais n'émettent aucune voix.
2. **Majorité stricte** : $k$ doit vérifier $\lfloor n / 2 \rfloor < k \le n$, sous peine de lever une `ValueError`.
3. **Refus des doublons** : deux propositions issues de la même paire `(provider, model_requested)` sont rejetées avec une `ValueError` (un doublon ne constitue pas un second vote).
4. **Décision avec consensus** : si une valeur atteint au moins $k$ voix, la méthode retourne :
   ```json
   {"consensus": true, "value": v, "votes": nombre, "models": ["provider:model", ...]}
   ```
5. **Abstention sans invention** : si aucune valeur n'atteint $k$ voix, la méthode retourne :
   ```json
   {"consensus": false, "value": null, "votes": plus_grand_nombre_de_voix, "models": []}
   ```
   La méthode n'invente jamais de valeur.
6. **Étanchéité vis-à-vis de la référence** : la référence de vérité terrain n'est jamais fournie à la méthode de vote ; l'évaluation de la conformité intervient strictement après que la décision a été scellée.

L'exercice du vote est validé par `kit-td1/atelier-vote.py` :
- Sur les 4 exemples synthétiques hors-réseau (`agreement`, `disagreement`, `unavailable`, `wrong consensus`).
- Sur les traces réelles de TD 1 (`traces-td1.csv`) avec le panel fixe 2-sur-3 (`--panel 3`) et le quorum complet 3-sur-5 (`--panel 5`).

---

### 1.2 Tableau comparatif des 20 questions (`C01` à `C20`) : 2-sur-3 vs 3-sur-5

* **Panel fixe 2-sur-3 ($n=3, k=2$)** : `openai/gpt-oss-120b` (Groq), `cohere/north-mini-code:free` (OpenRouter), `qwen/qwen3.8-27b` (Groq).
* **Quorum complet 3-sur-5 ($n=5, k=3$)** : les 3 modèles précédents + `openai/gpt-oss-20b` (Groq) + `dots-studio/dots-3-note-preview:free` (OpenRouter).

| Cas | Famille | Référence (cents) | Décision 2-sur-3 | Valeur 2/3 (cents) | Voix 2/3 | Conforme 2/3 ? | Décision 3-sur-5 | Valeur 3/5 (cents) | Voix 3/5 | Conforme 3/5 ? | Changement de décision / Écart observé |
|:---:|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---|
| **C01** | F1 (Période) | 792 800 | Consensus | 792 800 | 3/3 | Conforme | Consensus | 792 800 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5) |
| **C02** | F2 (Âge à date) | 590 320 | Consensus | 590 320 | 2/3 | Conforme | Consensus | 590 320 | 3/5 | Conforme | Marge décalée : 2/3 $\to$ 3/5 (Cohere & GPT-20b retournent 0 ; Dots vote 590 320) |
| **C03** | F3 (Produit + Période) | 936 350 | Consensus | 936 350 | 3/3 | Conforme | Consensus | 936 350 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5) |
| **C04** | F1 (Période) | 2 826 250 | Consensus | 2 826 250 | 3/3 | Conforme | Consensus | 2 826 250 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5) |
| **C05** | F1 (Période 1j) | 38 480 | Consensus | 38 480 | 3/3 | Conforme | Consensus | 38 480 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5) |
| **C06** | F1 (Période vide) | 0 | Consensus | 0 | 3/3 | Conforme | Consensus | 0 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5 ; `COALESCE` correct sur ensemble vide) |
| **C07** | F1 (Période 1j) | 13 970 | Consensus | 13 970 | 3/3 | Conforme | Consensus | 13 970 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5) |
| **C08** | F2 (Âge à date) | 605 580 | **Consensus** | **605 580** | **2/3** | **Conforme** | **Abstention** | **None** | **2/5** | **None** | **CHANGEMENT MAJEUR : Consensus $\to$ Abstention** (GPT-20b et Dots dispersent sur 25 920 et 523 000) |
| **C09** | F2 (Âge à date) | 487 980 | Consensus | 487 980 | 2/3 | Conforme | Consensus | 487 980 | 3/5 | Conforme | Marge décalée : 2/3 $\to$ 3/5 (Qwen retourne 0, GPT-20b sécurise la 3e voix) |
| **C10** | F2b (Âge commande) | 558 980 | Abstention | None | 1/3 | None | Abstention | None | 2/5 | None | Double abstention ; 2 erreurs SQL en 2/3 (Cohere syntaxe, Qwen jointure) |
| **C11** | F2 (Âge à date) | 446 690 | Consensus | 446 690 | 2/3 | Conforme | Consensus | 446 690 | 3/5 | Conforme | Marge décalée : 2/3 $\to$ 3/5 (Cohere et GPT-20b échouent ; Dots vote 446 690) |
| **C12** | F3 (Produits) | 1 666 490 | Consensus | 1 666 490 | 3/3 | Conforme | Consensus | 1 666 490 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5) |
| **C13** | F3 (Produit + Période) | 107 740 | Consensus | 107 740 | 3/3 | Conforme | Consensus | 107 740 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5) |
| **C14** | F3 (Période vide) | 0 | Consensus | 0 | 3/3 | Conforme | Consensus | 0 | 5/5 | Conforme | Identique (Unanimité 3/3 $\to$ 5/5) |
| **C15** | Combinaison | 168 680 | Abstention | None | 1/3 | None | Abstention | None | 2/5 | None | Double abstention ; dispersion multiple (168 680 a 2 voix < k=3) |
| **C16** | Combinaison | 376 740 | Consensus | 376 740 | 3/3 | Conforme | Consensus | 376 740 | 4/5 | Conforme | Marge décalée : 3/3 $\to$ 4/5 (Dots échoue à 211 260) |
| **C17** | Combinaison | 258 180 | Abstention | None | 1/3 | None | Abstention | None | 2/5 | None | Double abstention ; Dots en erreur syntaxe SQL (`near "AS"`) |
| **C18** | Combinaison | 62 480 | Consensus | 62 480 | 3/3 | Conforme | Consensus | 62 480 | 4/5 | Conforme | Marge décalée : 3/3 $\to$ 4/5 (Dots échoue à 39 580) |
| **C19** | Combinaison | 1 990 | Abstention | None | 1/3 | None | Abstention | None | 2/5 | None | Double abstention ; le panel 2/3 échoue totalement ; GPT-20b et Dots ont 1 990 (2 < 3) |
| **C20** | F1 (Période) | 1 106 090 | Consensus | 1 106 090 | 2/3 | Conforme | Consensus | 1 106 090 | 4/5 | Conforme | Marge décalée : 2/3 $\to$ 4/5 ; **Tolérance aux pannes** : Qwen en HTTP 429 |

---

### 1.3 Analyse détaillée des écarts et enseignements

1. **Le cas de bascule C08 (Consensus transformé en Abstention) :**
   - *Question* : chiffre d'affaires des clients ayant 25 ans révolus au 2026-09-24.
   - *Référence* : `605 580` cents.
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


### Cas étudié et résultats

C02 demande le chiffre d'affaires HT, en centimes, de **toutes les commandes des clients ayant exactement 25 ans le 25 septembre 2026**. Le cas provient de notre lot TD 1 du 21 octobre 2026, dont les traces sont étiquetées `real`. Les requêtes conservées ont été réexécutées localement sur `data/boutique.sqlite`, sans nouvel appel aux modèles.

La référence C02 de [reference-td1.csv](../kit-td1/reference-td1.csv) vaut **590 320 centimes**. Les cinq réponses retenues sont :

| Fournisseur et modèle | Valeur en centimes | Verdict | Trace source dans td1/raw-traces |
|---|---:|---|---|
| Groq / openai/gpt-oss-120b | 590 320 | correct | traces-gpt120b-C01-C20.csv |
| OpenRouter / cohere/north-mini-code:free | 0 | incorrect | traces-C.csv |
| Groq / qwen/qwen3.8-27b | 590 320 | correct | traces-D.csv |
| Groq / openai/gpt-oss-20b | 0 | incorrect | traces-gpt20b-C01-C20.csv |
| OpenRouter / dots-studio/dots-3-note-preview:free | 590 320 | correct | traces-E.csv |

Ces cinq cellules C02 figurent dans [traces-td1.csv](../kit-td1/traces-td1.csv). Pour Dots, nous retenons le lot principal `traces-E.csv`, conformément au [tableau de comparaison TD 1](../td1/model-question-comparison-en.csv).

GPT-OSS 20B et Cohere partagent donc la même valeur erronée, **0**, avec un écart de **590 320 centimes** par rapport à la référence.

### Requêtes SQL et causes des erreurs

**GPT-OSS 20B** — cellule `groq:openai/gpt-oss-20b:C02`, tentative 1, dans [traces-gpt20b-C01-C20.csv](../td1/raw-traces/traces-gpt20b-C01-C20.csv). Requête originale :

```sql
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE c.birth_date > '2025-09-25' AND c.birth_date <= '2026-09-25';
```

Le filtre sélectionne des personnes nées dans l'année précédant le 25 septembre 2026, au lieu de clients âgés de 25 ans. La fenêtre correcte est **`2000-09-25 < birth_date <= 2001-09-25`** : la borne gauche exclut les personnes ayant déjà 26 ans, tandis que la borne droite inclut celles qui fêtent leurs 25 ans ce jour-là. Aucun client ne satisfait le filtre erroné. La requête s'exécute sans erreur, mais `COALESCE` transforme la somme vide en **0**.

**Cohere** — cellule `openrouter:cohere/north-mini-code:free:C02`, tentative 1, dans [traces-C.csv](../td1/raw-traces/traces-C.csv). Requête originale :

```sql
SELECT COALESCE(SUM(o.quantity_product * p.price), 0) AS revenue_cents
FROM customers c
JOIN orders o ON c.customer_id = o.customer_id
JOIN product p ON o.product_id = p.product_id
WHERE c.birth_date <= '2026-09-25' AND c.birth_date > date('2026-09-25', '-26 years')
AND c.birth_date <= date('2026-09-25', '-25 years') AND c.birth_date > date('2026-09-25', '-26 years')
AND o.date >= '2026-09-25 00:00:00' AND o.date < '2027-09-25 00:00:00';
```

Le filtre d'âge est correct, malgré des conditions répétées. L'erreur est l'ajout des deux restrictions sur `o.date` : C02 demande **toutes les commandes**, sans cette période. La dernière commande de la base date du **20 septembre 2026 à 19:24:25**, donc aucune commande ne satisfait la période ajoutée. La requête retourne elle aussi **0**.

Les deux modèles donnent la même mauvaise valeur pour **deux causes différentes** : une mauvaise fenêtre de naissance et une mauvaise période de commandes.

### Diagnostic SQL et contrôle indépendant

Les deux requêtes erronées ne retiennent aucune ligne. Les montants oubliés correspondent donc à toutes les commandes des clients correctement sélectionnés par l'âge. Le [diagnostic suivant](../td2/B-consensus/diagnostic-c02.sql), exécuté sur `kit-td1/data/boutique.sqlite`, liste ces clients et leur chiffre d'affaires HT :

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

| Client | Date de naissance | Montant oublié par chaque modèle en centimes |
|---|---|---:|
| C001 | 2001-09-25 | 135 000 |
| C002 | 2001-09-24 | 25 920 |
| C005 | 2000-09-26 | 150 240 |
| C007 | 2000-11-30 | 118 740 |
| C008 | 2001-05-15 | 99 090 |
| C009 | 2001-03-10 | 61 330 |
| **Total** | | **590 320** |

Ces six clients expliquent exactement l'écart pour chacun des deux modèles : **590 320 - 0 = 590 320 centimes**. Aucune ligne n'est ajoutée à tort par les deux requêtes ; toutes les différences sont des omissions.

**Contrôle indépendant :** un calcul Python sur `customers.csv`, `orders.csv` et `product.csv`, sans exécuter de SQL, retrouve les mêmes montants par client et le même total. Il calcule l'âge par différence des années, corrigée selon que l'anniversaire est passé ou non, puis additionne `quantité × prix` sur toutes les commandes des clients âgés de 25 ans.

### Quorums et vérification avec le binôme A

Le décompte est effectué sur les réponses conservées, sans exclure les valeurs marquées `incorrect`. La référence sert à évaluer la décision après le vote.

| Panel déclaré | Seuil | Voix pour 590 320 | Voix pour 0 | Décision confirmée avec le code de A |
|---|---:|---:|---:|---|
| GPT-OSS 120B, Cohere, Qwen | 2 sur 3 | 2 | 1 | Consensus à 590 320, correct |
| Les cinq modèles du tableau ci-dessus | 3 sur 5 | 3 | 2 | Consensus à 590 320, correct |

Dans le panel 2 sur 3, GPT-OSS 120B et Qwen donnent la bonne valeur. Dans le quorum 3 sur 5, Dots apporte une troisième voix à cette valeur. **L'accord erroné entre GPT-OSS 20B et Cohere est donc battu dans les deux configurations.** Le passage de 2 sur 3 à 3 sur 5 ne change pas la valeur retenue sur C02.

**Vérification avec le binôme A effectuée le 18 novembre 2026.** Sa méthode `Orchestrateur.vote_k_sur_n` a été exécutée sur C02 pour les deux panels, à l'aide de son atelier. Depuis `kit-td1`, les commandes sont :

```powershell
python atelier-vote.py --traces traces-td1.csv --case C02 --panel 3
python atelier-vote.py --traces traces-td1.csv --case C02 --panel 5
```

Les résultats obtenus concordent avec le décompte : `consensus: true`, `value: 590320`, `votes: 2` pour le panel 2 sur 3 ; `consensus: true`, `value: 590320`, `votes: 3` pour le quorum 3 sur 5. Dans les deux cas, l'atelier indique `matches_reference: true`. La référence est comparée après la décision et n'est pas transmise à la méthode de vote. **La comparaison entre notre décompte et le code de A est donc terminée pour C02.**

Ce cas montre que deux modèles peuvent s'accorder sur une valeur fausse sans partager la même erreur SQL. Les deux quorums donnent ici la bonne décision, mais leur accord ne garantit pas leur exactitude sur d'autres questions. Le contrôle indépendant des données et des filtres permet de détecter les erreurs et de justifier le montant retenu.

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

- **Binôme A** : Implémentation du vote strict $k$-sur-$n$ dans `skeleton-multi-llm-en.py`, support multi-panel dans `atelier-vote.py`, tableau comparatif complet 2-sur-3 vs 3-sur-5 sur les 20 questions TD 1, analyse détaillée des écarts (bascule C08, résilience HTTP 429 sur C20, gestion des erreurs SQL C10/C17).
- **Binôme B** : Analyse du cas C02, identification de l’accord erroné entre GPT-OSS 20B et Cohere, diagnostic des deux requêtes SQL, exécution de la requête delta et contrôle indépendant sur les CSV. Décompte des quorums 2-sur-3 et 3-sur-5, puis vérification avec le code du binôme A.
- **Binôme C** : Calcul des taux TD 1 par famille (`F1`, `F2`, `F2b`, `F3`, `Combinaisons`), rédaction de la règle de routage, adaptation de `kit-td1/atelier-routage.py` et analyse de l'ordre de priorité de `choose`.
