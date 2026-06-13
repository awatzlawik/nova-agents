---
name: nova-continuity-db
description: "NOVA live continuity DB (Phase 2). Use when a writing persona needs the salient continuity facts for a scene (retrieval/context bundle), or to update last-seen tracking + rebuild the saliency index after a scene. Reads the same Phase-1 registers (continuity/*.json) — no ID renaming."
disable-model-invocation: true
allowed-tools: Bash
---

# NOVA — Continuity-DB live (Saliency-Retrieval + Tracking)

> **Modus:** mechanisch (Skript). **Muster:** NovelGenerator-Register (`Character`/`EstablishedFact`) +
> RecurrentGPT-Retrieval (Top-k saliente Records). **Vektor deferred** (memory.md) → lexikalische Salienz
> (ID-Overlap + Term-Overlap), stdlib-only, SentenceTransformer als dokumentierter Hook.
> **Invariante 4/7:** liefert nur **saliente** Fakten in den Kontext; liest die **unveränderten** Phase-1-IDs.

## Zwei Pfade
1. **Retrieval (Saliency, Lesepfad):** token-armes Kontext-Bündel für Drafting/Dialog/GHOSTWRITE.
   ```
   python3 .claude/skills/nova-continuity-db/scripts/continuity_db.py retrieve projects/<p> \
     --refs CHAR-001,WORLD-002 --pov CHAR-001 --query "Zeit zurückdrehen" -k 5
   ```
   (`--json` für maschinenlesbare Ausgabe.) Quelle: `continuity/{characters,world,plots}.json` + `summaries/*`.
2. **Update (Schreibpfad):** setzt `last_seen_scene` für `pov`/`bible_refs`-Figuren und baut den
   Saliency-Index `_memory/index/saliency.json` neu (memory.md: `index/` ab Phase 2 aktiv).
   ```
   python3 .claude/skills/nova-continuity-db/scripts/continuity_db.py update projects/<p> --scene SCENE-001
   ```
3. Selbsttest: `… continuity_db.py --selftest`.

## Interpretation
- **Exit 0** = Bündel/Update ok. **Exit 1** = inkonsistente Eingabe (unbekannte SCENE-ID / leere Anfrage).
- **Exit 2** = Pfad/JSON kaputt.

## Datenmodell (unverändert aus Phase 1)
- `characters.json`: `{id, name, status, relationships{}, development_arc[], voice_ref, last_seen_scene}`.
- `world.json`: `{id, name, type, rules[], kosten_grenzen}` · `plots.json`: `{id, name, status, related_characters[], key_events[], beats[]}`.

## Disziplin
- Schreibpfad ändert **nur** `last_seen_scene` + Index — keine inhaltliche Bible-Mutation, keine Prosa.
  Saliency ist Heuristik (ID > Term); semantische Salienz bleibt Vektor-Hook (Phase 3+).
