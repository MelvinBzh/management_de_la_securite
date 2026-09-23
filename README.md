# Management de la Sécurité

Projet E21 « Des agents IA pour analyser les risques » : système multi-agents opencode (orchestrateur + chaîne d'analyse) qui assiste un analyste de risques, avec suivi via GitHub Projects.

## Structure

- `.opencode/agents` — agents (orchestrateur E21, chaîne `e21-*`, github-manager, research, security)
- `.opencode/skills/*/SKILL.md` — skills (analyse-risques, frameworks STRIDE/LINDDUN/EBIOS-RM…, garde-fous-ia, registre, schémas)
- `knowledge_base/` — sources à ID stable (références des menaces et contre-mesures)
- `analyses/<date>_<cas>/` — dossier généré pour chaque analyse (registre + synthèse)
- `documentation/` — documentation technique et documents du sujet

## Workflow

Toute évolution passe par une issue GitHub sur le board « Sécurité — Management », une branche dédiée et une PR liée à l'issue.

## Documentation

Voir [documentation/README.md](documentation/README.md).