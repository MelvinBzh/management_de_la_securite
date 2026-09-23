# Étape 1 — Inventaire des actifs (cas ShoPix)

> Produit par la chaîne E21 (étape 1 · identifier les actifs). Valeurs estimées à partir des seuls éléments de l'étude de cas (CA ~15 000 €/trimestre, ~60 commandes/semaine, pic ×3 en nov–déc, budget sécurité 2 500 €/an).

## Actifs tangibles

| ID | Actif | Type | Description | Valeur estimée | Sensibilité |
|---|---|---|---|---|---|
| A-01 | Site web (catalogue, panier, checkout) | Logiciel / service | PHP 8 (EOL), front HTML/CSS/JS, SSL Let's Encrypt | Coût de refonte : 5–10 k€ ; indisponibilité = perte de CA directe (~500 €/semaine, ×3 en fêtes) | Critique |
| A-02 | API interne (commandes, stock) | Logiciel | Même VM partagée que le site | Faible coût seul, mais indispensable aux commandes | Interne |
| A-03 | Back-office `/admin` | Logiciel | Template Bootstrap, login mot de passe simple, sans MFA | Fonction clé de l'exploitation | Critique |
| A-04 | Base MySQL (clients, commandes, produits) | Données | 1 seule base, 1 compte `shopix`, MySQL 5.7 | Coût de reconstruction fort (historique commandes) ; cœur métier | Critique |
| A-05 | Données clients (nom, e-mail, adresse, tél., historique, mot de passe hashé sha1) | Données | Données **personnelles** — RGPD | Valeur pour un concurrent : élevée (fichier client) ; amende RGPD possible | **Confidentiel (RGPD)** |
| A-06 | Espace fichier (images produits, exports .csv) | Données | Exports `.csv` contenant **tout** (clients + commandes), sans pseudonymisation, conservés 24 mois | Réutilisation malveillante ; perte des images = refonte catalogue | **Confidentiel (RGPD)** |
| A-07 | Sauvegardes (`.sql` + `.zip`) | Données | Sauvegarde manuelle hebdomadaire, SQL en clair non chiffré, FTP vers dossier du même hébergeur | Coût de reconstruction d'un sinistre : 2 jours de commandes perdus en 2025 | Critique |
| A-08 | Clés API PayFlow & MailJet (`.env`) | Données / secret | Stockées en clair dans le code ; déjà versionnées une fois sur GitHub (oubliée 1 mois) | Abus de paiement / spam au nom de la boutique | **Critique (secret)** |

## Actifs intangibles / services

| ID | Actif | Type | Description | Valeur estimée | Sensibilité |
|---|---|---|---|---|---|
| A-09 | Compte admin « Mélanie » | Rôle | Droits totaux, mot de passe simple, **pas de MFA**, sessions 30 j | Compromission = compromission totale | Critique |
| A-10 | Comptes préparateurs ×2 | Rôle | Accès limité aux commandes du jour | Compromission = fuite de commandes/clients | Interne |
| A-11 | Consentement newsletter clients | Données | Cases « decochent mal enregistrées » — conformité incertaine | Non-conformité RGPD (preuve de consentement) | Confidentiel (RGPD) |
| A-12 | Nom de domaine `shopix.example` + sous-domaines | Service | `shopix.example`, `api.`, `admin.` ; déjà 1 avis de phishing reçu | Perte du domaine = perte d'identité en ligne | Critique |
| A-13 | Disponibilité du site (saison nov–déc) | Service / intangible | Caisses en période de fêtes ; pas de monitoring, pas de WAF, pas de CDN | Perte de CA directe (~1 500 €/semaine en pic) | Critique |
| A-14 | Réputation / confiance clients | Intangible | Petite entreprise, réputation fragile ; 1 avis de phishing non analysé | Perte durable de CA | Critique |
| A-15 | Hébergement mutualisé HostPlanet | Service (dépendance) | Mutualisé, pas de root, pare-feu non configurable, isolation non vérifiable | X autres clients sur la même machine | Moyenne |
| A-16 | Prestataires PayFlow / MailJet | Service (dépendance) | Paiement / e-mails externalisés — hors périmètre côté serveur | Rupture d'un prestataire = site partiellement inopérant | Moyenne |

## Actifs spécifiques « à ne pas oublier » (cas boutique en ligne)

- **Données clients (A-05)** : actif de plus grande valeur informationnelle — RGPD + réutilisation par un tiers.
- **Compte administrateur (A-09)** : point de rupture unique — pas de MFA, un seul compte admin.
- **Disponibilité saisonnière (A-13)** : le temps de décembre est irrattrapable (perte de CA définitive).
- **Clés API (A-08)** : incidents 2023 (MailJet piraté) et 2024 (clé PayFlow versionnée) déjà constatés.

## Notes de l'étape

- **Aucun actif matériel** détenu en propre (pas de serveur physique) — tout est hébergé mutualisé.
- **Ne pas oublier** : autres clients du même hébergement mutualisé (frontière F4) — menace latérale réelle mais non vérifiable.