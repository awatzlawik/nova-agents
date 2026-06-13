---
name: nova-planning-gate
description: "NOVA planning gate (Phase 1, CHECK). Use when the author wants to verify a project's story bible is complete & coherent before moving to writing (Phase 2): premise complete? milestone beats placed? character arcs mapped to acts? scenes bound to real beats? bible-refs/IDs stable?"
disable-model-invocation: true
allowed-tools: Bash
---

# NOVA — Planungs-Gate (CHECK)

> **Modus:** CHECK (nicht-generativ). Harte, **mechanische** Prüfung via Skript gegen die **realen**
> Template-Felder — kein LLM-Augenmaß. **Invariante 7:** hält den Übergang Phase 1→2.
> **Invariante 2:** Drei-Akt-Abweichung ist **Warnung, kein Block** (Autor entscheidet).
> Format-Vorbild: BMAD-Checklisten; Strenge wie die Phase-0-Gates.

## Zweck
Prüft die Story-Bible-Shards eines Projekts (`projects/<p>/_memory/story-bible/*.json`):
1. **Prämisse vollständig?** `premise.json`: logline, premise_paragraph, central_question, stakes.
2. **Beats platziert?** `beat-sheet.json`: Meilenstein-Beats haben `ist_prozent` (Abweichung > ±5 % = Warnung).
3. **Arcs an Akte gemappt?** `CHAR-*.json`: `arc_mapping.{akt1_zustand, akt2_wende, akt3_zustand}`.
4. **Szenen↔Beats integer?** `scene-list.json`: jede `scene.beat_id` existiert im Beat-Sheet.
5. **Bible-Refs/IDs stabil?** `scene.pov`/`bible_refs` → existierende CHAR-/WORLD-IDs.

## Ausführung
1. Selbsttest der Logik (ohne Datei):
   ```
   python3 .claude/skills/nova-planning-gate/scripts/check_planning.py --selftest
   ```
2. Gegen ein Projekt (Lazy: Skript erst jetzt):
   ```
   python3 .claude/skills/nova-planning-gate/scripts/check_planning.py projects/<projekt>
   ```
3. Befund einordnen:
   - **Exit 0 / ✅** = Gate erfüllt → mit `nova-orchestrator *approve 1` freigeben, dann Phase 2.
   - **Exit 1 / ⛔** = Pflichtartefakt unvollständig/inkohärent → dem Autor die fehlenden Felder melden,
     Phasenübergang hält (kein Phase-2-Start).
   - **Exit 2 / ✗** = Story-Bible strukturell kaputt (JSON) → zur Korrektur zurückgeben.
   - `⚠ Warnung` (z. B. Drei-Akt-Abweichung) ist **nie** ein Block.

## Kopplung
- Re-nutzt die Weiland-Marken/Toleranz von `nova-beat-percentage-check` (eine Quelle der Wahrheit;
  Import mit inline-Fallback). Endgültiges Annehmen-Gate ist `checkpoint_state.json` → `user_approved`
  (gesetzt vom Orchestrator nach Autor-Freigabe, Invariante 7).

## Disziplin
- Liefert nur Befund (CHECK); ändert keine Bible. Block ist hier **bewusst** an Pflichtartefakte
  gebunden (I7), Drei-Akt-Abweichung bleibt Warnung (I2).
