# Analyse de risques manuelle — cas ShoPix (référence)

| Champ | Valeur |
|---|---|
| Cas | Boutique en ligne ShoPix (produits imprimés, ~60 commandes/semaine, pic ×3 en nov–déc) |
| Chantier | #17 — consolidation soutenance |
| Date | 04/10/2026 |
| Analyste | Analyste humain (exercice de référence) |
| Méthode | STRIDE pour l'identification, DREAD pour la priorisation, matrice probabilité × impact en appui |
| Périmètre | Site, back-office, base, fichiers, sauvegardes, secrets, comptes. Hébergeur et prestataires sont des dépendances, pas des composants maîtrisables |
| Statut | travail manuscrit, non relu par un tiers |

Note de méthode : la présente analyse a été rédigée de façon autonome sur l'énoncé. Les livrables de la chaîne automatisée (`03-menaces.md`, `04-evaluation.md`, `05-traitement.md`) ont été consultés ensuite, uniquement pour la comparaison du § 7.

## 1. Actifs clés

Ce qui a réellement de la valeur, dans l'ordre où je les protégerais :

1. **Compte admin « Mélanie »** (A-09). Droit total, pas de MFA, session 30 jours. Point de rupture unique : sa perte équivaut à la perte de la boutique.
2. **Fichier clients** (A-05, A-06). Nom, adresse, téléphone, historique d'achats. Valeur marchande immédiate pour un concurrent, et RGPD : c'est le seul actif dont la fuite coûte des amendes en plus du préjudice commercial.
3. **Secrets PayFlow / MailJet** (A-08). En clair dans `.env`, déjà versionnés une fois. Un secret exposé n'a pas de durée de vie : il faut le considérer comme volé jusqu'à rotation.
4. **Commandes** (A-04). L'historique de cinq ans n'est pas reconstructible ; sa perte est définitive, pas amortissable.
5. **Disponibilité de décembre** (A-13). ~1 500 €/semaine pendant trois semaines. C'est la seule période où une minute d'indisponibilité se paie comptant.
6. **Nom de domaine et identité** (A-12, A-14). Un avis de phishing a déjà été reçu et jamais analysé ; perdre le domaine, c'est perdre l'adresse commerciale.

Point de perception : il n'y a aucun actif matériel détenu en propre. Tout le risque est logique, applicatif et organisationnel. Un pare-feu ou un scanner réseau ne changeraient pas grand-chose ; ce sont le MFA, les secrets et la restauration qui comptent.

## 2. Choix de méthode et échelles

**STRIDE** parce que le cas fournit un DFD lisible et que la quasi-totalité des chemins d'attaque passent par des éléments web. Je m'appuie sur les quatre frontières : Internet → hébergeur (F1), hébergeur → prestataires (F2), absence de cloisonnement interne (F3), mutualisation (F4). F3 est le point le plus structurant de tout le cas.

La vie privée et le RGPD sortent de STRIDE. Je les traite quand même (une seule menace, H-10) parce qu'ils conditionnent la légitimité de l'activité, mais je les signale comme hors grille plutôt que de forcer une catégorie.

**DREAD** en priorisation : elle est utile ici parce qu'elle force à séparer « how bad » de « how easy », ce que la matrice seule ne fait pas. C'est justement ce qui révèle les excès de la chaîne automatisée (§ 7).

Échelles utilisées :

- Probabilité 1–4 : 1 rare, 2 improbable, 3 probable, 4 quasi certain (sur 12 mois).
- Impact 1–4 : 1 négligeable, 2 limité, 3 important, 4 sévère (irréversible ou difficilement rattrapable).
- Matrice P × I : P ou I = 4 avec l'autre ≥ 3 → critique ; 3×3, 4×2, 2×4 → élevé ; le reste → moyen ou faible.
- DREAD, moyenne de 5 critères sur 10 : ≥ 8 critique, 6–8 élevé, 4–6 moyen, < 4 faible.
- Règle de décision : **je retiens le niveau le plus sévère entre la matrice et DREAD**, sauf si l'écart s'explique par un biais connu de la grille (cas de H-12, commenté plus bas).

## 3. Menaces identifiées (12)

