# Agent Skills

Base de stock de skills pour agents IA (Claude Code, OpenCode, Claude.ai, etc.), au format [Agent Skills](https://github.com/anthropics/skills).

Chaque skill vit dans `.skills/<nom>/` (source de vérité) et est exposé à Claude Code via un symlink `.claude/skills/<nom>`. Voir [`CLAUDE.md`](CLAUDE.md) pour l'architecture et les commandes.

## Skills

```
.skills/
├── skill-creator/          # méta-skill Anthropic : créer, tester, optimiser des skills
├── local-agent-planner/    # Sonnet planifie → plan + tâches granulaires
└── local-agent-executor/   # l'agent local (Qwen/OpenCode) exécute les tâches une par une
```

### skill-creator

Le [`skill-creator`](.skills/skill-creator/SKILL.md) officiel d'Anthropic : créer un skill de zéro, améliorer un skill existant, lancer des évaluations, optimiser la description (triggering), packager en `.skill`.
Source : [anthropics/skills](https://github.com/anthropics/skills/tree/main/skills/skill-creator).

### local-agent-planner + local-agent-executor (paire)

Un workflow à deux modèles pour économiser un modèle fort et exploiter un modèle local :

- [`local-agent-planner`](.skills/local-agent-planner/SKILL.md) — un modèle fort (Claude Sonnet) découpe une tâche de code en un `plan.md` + des fiches de tâches **auto-suffisantes** sous `.opencode/plans/<nom>/`. Les tâches donnent le *contrat + les indications*, pas le code clé en main.
- [`local-agent-executor`](.skills/local-agent-executor/SKILL.md) — un petit modèle local (Qwen sur OpenCode) implémente ces tâches **une par une**, sans jamais charger tout le plan, pour garder son contexte/RAM léger.

Chaque nouveau skill créé avec `skill-creator` doit être ajouté dans `.skills/<nom>/` **avec son symlink** `.claude/skills/<nom>`.
