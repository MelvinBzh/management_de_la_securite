# Étape 1 — Inventaire des actifs · cas « ShoPix »

> Analyse du **2026-09-24** — chaîne E21, étape 1 (identifier les actifs et leur valeur).
> Méthode : `ANSSI-CARTO-SI` — inventaire par **objets + attributs** (version, exposition, dépendances, besoins de sécurité), **vues métier/applicative/technique**, **sensibilité marquée** (public / interne / confidentiel / critique, RGPD).
> ⚠️ **Données fictives** : tout découle de `etude-de-cas.md` ; aucune donnée réelle.
> Hypothèses de valeur : CA **~15 000 €/trimestre** (donnée du cas) → **≈ 1 150 €/semaine** dérivé (15 000 ÷ 13) ; **≈ 3 450 €/semaine en pic** nov–déc (×3, cas §1) ; ~60 commandes/semaine ; budget sécurité **~2 500 €/an**. Les coûts de remplacement non fournis par l'étude de cas sont des **ordres de grandeur d'analyste**, signalés « est. ». Note : l'hypothèse initiale « ≈ 500 €/semaine » n'est **pas dérivable de l'étude de cas** et a été écartée au profit de la dérivation ci-dessus (contrôle e21 : « ~500 €/semaine » contredit le chiffre sourcé « ~15 000 €/trimestre »).

Besoins de sécurité (colonne DICT) : **D**isponibilité · **I**ntégrité · **C**onfidentialité · **T**raçabilité.

---

## 1. Vue d'ensemble — correspondance vues ANSSI ↔ actifs

| Vue (ANSSI-CARTO-SI) | Actifs | Sensibilité de la vue |
|---|---|---|
| Vue **métier** | Rôles et processus : **A-09 (admin), A-10 (préparateurs)**, A-11, A-13, A-14 | Critique / RGPD |
| Vue **applicative** | A-01, A-02, A-03, A-17, A-19 | Critique (exposition publique) |
| Vue **données** | A-04, A-05, A-06, A-07 | Critique / Confidentiel (RGPD) |
| Vue **architecture technique** | Secrets et dépendances : **A-08**, A-12, A-15, A-16, A-18 | Critique (secrets, dépendances) |

---

## 2. Actifs tangibles — données, logiciels, secrets

