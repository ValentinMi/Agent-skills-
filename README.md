# Agent Skills

Base de stock de skills pour agents IA (Claude Code, Claude.ai, etc.), au format [Agent Skills](https://github.com/anthropics/skills).

## Structure

```
.skills/
└── skill-creator/   # Meta-skill officiel d'Anthropic pour créer, tester et améliorer des skills
```

## skill-creator

Le skill [`skill-creator`](.skills/skill-creator/SKILL.md) permet de :

- Créer un nouveau skill à partir de zéro (interview, rédaction du `SKILL.md`, cas de test)
- Modifier/améliorer un skill existant
- Lancer des évaluations (avec/sans skill) pour mesurer l'impact
- Optimiser la description d'un skill pour améliorer son déclenchement (triggering)
- Packager un skill en fichier `.skill` distribuable

Source : [anthropics/skills — skills/skill-creator](https://github.com/anthropics/skills/tree/main/skills/skill-creator).

Chaque nouveau skill créé avec `skill-creator` devrait être ajouté dans `.skills/<nom-du-skill>/`.
