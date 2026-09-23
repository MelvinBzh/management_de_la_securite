# Prompt — Inventaire du homelab pour le projet E21

> À coller dans opencode (lecture seule). Le résultat est enregistré dans `.opencode/skills/machine-state/SKILL.md`.

```
Fais l'inventaire de mon environnement (homelab) dont le projet E21 « Des agents IA pour
analyser les risques » a besoin pour fonctionner, puis enregistre le résultat.

## Objectif
Le prototype = environnement opencode (agents + skills). Pour décider « quel LLM / quel outil
est utilisable », le projet doit connaître précisément la machine. Charge le skill machine-state
pour voir l'état actuel, puis mets-le à jour avec les infos réelles.

## À relever (commandes lecture seule, ne rien installer ni modifier d'autre)
1. **Système** : OS + version, machine, RAM libre/occupée (free -h), CPU, espace disque (df -h),
   swap, charge (uptime).
2. **Réseau** : IP locale, accès internet (test), ports ouverts en écoute (ss -tlnp), et si d'autres
   machines du homelab (VM/containers) sont joignables.
3. **LLM local** :
   - Ollama installé ? (commande ollama list) sinon est-il démarré ? quel port ?
   - Modèles disponibles + tailles (adapter à la RAM) ;
   - ping des alternatives : llama.cpp serv, vLLM, text-generation-webui, LM Studio.
   - GPU dispo ? (nvidia-smi / lspci)
4. **Clés API / comptes restants** (SANS les afficher ni les écrire) :
   - variables d'env (env / ~/.zshrc, ~/.bashrc, ~/.config/opencode/…) : OPENAI_API_KEY,
     ANTHROPIC_API_KEY, MISTRAL_API_KEY, GROQ_API_KEY, etc. → juste OUI/NON + nom du provider.
   - aucun secret ne doit être affiché, commité ni copié.
5. **Outils** : python3 + version, pip, node/npm, docker + containers actifs (docker ps),
   git + gh (connecté à quel compte ?), sqlite3, make.
6. **opencode** : version, config actuelle (~/.config/opencode/*) : modèle par défaut, agents ajoutés.
7. **Services pertinents** pour le projet : serveur DNS, reverse-proxy, stockage/sauvegarde,
   monitoring — uniquement ce qui peut servir au projet.

## Sortie
1. Un tableau récapitulatif compact (catégorie | valeur) dans ta réponse ;
2. Mise à jour de `.opencode/skills/machine-state/SKILL.md` avec ces valeurs réelles ;
3. Une conclusion claire en 3 lignes : quel mode LLM utiliser (ollama local / api / mock déterministe)
   pour que le prototype E21 « toujours fonctionnel », et que faut-il installer en priorité.
```