| ID | Actif | STRIDE | Menace, en une phrase | Fait documenté qui la rend crédible |
|---|---|---|---|---|
| H-01 | A-03, A-09 | S | Attaque par dictionnaire sur `/admin`, sans verrouillage ni MFA | ~1 000 tentatives/24 h en 2024, aucun lockout |
| H-02 | A-09, A-01 | S | Vol de session admin (cookie trop long, drapeaux non documentés, XSS ou clic sur lien) | Sessions 30 j ; rien sur `httpOnly`/`secure`/CSP |
| H-03 | A-01, A-04 | T | Injection SQL ou exploitation d'une faille applicative sur le site public | PHP 8.0 EOL, pas de WAF, aucun audit lancé |
| H-04 | A-01 à A-06 | E | Pas de cloisonnement : une seule compromission donne la base, les exports et le back-office | Site = API = BO = MySQL sur la même VM, compte `shopix` unique |
| H-05 | A-08, A-14 | I | Divulgation des clés API (déjà survenue) et usage frauduleux | MailJet 2023 (2 j de spam), PayFlow 2024 (versionnée 1 mois) |
| H-06 | A-07 | I | Dump SQL en clair déposé en FTP sur le même hébergeur mutualisé | Sauvegarde hebdomadaire manuelle, aucun chiffrement |
| H-07 | A-04, A-07 | D | Sauvegarde oubliée ou jamais restaurée : perte définitive de l'historique de commandes | Incident réel 2025, 2 jours de commandes perdus |
| H-08 | A-01, A-16 | T | Détournement de paiement : SDK non patché, webhook `payment.ok` non vérifié, chargebacks | SDK 2.1 vulnérable, `composer audit` jamais exécuté |
| H-09 | A-13, A-01 | D | Indisponibilité pendant le pic de décembre (saturation, panne, attaque) | Pas de monitoring, pas de redondance, VM mutualisée |
| H-10 | A-05, A-11 | hors grille (RGPD) | Contrôle ou réclamation : registre absent, consentement douteux, droit à l'oubli non outillé | Mentionnés dans le cas comme non conformes |
| H-11 | A-06, A-10 | I | Usage détourné des données clients par les comptes internes (exports `.csv` complets, préparateurs) | Exports non pseudonymisés conservés 24 mois, 2 comptes préparateurs sans MFA |
| H-12 | A-03, A-06 | R | Aucune trace des actions d'administration : ni preuve en litige, ni preuve RGPD | Aucune journalisation centralisée |

Trois choix de cadrage que j'assume :

- **H-02 est séparée de H-01** parce que les contre-mesures ne sont pas les mêmes. Fermer le brute force ne ferme pas le vol de session : si la session dure 30 jours, un cookie volé reste valable même une fois le MFA en place. C'est le trou que la lecture automatisée laisse ouvert.
- **H-06 et H-07 restent séparées** : l'une parle d'un tiers qui lit, l'autre d'un disque qui meurt. Même cause racine (la sauvegarde est traitée à la main), effets opposés.
- **H-11 replace l'insider au centre.** Le cas ne dit rien de malveillant sur les préparateurs, mais deux comptes sans MFA qui téléchargent des exports complets, c'est une surface d'attaque interne réelle. Personne n'en parle dans la lecture automatisée.

## 4. Évaluation des risques

| ID | P | I | Matrice | DREAD (D/R/E/A/D) | Moy. | DREAD | Niveau retenu |
|---|---|---|---|---|---|---|---|
| H-01 | 4 | 4 | Critique | 9/9/8/8/10 | 8,8 | Critique | **Critique** |
| H-02 | 2 | 4 | Élevé | 7/5/5/7/5 | 5,8 | Moyen | Élevé (matrice) |
| H-03 | 2 | 4 | Élevé | 9/7/7/9/7 | 7,8 | Élevé | **Élevé** |
| H-04 | 4 | 4 | Critique | 9/9/8/9/6 | 8,2 | Critique | **Critique** |
| H-05 | 3 | 3 | Élevé | 8/7/7/8/5 | 7,0 | Élevé | **Élevé** |
| H-06 | 2 | 4 | Élevé | 9/8/6/9/5 | 7,4 | Élevé | **Élevé** |
| H-07 | 2 | 4 | Élevé | 8/7/5/8/5 | 6,6 | Élevé | **Élevé** |
| H-08 | 2 | 3 | Moyen | 8/5/4/7/4 | 5,6 | Moyen | Moyen |
| H-09 | 3 | 4 | Critique | 8/5/5/8/7 | 6,6 | Élevé | Élevé (DREAD) |
| H-10 | 3 | 3 | Élevé | 5/9/8/8/8 | 7,6 | Élevé | **Élevé** |
| H-11 | 2 | 3 | Moyen | 7/7/5/6/4 | 5,8 | Moyen | Moyen |
| H-12 | 4 | 2 | Élevé | 4/8/7/3/6 | 5,6 | Moyen | Moyen (arbitrage, voir note) |

