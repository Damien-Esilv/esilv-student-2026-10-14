# TD 2 — Étape 1 : Le vote k-sur-n (Binôme A)

## 1. Contrat et implémentation de `vote_k_sur_n`

La méthode `Orchestrateur.vote_k_sur_n(self, traces_question, k)` a été implémentée dans [`kit-td1/skeleton-multi-llm-en.py`](../../kit-td1/skeleton-multi-llm-en.py) conformément au contrat de l'Étape 1 du TD 2 :

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

## 2. Tableau comparatif des 20 questions (`C01` à `C20`) : 2-sur-3 vs 3-sur-5

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

## 3. Analyse détaillée des écarts et enseignements

### 3.1 Le cas de bascule C08 (Consensus transformé en Abstention)
- **Question** : Chiffre d'affaires des clients ayant 25 ans révolus au 2026-09-24.
- **Référence** : `605 580` cents.
- **Traces exactes** :
  - `openai/gpt-oss-120b` : `val=605580`, `verdict=correct`, `http=200`
  - `cohere/north-mini-code:free` : `val=1188090`, `verdict=incorrect`, `http=200`
  - `qwen/qwen3.8-27b` : `val=605580`, `verdict=correct`, `http=200`
  - `openai/gpt-oss-20b` : `val=25920`, `verdict=incorrect`, `http=200`
  - `dots-studio/dots-3-note-preview:free` : `val=523000`, `verdict=incorrect`, `http=200`
- **Mécanisme** : Dans le panel 2-sur-3, `gpt-120b` et `qwen` s'accordent sur la borne de date correcte, atteignant le seuil $k=2$. En passant à 5 modèles, les deux modèles ajoutés (`gpt-20b` et `dots-3`) échouent tous deux sur le calcul d'âge et renvoient des valeurs erronées différentes. La valeur exacte `605 580` ne rassemble que 2 voix sur 5, ce qui est strictement inférieur au seuil requis $k=3$. Le quorum 3-sur-5 **s'abstient**.
- **Enseignement** : Élargir un quorum à des modèles de moindre capacité augmente le risque de dispersion des voix sur des conditions temporelles complexes. Le quorum 3-sur-5 privilégie la prudence et la sécurité au détriment de la disponibilité.

### 3.2 Résilience infrastructurelle sur C20 (Absorption d'une erreur HTTP 429)
- **Trace** : `qwen/qwen3.8-27b` subit un dépassement de quota tokens/minute (`http_status=429`, `verdict=not_executed`).
- **Mécanisme** : En 2-sur-3, le panel est fragilisé : seuls 2 modèles s'exécutent (`gpt-120b` et `cohere` à `1 106 090`), atteignant de justesse le seuil $k=2$. En 3-sur-5, `gpt-20b` et `dots-3` s'exécutent avec succès et votent également `1 106 090`. Le quorum atteint **4 voix sur 5**, absorbant l'indisponibilité temporaire de Qwen sans vaciller.

### 3.3 Filtrage des requêtes SQL malformées (C10 et C17)
- Sur C10, `cohere` génère une erreur de syntaxe SQLite (`syntax_error near ")"`) et `qwen` une erreur d'exécution (`runtime_error no such column: p.price` car la table `product` n'a pas été jointe).
- Sur C17, `dots-3` produit une syntaxe invalide (`syntax_error near "AS"`).
- Ces requêtes échouent avant résultat et ne votent pas (`verdict != "executed"`), évitant toute corruption du vote.

### 3.4 Questions simples témoins (F1 et F3)
- 100 % d'unanimité (5/5) sur les 9 questions de période pure et de liste de produits (`C01, C03, C04, C05, C06, C07, C12, C13, C14`).
- Confirme la règle de routage : pour F1 et F3, un modèle gratuit rapide sans vérification lourde suffit pour les usages internes.
