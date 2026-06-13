# NOVA — Datei-/Namens-Konventionen (DE/EN-fähig, Invariante 3/6)

## Skills (Personas, Workflows, Gates)
- Verzeichnis: `.claude/skills/<skill-name>/SKILL.md` (projekt-nativ entdeckbar) bzw. Plugin-`skills/`.
- Skript-Bundles im Skill: `.claude/skills/<skill-name>/scripts/*.py`.
- Namensschema: **`nova-<id>`** (Präfix `nova-`).
  - Persona: `nova-<rolle>` (z. B. `nova-plot-architect`).
  - Gate/CHECK: `nova-<gegenstand>-check` / `nova-<…>-gate`.
  - GHOSTWRITE: `nova-ghostwrite` mit Frontmatter `disable-model-invocation: true`.
- Frontmatter: nur `name` + `description` (+ optional `disable-model-invocation`, `allowed-tools`).
- Phasen-Organisation in der Quelle (optional): Unterordner oder Namens-Infix `p0…p4`.

## Persona-Schema-Vorlage
- `nova/_templates/persona-skill.template.md` — Schema, aus dem neue Personas geklont werden.

## Framework-Daten (vom Skill konsumiert, nicht selbst Skill)
- `nova/templates/<id>-tmpl.yaml` · `nova/data/*.md` · `nova/modes/modes.yaml` · `nova/conventions/*.md`.
- Pfad-Referenz in Skills: `{project-root}/nova/...` (v6-Muster) bzw. relativer Skill-Pfad fürs Bundle.

## Autorprojekte
- `projects/<projekt>/story-bible/<id>.md` (Template-Instanzen) · `projects/<projekt>/manuscript/` ·
  `projects/<projekt>/_memory/` (siehe `memory.md`).

## Bible-IDs (Continuity-fähig, Phasen 2/3)
- Stabile IDs pro Eintrag: `CHAR-001`, `WORLD-001`, `SCENE-001`, `BEAT-<id>`, `TIME-001`, `STYLE-001`.
- Querverweise nutzen genau diese IDs (`bible_refs`, `beat_id`, `ziel_char_id`).

## Zweisprachigkeit in Dateien
- Strukturierte Felder mit Suffix `_de` / `_en`; Templates tragen `lang: [de, en]`.
- Sprache der laufenden Kommunikation/Ausgabe: `nova/config.yaml` (`communication_language`, `document_output_language`).