Justification des cinq premières :

- **H-01** — Reproductibilité 9 : l'attaque a déjà eu lieu mille fois par jour, elle est scriptable. Découvrabilité 10 : les journaux la montrent et personne n'a réagi. Impact 4 : accès total et durable, sans trace de contre-seing.
- **H-03** — Damage et Affected 9 : la base contient tout le fichier clients et les prix. Exploitabilité 7 : aucune protection en place, mais je ne peux pas affirmer qu'un paramètre est réellement injectable, donc probabilité 2 et non 3. C'est une menace à confirmer, pas une certitude.
- **H-04** — Je la traite comme une menace à part entière et non comme un simple amplificateur. Raisonnement : elle est matérialisable sans compromission préalable (un attaquant peut cibler directement les fichiers ou le back-office) et son traitement est radicalement différent. Découvrabilité 6 seulement, parce qu'elle ne se voit pas depuis l'extérieur.
- **H-05** — Probabilité 3 et non 2 : le contrôle a déjà échoué deux fois et rien dans le cas n'indique une rotation. Découvrabilité 5 : l'événement est visible côté boutique (spam, transactions), pas côté attaquant.
- **H-09** — La matrice ressort critique parce qu'elle traite la saisonnalité comme une certitude. Je n'y crois pas : une panne en décembre reste un événement possible, pas probable. DREAD 6,6 tranche. Impact 4 conservé (perte de CA irrattrapable).

Note d'arbitrage sur **H-12** : la matrice donne élevé uniquement parce que la probabilité est 4 — or l'événement est permanent, ce qui rend la probabilité inutile comme indicateur. La majorité des actions non tracées n'a aucune conséquence, et Damage comme Découvrabilité ne sont pas concernés. **Je classe ce risque Moyen et je refuse de le remonter** : le ratio coût du contrôle / gain est mauvais. À traiter en lot 2, pas en priorité.

## 5. Traitement des risques

| ID | Décision | Actions | Coût indicatif | Résiduel |
|---|---|---|---|---|
| H-01 | Réduire | MFA TOTP sur `/admin` (application gratuite) ; lockout à 5 échecs + limitation de débit ; session 8 h ; accès `admin.` restreint | 0–100 € | Moyen |
| H-02 | Réduire | `httpOnly` + `secure` + `SameSite=Strict`, CSP sur le BO, invalidation des sessions à la connexion, session 8 h | 0 € (config) | Faible |
| H-03 | Réduire + Éviter | Requêtes paramétrées sur tout le chemin catalogue/checkout ; compte MySQL en lecture seule pour le site ; **retirer le plugin impressions 3.2.1** plutôt que le patcher (aucun audit possible, fonction non critique) ; PHP/MySQL à jour | ~200 € | Moyen |
| H-04 | Réduire | Exiger de l'hébergeur une isolation vérifiable, sinon migrer sur un VPS ; un compte MySQL par application ; cloisonner l'accès aux exports | 700–900 €/an | Moyen (mutualisation résiduelle) |
| H-05 | Réduire + Transférer | **Rotation immédiate des deux clés**, avant toute autre action ; `.env` hors dépôt + secret scanning ; clé PayFlow limitée au seul paiement ; DPA avec les deux prestataires | ~50 € | Faible–Moyen |
| H-06 | Réduire + Transférer | Chiffrement du dump avant transfert ; sauvegarde externalisée chez un tiers, donc **hors de la machine mutualisée** (transfert de la charge de conservation) | ~150 €/an | Faible |
| H-07 | Réduire | Sauvegarde automatique (cron) au lieu de la main ; test de restauration **mensuel et horodaté** — une sauvegarde non testée n'est pas une sauvegarde ; règle 3-2-1 | ~100 € | Faible |
| H-08 | Réduire | `composer audit` en intégration continue ; vérification de signature sur le webhook ; alerte sur écart entre commandes payées et commandes expédiées | ~100 € | Moyen |
| H-09 | Accepter + Transférer | Monitoring de disponibilité gratuit + alerte ; limitation de débit ; **risque résiduel accepté** si aucune assurance n'est souscrite | 0 € | Moyen |
| H-10 | Réduire | Registre des traitements (une demi-journée) ; consentement en double opt-in ; procédure d'effacement ; mentions légales complètes ; habilitation d'un référent | ~400 € (temps) | Faible |
| H-11 | Réduire + Éviter | MFA sur les 2 comptes préparateurs ; **arrêter l'export `.csv` complet** au profit d'un export limité aux commandes du jour ; réattribution des droits à chaque départ ; conservation ramenée de 24 à 12 mois | 0–50 € | Faible |
| H-12 | Réduire (lot 2) | Journalisation des actions d'administration (exports, prix, suppression de commande) ; journaux en écriture seule, 1 an de rétention | ~150 € | Faible |