| ID | Actif | Type | Description (version · exposition · dépendances) | Valeur estimée | Sensibilité | DICT |
|---|---|---|---|---|---|---|
| A-01 | Site web (catalogue, panier, checkout) | Logiciel / service | PHP 8.0 (EOL, maintenu par hébergeur), front HTML/CSS/JS, SSL Let's Encrypt ; exposé Internet (F1) ; dépend de la base et des prestataires | Coût de remplacement (refonte équivalente) : **5–10 k€ (est.)** ; indisponibilité = perte de CA directe **≈ 1 150 €/semaine** (normale), **≈ 3 450 €/semaine** (pic fêtes, ×3) — dérivé du CA trimestriel | **Critique** | D, I, T |
| A-02 | API interne (commandes, stock) | Logiciel | Même VM que le site (F2) ; appelée en interne ; pas d'authentification distincte décrite | Faible coût seul, **indispensable aux commandes** (panier → validation) | Interne | D, I |
| A-03 | Back-office `/admin` | Logiciel | Template Bootstrap, login mot de passe simple, **pas de MFA**, sessions 30 j ; exposé Internet (F1) ; brute force observée 2024 | Conséquences d'une compromission : **totales** (droits admin) — point de rupture unique | **Critique** | D, I, C, T |
| A-04 | Base MySQL (clients, commandes, produits) | Données | MySQL 5.7, **1 seule base**, **1 compte `shopix`** ; cœur du métier (historique commandes) | Reconstruction d'un historique perdu : coût fort (**jours d'exploitation**, est.) ; indisponibilité = arrêt des ventes | **Critique** | D, I, C |
| A-05 | Données clients (nom, e-mail, adresse, tél., historique, mot de passe hashé **sha1**) | Données | Données **personnelles** (RGPD) ; mot de passe hashé avec un algorithme obsolète ; exposées via base, back-office, exports | Valeur pour un concurrent : **élevée** (fichier client réutilisable) ; amende RGPD possible (plafond art. 83 : 20 M€ / 4 % CA mondial, proportionnée) ; notification 72 h (art. 33) | **Confidentiel (RGPD)** | C, I |
| A-06 | Espace fichier (images produits, exports `.csv`) | Données | Exports `.csv` **complets** (clients + commandes), **non pseudonymisés**, conservés **24 mois** ; téléchargés « localement » (F5) ; images = catalogue | Perte des images = refonte du catalogue (est.) ; fuite d'un `.csv` = fuite du fichier client complet + mise en cause RGPD | **Confidentiel (RGPD)** | C, I |
| A-07 | Sauvegardes (`.sql` + `.zip`) | Données | Sauvegarde **manuelle hebdomadaire** (cron absent), **SQL en clair non chiffré**, FTP vers dossier du même hébergeur (F6) ; responsable de la perte de 2 jours de commandes en 2025 | Coût de reconstruction d'un sinistre : 2 jours de CA perdus — **≈ 330 € hors pic, ≈ 990 € en pic** (base : CA hebdomadaire dérivé ÷ 7 ; la période de l'incident 2025 n'est pas précisée par le cas) + charges refaites | **Critique** | D, I, C |
| A-08 | Clés API PayFlow & MailJet (fichier `.env`) | Données / secret | Stockées **en clair** dans le code ; PayFlow déjà versionnée sur GitHub 1 mois (2024) ; MailJet déjà piratée (spam 2 j, 2023) | Abus de paiement (PayFlow) ou envoi de spam au nom de la boutique (MailJet) ; perte de confiance prestataires/clients | **Critique (secret)** | C, I |
| A-17 | Bibliothèque PayFlow-SDK 2.1 | Logiciel (tiers) | **CVE-2023-XXXX connue, non patché** ; s'exécute dans le flux de checkout exposé Internet (F1) | Exploitation = compromission du checkout (paiement) ; correctif bloqué par… rien (composer audit jamais lancé) | Interne (exposition publique) | I, T |
| A-18 | Compte technique MySQL « shopix » (+ accès FTP) | Données / compte technique | Compte unique pour toute la base (A-04) ; accès FTP pour la sauvegarde ; pas de séparation d'accès documentée | Compromission du compte = accès à **toutes** les données ; mot de passe partagé entre les besoins (aucun autre compte décrit) | **Critique (secret)** | C, I |
| A-19 | Script de sauvegarde manuelle (dump MySQL + zip uploads) | Logiciel / processus | Lancé **manuellement par l'admin** ; **cron absent** (cause directe de la perte de 2025) ; envoi FTP | Son absence de fiabilité a déjà coûté 2 jours de commandes (2025) ; aucun log exploitable | Interne | D, I, T |

---

## 3. Actifs intangibles et services

| ID | Actif | Type | Description | Valeur estimée | Sensibilité | DICT |
|---|---|---|---|---|---|---|
| A-09 | Compte admin « Mélanie » | Rôle | Droits totaux, mot de passe simple, **pas de MFA**, sessions 30 j | Compromission = **compromission totale** de la boutique (produits, clients, exports, sauvegardes) | **Critique** | C, I, T |
| A-10 | Comptes préparateurs ×2 | Rôle | Accès limité aux commandes du jour + marquage « expédiée » ; mot de passe simple | Compromission = fuite de commandes/clients (RGPD) et fausses expéditions (intégrité) | Interne | C, I, T |
| A-11 | Consentement newsletter clients | Données (conformité) | Cases « décochent mal enregistrées » — **preuve de consentement incertaine** | Non-conformité RGPD (bases légales) : réclamations, sanction, désinscription non effective | Confidentiel (RGPD) | C, T |
| A-12 | Nom de domaine `shopix.example` (sous-domaines `api.`, `admin.`) | Service | SSL Let's Encrypt auto-renouvelé par l'hébergeur ; **1 avis de phishing** déjà reçu (abandonné) | Perte du domaine = perte d'identité en ligne et de CA (e-mails, clients perdus) ; détournement = usurpation (phishing clients) | **Critique** | D, I, C |
| A-13 | Disponibilité du site (saison nov–déc) | Service / intangible | Pas de monitoring, pas de WAF, pas de CDN, pas de redondance ; CA irrattrapable en période de fêtes | Perte de CA **directe et définitive** : **≈ 3 450 €/semaine en pic** (dérivé 15 000 € ÷ 13, ×3) ; un arrêt prolongé en période de fêtes = perte irrattrapable, chiffrée en dizaines de milliers d'euros | **Critique** | D |
| A-14 | Réputation / confiance clients | Intangible | Petite entreprise, réputation fragile ; antécédents : emailing piraté (2023), 1 avis de phishing | Perte durable de CA après incident public (clients qui ne reviennent pas) ; difficilement chiffrable mais élevé pour une TPE | **Critique** | C, D |
| A-15 | Hébergement mutualisé HostPlanet | Service (dépendance) | Mutualisé, pas de root, pare-feu non configurable, PHP/MySQL gérés par l'hébergeur, **isolation non vérifiable** (F3) | Défaillance ou réinitialisation hébergeur = perte de données (déjà arrivé en 2025) ; autres locataires = menace latérale | Interne (dépendance) | D, I |
| A-16 | Prestataires PayFlow / MailJet | Service (dépendance) | Paiement et e-mails externalisés, **hors périmètre serveur** (F4) ; accès par clés API (A-08) | Rupture d'un prestataire = checkout ou e-mails inopérants ; compromission côté prestataire = choc de réputation | Interne (dépendance) | D, I, C |

