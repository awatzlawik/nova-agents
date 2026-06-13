---
name: nova-continuity-check
description: "NOVA continuity post-check (Phase 2, CHECK). Use to automatically validate a GHOSTWRITE passage / written scene against the continuity registers and three-act position (dangling IDs, dead-POV contradictions, milestone deviation). Also runs the false-positive benchmark for Recommendation 2."
disable-model-invocation: true
allowed-tools: Bash
---

# NOVA — Continuity-Nachprüfung (CHECK) — GHOSTWRITE-`post_check` + Benchmark

> **Modus:** CHECK (nicht-generativ). Harte, **mechanische** Prüfung via Skript.
> Der automatische Konsistenz-Check **nach** GHOSTWRITE (Overview §7 Schritt 7) — und die
> **Benchmark-Quelle** für Rec. 2 (< 5 % False-Positives).
> **Invariante 2:** Drei-Akt-Abweichung = **Warnung**, nie Block. Marken aus `nova-beat-percentage-check` (eine Quelle).

## Zweck
Validiert eine Szene/Passage mechanisch gegen `continuity/*.json` + Drei-Akt-Position:
1. **ID-Existenz** — `pov`/`bible_refs`/im Text genannte CHAR-/WORLD-IDs existieren (sonst dangling → Verstoß).
2. **Status/POV** — POV-Figur ist nicht tot (kein „toter spricht"-Widerspruch).
3. **Drei-Akt** — `scene.beat_id` → Weiland-Marke; Abweichung > ±5 % = Warnung.

Volle LLM-Widerspruchserkennung (Zeit/Ort/Fakten-Subtext, parallele Subagenten) = **Phase 3**.

## Ausführung
1. Passage einer Szene prüfen:
   ```
   python3 .claude/skills/nova-continuity-check/scripts/check_continuity.py projects/<p> \
     --scene SCENE-001 --file "projects/<p>/manuscript/kapitel-01.md"
   ```
2. Benchmark (FP-Rate gegen gelabeltes Fixture, Rec. 2):
   `… check_continuity.py --benchmark`
3. Selbsttest: `… check_continuity.py --selftest`

## Interpretation
- **Exit 0 / ✅** = ok (Warnungen sind kein Block) → GHOSTWRITE-Passage darf bleiben (markiert).
- **Exit 1 / ⛔** = Widerspruch (ID-/Status-Verstoß) → Passage zurück an den Autor.
- **Exit 2** = Pfad/JSON kaputt.

## Benchmark-Kopplung (Rec. 2)
- `--benchmark` druckt die False-Positive-Rate vs. `config.ghostwrite.benchmark_continuity_false_positive_threshold (0.05)`.
- Solange FP ≥ 5 % **oder** das repräsentative Korpus + der Phase-3-Checker fehlen, bleibt
  `config.ghostwrite.enabled:false` und **jede** GHOSTWRITE-Passage manuell nachzukontrollieren.

## Disziplin
- Liefert nur Befund (CHECK); ändert kein Manuskript. Block ist an echte Widersprüche gebunden (I5/I7),
  Positions-Abweichung bleibt Warnung (I2).