Répartition des décisions : 9 réduire, 2 réduire + transférer (H-05, H-06), 2 réduire + éviter (H-03, H-11), 1 accepter + transférer (H-09). Aucun risque n'est ignoré sans décision.

Séquencement en trois lots, pour tenir l'enveloppe de 2 500 €/an :

- **Lot 1 — immédiat, ~150 €** : rotation des clés (H-05), retrait du plugin non audité (H-03), durcissement des cookies (H-02), arrêt de l'export complet (H-11). Ce sont des décisions, pas des achats.
- **Lot 2 — ~1 350 €** : MFA et lockout (H-01), sauvegarde automatisée et externalisée (H-06, H-07), journalisation (H-12), conformité RGPD (H-10).
- **Lot 3 — ~700–900 €/an** : hébergement isolé ou VPS (H-04), `composer audit` en continu (H-08), monitoring (H-09).

Total ~2 200 €/an, sous l'enveloppe. La cyber-assurance perte d'exploitation (~2 000 €) **ne rentre pas** et je ne la recommande pas en priorité : elle ne couvrirait qu'un seul des douze risques, pour plus cher que la réduction de onze d'entre eux. Si le dirigeant veut tout de même transférer H-09, il faut trouver 800 € de plus ou renoncer au lot 3.

## 6. Validation et suivi (note de l'analyste)

**Risque résiduel global.** Après les lots 1 et 2, je place le risque résiduel de la boutique à **Moyen**, et non à Faible. Deux motifs le justifient : l'hébergement mutualisé reste non vérifiable tant que le lot 3 n'est pas fait (H-04), et la perte de l'historique de commandes ne se rattrape pas si la restauration échoue au moment de tester (H-07). Un plan de réduction qui promet un risque résiduel faible sans avoir testé une restauration est une promesse que je ne fais pas.

**Ce que j'accepte, et par écrit** :

- **H-09** (indisponibilité en décembre) : risque résiduel Moyen accepté. Il est impossible de le réduire à coût raisonnable sur une VM mutualisée, et le transfert coûte plus que le budget disponible. La compensation est organisationnelle : procédure de bascule manuelle vers un paiement hors ligne et information client affichée sur la page d'accueil.
- **H-12** (absence de traçabilité) : risque Moyen accepté jusqu'au lot 2, sans conséquence commerciale connue à ce jour.
- **H-02** : risque résiduel Faible accepté sans audit de code, en raison du rapport coût/bénéfice.

**Ce que je n'accepte pas** : les deux risques critiques H-01 et H-04 tant que le lot 1 et le lot 2 ne sont pas faits. Un budget de 2 500 € sans MFA sur le back-office n'est pas un budget sécurité, c'est un budget décoratif.

**Suivi** : revue trimestrielle du registre ; revue complète avant le 15 octobre (avant le pic) et après. Déclencheurs de revue hors périodique : tout incident de sécurité, tout changement d'hébergeur ou de prestataire, toute nouvelle fonctionnalité de paiement, tout dépassement du seuil de commandes au-delà duquel le site deviendrait rentable à protéger.

