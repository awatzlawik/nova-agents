# `_EXAMPLE` — NOVA-Beispielprojekt (Skelett)

Leeres Autorprojekt-Gerüst + Integrations-Fixtures für Phase 0. Kopiere diesen Ordner
nach `projects/<dein-projekt>/` und befülle die Story Bible (ab Phase 1).

## Struktur
- `story-bible/` — Instanzen der `nova/templates/*` (versioniert, SSoT). Enthält `sample-beat-sheet.json` (Fixture).
- `manuscript/` — Prosa (ab Phase 2). Enthält `sample-chapter.md` (Provenienz-Fixture).
- `_memory/` — Sidecars, Continuity-Register, Summaries, Index, Gate-State (siehe `nova/conventions/memory.md`).

## Gates ausprobieren (Phase 0)
```bash
# Drei-Akt-Meilenstein-Check (zeigt 1 Warnung @ midpoint 58%)
python3 .claude/skills/nova-beat-percentage-check/scripts/check_marks.py \
  projects/_EXAMPLE/story-bible/sample-beat-sheet.json

# Provenienz-Export-Gate (1 saubere KI-Passage → Exit 0)
python3 .claude/skills/nova-provenance-export-gate/scripts/scan_ai_prose.py \
  "projects/_EXAMPLE/manuscript/*.md"
```
