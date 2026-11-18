## Partie B Accord erroné sur C02

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