**Points que je n'ai pas pu trancher seul, à remonter au dirigeant** : le budget (lot 3 ou assurance), le sort du plugin d'impression (retrait = perte de fonction), et la décision de migrer ou non l'hébergement.

## 7. Comparaison avec l'analyse automatisée

### 7.1 Couverture de mes menaces par la chaîne IA

Écart de score = DREAD moyen (sur 10) de la menace IA correspondante moins le mien. Je commente au-delà de 1 point.

| Mienne | IA | Couverte ? | DREAD IA | DREAD moi | Écart | Lecture de l'écart |
|---|---|---|---|---|---|---|
| H-01 auth. back-office | M-01 | oui | 7,6 | 8,8 | −1,2 | **Commenté.** L'IA sous-estime Damage (8) et surtout les utilisateurs affectés (5). Le back-office donne accès à tout : produits, commandes, clients, exports. À 5/10 en/users affectés, la menace sort du top 3 alors qu'elle est la pire du dossier. |
| H-02 vol de session | — | **non** | — | 5,8 | — | **Absent.** L'IA mentionne les sessions 30 jours comme un facteur aggravant de M-01, mais ne fait jamais du vol de session une menace, ni n'y rattache de contre-mesure (`httpOnly`, `secure`, CSP). Une session de 30 jours rend le MFA partiel : c'est un trou de raisonnement. |
| H-03 injection / site public | M-04 | oui | 7,6 | 7,8 | −0,2 | Concordance. Même niveau Élevé. |
| H-04 absence de cloisonnement | M-10 | oui | 8,8 | 8,2 | +0,6 | Concordance. Je retire 1 point de découvrabilité : cette faiblesse ne se voit pas de l'extérieur, l'IA la met à 9. |
| H-05 clés API | M-07 | oui | 6,8 | 7,0 | −0,2 | Concordance. L'IA traite M-03 (MailJet) séparément, je le fusionne : même actif, même contrôle qui a échoué. |
| H-06 sauvegardes en clair | M-08 | oui | 6,6 | 7,4 | −0,8 | Concordance. Je monte la reproductibilité à 8 : le dump est en clair en permanence, l'exposition n'est pas un événement mais un état. |
| H-07 perte de commandes | M-14 | oui (niveau différent) | 5,8 | 6,6 | −0,8 | **Commenté.** L'IA donne un impact Moyen parce que le compteur de l'incident 2025 dit « 2 jours perdus ». C'est une lecture trop locale : ce qui est en jeu n'est pas 2 jours, c'est l'historique de commandes non reconstructible, avec le fichier clients dedans. Impact 4 de mon côté, donc Élevé et non Moyen. |
| H-08 fraude au paiement | M-05 | oui (niveau différent) | 6,2 | 5,6 | +0,6 | **Commenté.** Je classe Moyen et non Élevé : le paiement est externalisé et tokenisé, l'impact financier est borné par le montant des transactions détournées, et l'exploitabilité est faible (il faut connaître la faille du SDK). L'IA met l'impact à Élevé par association avec la perte de CA global, ce qui revient à compter deux fois le même euro. |
| H-09 indisponibilité déc. | M-09 | oui | 7,0 | 6,6 | +0,4 | Concordance sur le DREAD, mais la matrice de l'IA renvoie aussi Élevé alors qu'elle devrait donner critique avec mon impact 4. Nous trichons tous les deux sur la saisonnalité. |
| H-10 non-conformité RGPD | M-13 | oui | 7,6 | 7,6 | 0 | Score identique, **raisonnement différent** : l'IA justifie la probabilité Élevée par la non-conformité *actuelle*. On ne peut pas probabiliser un état ; ce qui a une probabilité, c'est le contrôle ou la réclamation, que j'estime à 3. La surévaluation de la probabilité est compensée par un impact plus bas, d'où une convergence de score par deux chemins opposés. |
| H-11 usage interne / exports | M-11 (partiel) | **partiellement** | 7,2 | 5,8 | −1,4 | **Commenté, plus gros écart du dossier.** L'IA note 7,2 « Élevé » et range M-11 au rang 6 sur 14 sur la seule base de fichiers `.csv` non pseudonymisés. Or l'exportabilité excessive est une faiblesse de contrôle, pas une menace : elle ne se réalise pas seule. Mon score est de 5,8 (Moyen) : l'accessibilité interne n'entre pas dans le périmètre STRIDE de l'IA, et le dommage d'un export téléchargé par un préparateur est une fuite interne ponctuelle, pas une violation systématique. |
| H-12 absence de logs | M-06 | oui (niveau différent) | 5,8 | 5,6 | +0,2 | **Commenté.** L'IA met M-06 à « Élevé » (rang 13/14 en DREAD, ce qui est déjà incohérent avec elle-même) en justifiant par « probabilité élevée ». Or la probabilité 4 mesure la fréquence, pas le risque : la majority des actions non tracées est sans conséquence. Ma note 5,6 reste cohérente avec son propre classement DREAD. |

