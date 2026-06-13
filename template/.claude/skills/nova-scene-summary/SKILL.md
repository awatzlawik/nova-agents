---
name: nova-scene-summary
description: "NOVA scene-summary pipeline (Phase 2). Use when the author wants to record a per-scene summary into the live memory after writing a scene, or inspect the rolling short/long memory. RecurrentGPT short/long memory; the script does the deterministic memory I/O, the author/persona provides the summary text."
disable-model-invocation: true
allowed-tools: Bash
---

# NOVA — Szenen-Summary-Pipeline (Memory-I/O)

> **Modus:** mechanisch (Skript). Der **Inhalt** der Summary kommt vom Autor/von der Persona (SUGGEST,
> In-Context); dieses Skript besorgt nur die **deterministische Memory-I/O** (Phase-0-Philosophie).
> **Muster:** RecurrentGPT Kurz-/Langzeit-Memory (`short_memory`/`long_memory`). **Layout:** memory.md.

## Zweck
Schreibt nach jeder Szene eine kompakte Summary ins Phase-0-Memory-Layout und hält eine rollende
Kurz-Summary (token-arm, Invariante 4):
- `_memory/summaries/<SCENE-ID>.json` — Long-Memory-Record (`scene_id, beat_id, pov, akt, summary, key_facts[], salient_ids[], chars[]`).
- `_memory/summaries/_state.json` — `{ short_memory (rollend, ±400 Wörter), long_memory_order[] }`.

## Ausführung
1. Summary einer Szene speichern (Lazy: Skript erst jetzt):
   ```
   python3 .claude/skills/nova-scene-summary/scripts/summarize_scene.py write projects/<p> \
     --scene SCENE-001 --summary "<vom Autor verdichtete Szene>" \
     --key-facts "fakt1,fakt2" --salient "CHAR-001,WORLD-001"
   ```
   `beat_id`/`pov`/`akt` werden aus `story-bible/scene-list.json` automatisch ergänzt.
2. Memory-Übersicht: `… summarize_scene.py show projects/<p>`
3. Selbsttest: `… summarize_scene.py --selftest`

## Interpretation
- **Exit 0** = Record + Short-Memory aktualisiert.
- **Exit 1** = SCENE-ID nicht in `scene-list.json` (unbekannte Szene → korrigieren).
- **Exit 2** = Pfad/JSON kaputt.

## Kopplung
- Speist `nova-continuity-db retrieve` (Summaries gehen in den Saliency-Korpus) und das GHOSTWRITE-
  Kontext-Bündel (`summary_t`). IDs bleiben die Phase-1-Bible-IDs (keine Umbenennung).

## Disziplin
- Schreibt **keine** Manuskript-Prosa, nur Memory-Records. Generierung der Summary bleibt Autor-getrieben (I1).
