# Arbitrage budgétaire — cas ShoPix

> Projet E21 « Des agents IA pour analyser les risques » — M2 Cybersécurité.
> Objet : trancher l'arbitrage budgétaire laissé ouvert par le dossier d'analyse (issue #20) : **plan de remédiation sous enveloppe de 2 500 €/an ou dépassement**.
> Sources des montants : `analyses/2026-09-23_boutique-en-ligne/05-traitement.md` § 3 (« Équilibre budgétaire indicatif ») — montants repris **tels quels**, sans retraitement. Enveloppe et finalité : `00-description.md` (§ finalité, § « Budget : ~2 500 €/an à justifier »). Statut des risques : `06-validation.md`. Synthèse : `SYNTHESE.md` § 3.
> Portée de ce document : il est une **proposition d'analyste pour la soutenance**. Il ne modifie aucun fichier d'analyse ; le registre reste validé par l'humain (`valide_par`).

## 1. Tableau financier

Reprise intégrale des postes de `05-traitement.md` § 3, avec le rattachement aux risques du registre validé.

| # | Poste (libellé du dossier) | Risques couverts | Coût annuel indicatif |
|---|---|---|---|
| 1 | MFA + verrouillage `/admin` + journalisation (outillage SaaS/SMTP) | R-01 (**critique**), R-06 (élevé) | ~600 € |
| 2 | Hébergement avec isolation / VPS + monitoring | R-10 (**critique**), R-09 (élevé) | ~800 € |
| 3 | `composer audit`, patchs, secret manager, rotation de clés | R-04, R-05, R-07 (élevés) | ~300 € |
| 4 | Mise en conformité RGPD (registre, mentions, consentement) | R-12, R-13 (élevés) | ~400 € (temps) |
| 5 | Sensibilisation + runbook + test de restauration | R-01 (critique), R-09, R-14 (élevé) | ~200 € |
| | **Sous-total mesures (traitement « Réduire »)** | 2 risques critiques + risques élevés | **~2 300 €** |
| 6 | Cyber-assurance perte d'exploitation (transfert de R-09) | R-09 (élevé) | ~2 000 € |
| | **Total** | | **~4 300 €** |

Repères :

- **Enveloppe à justifier devant le dirigeant : ~2 500 €/an** (`00-description.md`).
- **Le plan complet dépasse l'enveloppe de ~1 800 €/an** (4 300 € vs 2 500 €), dont **~2 000 € de cyber-assurance**, soit **46 % du total** pour le seul transfert de R-09 (`SYNTHESE.md` § 3 : « le plan passe de ~2 300 € à ~4 300 €/an avec la cyber-assurance »).
- **Les deux risques critiques sont des « quick wins »** compatibles avec l'enveloppe, sans obstacle technique (`05-traitement.md` § 1) : les 2 300 € de mesures ne sont pas un choix, c'est le minimum du plan.
- Les montants sont des **ordres de grandeur de cadrage**, pas des devis : le tableau du dossier les présente comme tels. Aucun montant n'a été inventé ici.

## 2. Options examinées

| Option | Contenu | Pour | Contre |
|---|---|---|---|
| **(a) Tout financer** | Les 4 300 €/an, dépassement assumé | Le plan de remédiation est appliqué en totalité, aucun risque élevé ne reste sans mesure, traitement « Réduire » + « Transférer » conforme au registre validé | Dépassement de **+72 %** de l'enveloppe sans capacité budgétaire démontrée pour une TPE de ~60 commandes/semaine ; aucune priorisation n'est faite entre ce qui est critique et ce qui est secondaire |
| **(b) Prioriser les risques élevés/critiques et décaler les non critiques** | Financer les 2 risques critiques et les 11 risques élevés (2 300 €), décaler ce qui ne sert qu'aux risques moyens ; traiter l'assurance comme une décision séparée | Cohérent avec la matrice du cas (les 2 critiques d'abord) ; **les 2 300 € tiennent dans l'enveloppe** (92 % de 2 500 €) ; respecte les échéances déjà actées (R-13 déc. 2026) ; laisse une porte de sortie explicite si la prime est refusée | Le tableau de `05-traitement.md` agrège les mesures **par famille d'outillage, pas par risque** : aucun poste ne peut être isolé pour R-02 (seul risque moyen) sans re-devis ; l'assurance reste à trancher |
| **(c) Assurance limitée à la RC** | Ne pas souscrire de perte d'exploitation, seulement une responsabilité civile | Coût plus faible en apparence | Incohérent avec le registre : R-09 est traité « Réduire **+ Transférer** » et validé tel quel le 2026-09-24 ; la perte de CA de pic n'est **pas** couverte par une RC, donc l'impact Élevé reste entièrement porté par l'entreprise ; **aucun montant de RC n'existe dans le dossier** (l'énoncé ne cite que « cyber-assurance » comme exemple de transfert) → option non chiffrable ici ; le résiduel de R-09 passerait de Moyen à un niveau non évaluable |
| **(d) Accepter certains risques faibles sans mesure** | Ne rien faire sur les risques moyens/faibles | Économie immédiate | Contredit `06-validation.md` § 2 (« aucun risque « accepter » : tous les risques retenus sont traités en Réduire ») ; les résiduels sont **déjà acceptés** par l'analyste : ré-accepter sans mesure n'apporte rien et supprime des contre-mesures peu coûteuses (bcrypt/argon2, 2FA clients) qui font passer R-02 en résiduel Faible |

## 3. Décision recommandée

**Option (b)** — c'est la plus défendable devant un jury parce qu'elle est la seule qui **suit la matrice** (2 critiques, puis 11 élevés), **respecte les décisions déjà validées** par l'analyste le 2026-09-24, et **tient dans l'enveloppe** pour tout ce qui relève du traitement « Réduire ».

Logique en trois temps :

1. **Mesures : 2 300 €/an, sous l'enveloppe.** Les 2 risques critiques (R-01, R-10) et les 11 risques élevés sont traités. Marge résiduelle : ~200 €/an. Aucun poste n'est différé : le tableau du dossier agrège les mesures par famille d'outillage, et le seul risque moyen (R-02) ne dispose d'aucune ligne budgétaire propre — ses mesures (bcrypt/argon2, 2FA clients, détection de connexions anormales) sont absorbées par l'outillage des postes 1 et 3. Différer R-13 (400 €) serait contredit par l'échéance **déc. 2026** actée dans `06-validation.md` § 3.
2. **Cyber-assurance : décision séparée, pas une ligne de remédiation.** R-09 est le seul risque où l'impact est **non récupérable** (pic de novembre–décembre, ~1 500 €/semaine de CA, `SYNTHESE.md`) : le transfert financier est le seul traitement qui le rend supportable, et il est **déjà validé** au registre (« Réduire + Transférer »). Sa souscription relève donc d'une **décision de gestion du dirigeant**, pas d'une priorité technique à arbitrer entre des mesures.
3. **Dépassement argumenté si la prime est souscrite : 4 300 €/an, soit +1 800 €/an (+72 %).** Argumentaire : (i) la perte de pic est chiffrée dans le dossier et porte sur plusieurs semaines de pic, alors que la saison rattrapable ne l'est pas ; (ii) le plan reste raisonnable en valeur absolue pour l'activité ; (iii) l'assurance est **réversible** (échéance annuelle), et son refus est une décision tracée, pas un oubli.

**Repli si le dirigeant refuse la prime** : R-09 reste traité en « Réduire » seul (monitoring, alertes, rate-limiting/CDN, runbook de rétablissement dimensionné au pic — action A5 de `SYNTHESE.md`), le **risque résiduel de R-09 n'est plus couvert par un transfert** et doit être acté comme tel ; point réexaminé à la revue de mars 2027 ou avant novembre 2027.

## Décision D-2026-01 — Prioriser les risques critiques et élevés, trancher la cyber-assurance comme dépassement argumenté

| Champ | Valeur |
|---|---|
| **Date** | 2026-10-04 |
| **Question** | Assurer le transfert de R-09 (cyber-assurance perte d'exploitation, ~2 000 €/an) ou rester sous l'enveloppe de 2 500 €/an ? (issue #20, arbitrage resté ouvert dans `05-traitement.md` § 3 et `06-validation.md`) |
| **Options examinées** | (a) tout financer (4 300 €) · (b) prioriser critiques/élevés, décaler le non critique · (c) assurance limitée à la RC · (d) accepter les risques faibles sans mesure |
| **Option retenue** | **(b)** |
| **Budget « Réduire »** | **~2 300 €/an** — dans l'enveloppe de 2 500 €/an (marge ~200 €) |
| **Cyber-assurance (transfert R-09)** | **~2 000 €/an** — **décision de gestion distincte**, à faire acter par le dirigeant de ShoPix |
| **Budget final si assurance souscrite** | **~4 300 €/an → dépassement argumenté de ~1 800 €/an (+72 %)** |
| **Si la prime est refusée** | R-09 en « Réduire » seul ; perte de CA de pic **non transférée** ; résiduel à acter ; réexamen à la revue semestrielle (prochaine : mars 2027) et avant novembre |
| **Incohérences écartées** | (c) : la RC ne couvre pas la perte d'exploitation et aucun montant de RC n'existe dans le dossier — R-09 perdrait son transfert validé. (d) : contredit `06-validation.md` § 2 et les résiduels déjà acceptés |
| **Responsable** | Analyste (Melvin RAIMBAULT) pour la proposition et la priorisation · dirigeant ShoPix pour la souscription de l'assurance |
| **Statut** | **Proposition d'analyste** — consignée ici pour la soutenance ; le registre et les fichiers d'analyse ne sont pas modifiés, `valide_par` reste humain |

> Justification à retenir devant le jury : *« je n'ai pas essayé de faire rentrer 4 300 € dans 2 500 €. J'ai payé 2 300 € de mesures sous enveloppe, et j'ai nommé la seule ligne — l'assurance — qui est une décision de gestion, pas une priorité technique. »*