### 7.2 Menaces de l'IA absentes de ma liste

| Menace IA | Raison de l'absence |
|---|---|
| **M-02** (credential stuffing des comptes clients) | Le compte client est **optionnel** et ne sert qu'au suivi de commande. Aucune donnée de paiement n'y est rattachée (cartes tokenisées par PayFlow). La valeur à revendre est faible, donc l'exploitabilité aussi. Je la classe avec H-01 (authentification faible) au lieu de la gonfler en menace autonome ; la migration SHA-1 → bcrypt est à faire, mais ce n'est pas un risque de rang 5 sur 14. |
| **M-03** (usurpation d'identité, spam, phishing) comme menace autonome | Je la fusionne dans H-05 : le déclencheur est la clé en clair, pas le phishing. Le phishing sur le domaine, en soi, a un retour faible pour l'attaquant tant que les cartes sont tokenisées. La réputation est déjà couverte en impact de H-05. |
| **M-12** (divulgation des données personnelles comme conséquence) | L'IA le dit lui-même : ce n'est pas une menace indépendante mais l'impact réglementaire de M-04/M-08/M-10. Le garder comme ligne de registre crée un double comptage du même euro. Je le traite comme un impact, pas comme un risque — et j'ai approché le même point via H-10. |

### 7.3 Menaces de l'IA que je juge peu pertinentes

- **M-06** (répudiation, aucun log) : pertinente en l'état actuel, mais son classement « Élevé » repose sur une probabilité permanente qui ne veut rien dire. La menace n'est pas fausse, sa priorité est fausse.
- **M-11** (exports non pseudonymisés) : ce n'est pas une menace, c'est une non-conformité de minimisation. Elle mérite d'être traitée, pas d'être notée 7,2 en DREAD.
- **M-13** (non-conformité RGPD) : réel et documenté, mais probabiliser l'état de non-conformité revient à noter un fait comme une menace. Le classement correct reste élevé, pour une autre raison que celle donnée.

### 7.4 Ce que la chaîne automatisée fait mieux que moi

- Le rattachement de chaque menace à une source (ISO 27002, LINDDUN, ATT&CK) et le signalement honnête des références absentes, dont le placeholder `CVE-2023-XXXX` que je n'aurais pas su gérer seul.
- Le découpage frontend/prestataire (F1 à F4) est plus rigoureux que ma passe.
- Le registre au format JSON et la structure de registre sont prêts à être exploités tels quels ; mon tableau est plus rapide à lire mais moins automatisable.

## 8. Conclusion

**L'IA rattrape-t-elle l'analyse manuelle ?** Elle récupère environ 9 de mes 12 menaces, avec une rigueur de sourcing et une traçabilité supérieures. Elle ne rattrape pas sur le classement : elle sur-note les menaces organisationnelles (M-11 à 7,2, M-06 et M-14 au niveau Élevé), sous-note la pire menace du dossier sur le critère des utilisateurs affectés (M-01), et laisse un angle mort réel sur le vol de session.

**Forces** : couverture, sources, homogénéité, caractère reproductible et auditable.
**Faiblesses** : une grille de probabilité mal comprise (état confondu avec événement), des impacts comptés deux fois, et aucun regard sur l'angle mort « ce que la menace elle-même ne couvre pas ».
**Recommandations** : traiter la sortie IA comme une première passe à relire, pas comme un registre ; exiger qu'une probabilité 4 soit justifiée par une fréquence observée et non par un constat de non-conformité ; croiser la menace avec la liste des contre-mesures pour repérer ce qui n'est couvert par rien (c'est ainsi qu'est apparu H-02).
