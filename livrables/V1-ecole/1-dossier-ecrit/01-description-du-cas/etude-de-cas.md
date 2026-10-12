# Étude de cas — Boutique en ligne (cas « pilote »)

> Cas d'exemple riche pour tester la chaîne d'agents E21. Description volontairement détaillée
> (architecture, acteurs, flux, données, contraintes, incidents) pour que chaque étape ait de quoi travailler.
>
> **Données personnelles : OUI** (`donnees_personnelles: true`) — RGPD applicable.

## 1. Contexte métier

« ShoPix » est une petite boutique en ligne (TPE) qui vend des produits imprimés (posters, t-shirts, goodies) sur commande. Créée en 2021, ~15 000 € de CA par trimestre, ~60 commandes/semaine en moyenne, pic à 3× en période de fêtes (nov–déc).

But de l'analyse : **livrer un registre des risques priorisé** (actifs, menaces, niveaux, contre-mesures) pour justifier un budget sécurité auprès du dirigeant, puis un plan de remédiation par ordre de priorité.

## 2. Architecture

```
Clients (Internet)
   │ HTTPS
   ▼
[ Hébergeur mutualisé "HostPlanet" ]
   ├─ Site web (catalogue + panier + checkout)     → PHP 8, front simple (HTML/CSS/JS)
   ├─ API interne (commandes, stock)               → même VM partagée
   ├─ Base MySQL (clients, commandes, produits)    → 1 seule base, 1 compte "shopix"
   ├─ Espace fichier (produits images, exports .csv commandes)
   └─ Back-office admin (/admin, template Bootstrap, login mot de passe simple)
        ↑── Admin cliente (1 personne)
        └── 2 préparateurs (accès limité aux commandes du jour)
   │
   ├──► Prestataire de paiement "PayFlow" (cartes, SEPA) — API REST + webhooks
   ├──► Prestataire e-mail "MailJet" (confirmations, newsletters)
   └──► Reversé : téléversement accès ftp, sauvegarde manuelle hebdo (1 .sql + 1 zip fichiers)
```

- Nom de domaine `shopix.example` (+ sous-domaines `api.`, `admin.`), SSL via Let's Encrypt auto-renouvelé par l'hébergeur.
- Pas de CDN, pas de WAF, pas de monitoring, pas de logging centralisé.
- Hébergement **mutualisé** : autres clients sur la même machine (isolation PHP par l'hébergeur, non vérifiable).

## 3. Acteurs et rôles

| Rôle | Droits | Compte |
|---|---|---|
| Admin cliente « Mélanie » | Tout (produits, commandes, clients, exports) | mot de passe simple, **pas de MFA**, sessions 30 j |
| Préparateur (×2) | Voir les commandes du jour, marquer « expédiée » | comptes dédiés, mot de passe simple |
| Client | Passer commande, suivre, se désinscrire de la newsletter | compte optionnel (e-mail + mot de passe) |
| Prestataires | PayFlow : webhooks commandes ; MailJet : envoi | clés API dans .env du site |

## 4. Données présentes / sensibles

- **Clients** : nom, e-mail, adresse de livraison, n° de téléphone, historique de commandes, mot de passe (hashé sha1 — ancien), consentement newsletter (cases décochent mal enregistrées).
- **Bancaires** : cartes **jamais stockées** (tokenisation côté PayFlow) — hors périmètre serveur.
- **Admin** : comptes, exports `.csv` contenant **tout** (clients + commandes) sans pseudonymisation, stockés 24 mois.
- Sauvegarde hebdo : un `.sql` complet + un `.zip` des uploads (SQL en clair, pas chiffré).

## 5. Flux principaux

1. **Commande** : client panier → checkout → PayFlow (token) → webhook « payment.ok » → validation commande → e-mail MailJet.
2. **Préparation** : préparateur lit les commandes du jour → marque « expédiée » → e-mail de suivi.
3. **Admin** : crée/modifie produits ; consulte clients ; **exporte** `.csv` localement.
4. **Sauvegarde** : admin lance manuellement un script (cron absent) qui dump MySQL + zip uploads → FTP vers un dossier du même hébergeur mutualisé.

## 6. Incidents passés / signaux

- 2023 : **emailing piraté** via MailJet (clé API stockée en clair dans le code) → envoi de spam au nom de la boutique (2 jours).
- 2024 : **tentative brute force** sur `/admin` détectée dans les logs HTTP (mille tentatives/24 h) — aucun lockout.
- 2025 : perte de **2 jours de commandes** (sauvegarde manuelle oubliée + disque hébergeur réinitialisé).
- Le site a déjà reçu **1 avis de phishing** sur le domaine (abandonné, non analysé).
- Clé API PayFlow stockée dans le **.env** versionné sur GitHub (repo privé, oubliée pendant 1 mois).

## 7. Exigences et contraintes

- **RGPD** : données personnelles côté EU ; pas de DPO, registre absent, mentions légales incomplètes, droit à l'oubli non automatisé.
- **PCI DSS** : cartes hors périmètre (tokenisation) mais le checkout manipule des pages de paiement embarquées.
- Contraintes hébergeur : **mutualisé**, PHP version gérée par l'hébergeur, pas de root, pare-feu non configurable.
- Budget sécurité envisagé : **2 500 €/an** (outillage + temps) — à justifier.
- Impératif : **rester concurrentiel côté prix**, site simple, pas d'équipe technique interne (prestataire au besoin).

## 8. Données d'entrée pour la chaîne (déjà collectées)

- Description, architecture, acteurs, flux : sections 1–5 ci-dessus.
- Documents à disposition : cette fiche + capture logs HTTP (brute force) + liste des extensions installées (voir ci-dessous).

## 9. Extensions / dépendances du site

| Composant | Version | Remarque |
|---|---|---|
| PHP | 8.0 (EOL, maintenu par hébergeur) | ancien |
| MySQL | 5.7 | hébergeur |
| Bibliothèque paiement PayFlow-SDK | 2.1 | CVE-2023-XXXX connue, **non patché** |
| Plugin impressions | 3.2.1 | non audité |
| Composer | présents, **jamais lancé `composer audit`** | |

## 10. Périmètre de l'analyse

- **Inclus** : site web public, back-office, base de données, flux paiement côté boutique, e-mails, sauvegardes, comptes admin.
- **Exclus** (mais frontières de confiance à tracer) : infrastructure PayFlow, MailJet, hébergeur (côté fournisseurs), postes clients.
- **Règles affaires** : la disponibilité du site est critique en décembre (sinon perte de CA directe) ; le respect RGPD est une exigence réglementaire ; la réputation est fragile (petite entreprise).

## 11. Ce qu'on attend des agents

Sur cette étude de cas, la chaîne doit produire un registre d'**au moins 8–10 risques** cohérents, chacun avec : actif + menace (catégorie grille) + probabilité + impact + niveau + traitement + contre-mesures sourcées (`knowledge_base/`) + `valide_par` après validation humaine. La méthode doit être **justifiée** (ex. STRIDE principal, LINDDUN pour les données personnelles, DREAD/CVSS pour la priorisation).