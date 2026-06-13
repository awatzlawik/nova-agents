---
name: nova-provenance-export-gate
description: "NOVA provenance pre-export gate. Use when the user wants to verify no broken/unmarked AI prose before exporting the manuscript. Hard CHECK: blocks on broken markers OR on accepted-but-unmarked AI prose (ledger↔markup reconciliation)."
disable-model-invocation: true
allowed-tools: Bash
---

# NOVA — Provenienz-Export-Gate (CHECK)

> **Modus:** CHECK (nicht-generativ). Harte, **mechanische** Prüfung via Skript.
> **Invariante 5 (nicht verhandelbar) / Overview Rec. 5:** KI- vs. Menschen-Prosa technisch trennbar; vor Export
> darf **keine** defekt/unmarkiert entstandene GHOSTWRITE-Provenienz durchrutschen.

## Zweck
Scannt Manuskript-Dateien nach NOVA-KI-Markern
(`<!-- NOVA:AI start … -->` … `<!-- NOVA:AI end -->`, siehe `nova/conventions/provenance.md`) und **blockiert**
den Export bei
1. **kaputten/unbalancierten Markern** (Marker-Balance, seit Phase 0), **und**
2. **akzeptierter, aber unmarkierter KI-Prosa** (Ledger↔Markup-Abgleich, **Phase 4 — aktiv**, Rec. 5).

Die **zwei Provenienz-Spuren** bleiben das Schema: Inline-Markup **und** `ai:`-Commit
(Trailer `NOVA-Provenance: ghostwrite`). Dieser Skill ist die **eine** Provenienz-Quelle — erweitert, nicht ersetzt.

## Ausführung
1. Nur Marker-Balance (Phase 0):
   ```
   python3 .claude/skills/nova-provenance-export-gate/scripts/scan_ai_prose.py "projects/<name>/manuscript/**/*.md"
   ```
2. **Mit Ledger↔Markup-Abgleich (Phase 4)** — eine der beiden Ledger-Quellen:
   ```
   # Datei-Ledger (auch vor dem ersten Commit nutzbar):
   … scan_ai_prose.py "projects/<name>/manuscript/**/*.md" --ledger projects/<name>/_memory/provenance/ledger.json
   # ODER aus ai:-Commits ableiten (Produktivpfad, sobald committet):
   … scan_ai_prose.py "projects/<name>/manuscript/**/*.md" --git
   ```
3. Selbsttest: `… scan_ai_prose.py --selftest` (Balance + Ledger-Reconcile inkl. Negativfall).

## Interpretation
- **Exit 0 / ✅** = Marker sauber **und** Ledger abgeglichen → Export darf weitergehen.
- **Exit 1 / ⛔ BLOCK** = defekte Marker **oder** `unmarked-ai` (akzeptierte KI-Prosa ohne Markup) **oder**
  `discarded`-Prosa eingeschlichen → Export **stoppen**, dem Autor die betroffenen Stellen melden.
- **Exit 2** = Aufruffehler (keine Dateien).

## Ledger-Regeln (Rec. 5)
- **`accepted`**-Eintrag ohne markierte Spanne, dessen Text aber im Manuskript steht ⇒ **BLOCK** (`unmarked-ai`).
- Text **gar nicht** im Manuskript ⇒ vom Autor überschrieben (erlaubt, `provenance.md §4`) — kein Block.
- **`discarded`**-Eintrag, dessen Text dennoch im Manuskript steht ⇒ **BLOCK** (verworfene KI-Prosa eingeschlichen).
- Match: `agent`+`ts` (== Markup-Attribute), bestätigt per Text-Hash.

## Pipeline-Position
- **Phase 4, Finalisierung.** Erster Schritt des `nova-publish`-**Preflight** (vor EPUB/KDP). Kombiniert mit dem
  Continuity-Gate (`nova-continuity-checker`) sind dies die **zwei** harten Export-Blocker (I5/I7); Struktur =
  Warnung, Voice = Flag (I2).

## Disziplin
- Liefert nur Befund; ändert kein Manuskript. Block ist hier **bewusst hart** (Invariante 5). Kein `*yolo`.

## Dependencies (on-demand)
- conventions: [ `nova/conventions/provenance.md` ]
- scripts: [ `.claude/skills/nova-provenance-export-gate/scripts/scan_ai_prose.py` ]
- reads: [ `projects/<p>/manuscript/*.md`, `projects/<p>/_memory/provenance/ledger.json` (optional), `ai:`-Commits ]
