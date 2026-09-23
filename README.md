# Management de la Sécurité

Gestion de la sécurité du projet : suivi via GitHub Projects, issues, PRs et pipeline CI/CD orchestré par des agents opencode.

## Structure

- `.opencode/agents` — agents (orchestrateur, github-manager, security, backend, frontend, …)
- `.opencode/skills` — skills (project-context, git-workflow, machine-state, …)
- `documentation/` — documentation initiale et documents du projet
- `.github/workflows` — pipeline CI/CD

## Workflow

Toute évolution passe par une issue GitHub sur le board « Sécurité — Management », une branche dédiée et une PR liée à l'issue.

## Documentation

Voir [documentation/README.md](documentation/README.md).