---

## 4. Actifs spécifiques « à ne pas oublier » (cas boutique en ligne)

- **Données clients (A-05)** : actif de plus forte valeur informationnelle — RGPD, valeur pour un concurrent, conséquence en cascade sur la réputation (A-14).
- **Compte administrateur (A-09)** : **point de rupture unique** — un seul compte admin, pas de MFA, sessions 30 j ; sa compromission neutralise toutes les autres protections.
- **Disponibilité saisonnière (A-13)** : le temps de décembre est **irrattrapable** — perte de CA définitive (≈ 1 150 €/semaine normal, ≈ 3 450 €/semaine en pic — dérivés du CA trimestriel).
- **Clés API (A-08)** : incidents déjà constatés — 2023 (MailJet piraté) et 2024 (clé PayFlow versionnée sur GitHub) ; stockage en clair dans `.env`.
- **Sauvegarde manuelle (A-19 / A-07)** : cause de la perte de 2 jours de commandes en 2025 ; cron absent, sauvegarde non chiffrée sur FTP du même hébergeur.

---

## 5. Notes de l'étape (manques et hypothèses)

- **Aucun actif matériel en propre** : pas de serveur, pas de poste décrit — le SI tient entièrement chez l'hébergeur mutualisé (F2/F3).
- **Point non décrit et signalé** : le **poste local de l'admin** (réception des exports `.csv`, lancement de la sauvegarde) n'est pas couvert par l'étude de cas → frontière F5 vers un poste non maîtrisé, à confirmer avec le dirigeant.
- **Coûts de remplacement non fournis** (site A-01, base A-04, images A-06) : valeurs « est. » à consolider à l'étape 6 ; seuls les ordres de grandeur CA (≈ 1 150 €/semaine — dérivé de 15 000 €/trimestre ÷ 13 — et ≈ 3 450 €/semaine en pic, ×3) sont des données du cas ; l'hypothèse « 500 €/semaine » a été écartée (non dérivable).
- **Éléments** hors inventaire volontairement : cartes bancaires (jamais stockées — tokenisation PayFlow), logements techniques côté prestataires (F4, hors périmètre).
- Garde-fous IA appliqués : aucune donnée réelle manipulée ; toutes les affirmations proviennent de l'étude de cas ou sont explicitement marquées comme estimations.

---

## 6. Sources

- `ANSSI-CARTO-SI` — *Cartographie du système d'information — Guide d'élaboration en 5 étapes* (ANSSI, 2018) : vues, objets + attributs, sensibilité, granularité. [base de connaissances `knowledge_base/README.md`]
- `etude-de-cas.md` — cas pilote « ShoPix » : §1 (CA, commandes, pic fêtes), §4 (données sensibles, sauvegarde), §6 (incidents 2023/2024/2025), §9 (dépendances versionnées), §10 (périmètre).
- Skill `analyse-risques` — étape 1 : types d'actifs (données/logiciel/matériel/service/rôle), valeur tangible et intangible.
- RGPD (art. 33 et 83) — référence réglementaire du contexte (mention textuelle, hors index des contre-mesures).