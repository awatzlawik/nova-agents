# NOVA — Provenienz-Konvention (Invariante 5, nicht verhandelbar)

KI- vs. Menschen-Prosa muss jederzeit technisch trennbar sein — über **zwei** redundante Spuren:
Inline-Markup **und** Git-Commit-Konvention. Durchgesetzt vom `nova-provenance-export-gate`.

## 1. Inline-Markup (maschinell scanbar)

```
<!-- NOVA:AI start agent=<skill-id> mode=GHOSTWRITE ts=<ISO-8601> -->
… KI-generierte Prosa …
<!-- NOVA:AI end -->
```
- Rendering-Hinweis: „purple" (Sudowrite-UX-Anker) — KI-Text optisch markiert, bis der Autor ihn
  selbst überschreibt.
- Marker dürfen **nicht** verschachteln; jedes `start` braucht genau ein `end`
  (geprüft von `scan_ai_prose.py`).
- Attribute: `agent`, `mode`, `ts` (Pflicht); optional `variant=<1..6>`.

## 2. Git-Commit-Konvention

| Typ | Bedeutung |
|---|---|
| `ai:` | GHOSTWRITE-Prosa (KI-generiert) |
| `human:` | Autorprosa |
| `plan:` | Story-Bible / Planungsartefakte |
| `gate:` | Checklisten-/Gate-Ergebnisse |
| `chore:` / `docs:` | Framework / Doku |

- KI-Commits zusätzlich Trailer: `NOVA-Provenance: ghostwrite`.

## 3. Pre-Export-Gate (hart)

- `nova-provenance-export-gate` scannt vor jedem Export.
- **Block (Exit 1)** bei defekten/unbalancierten Markern.
- Phase-4-Ausbau: Abgleich Commit-Ledger ↔ Markup — akzeptierte, aber **unmarkierte** KI-Prosa ⇒ Block
  (Overview Rec.5).

## 4. GHOSTWRITE-Kopplung
- GHOSTWRITE (`config.ghostwrite.enabled: false`) erzeugt Output **nur** mit Markup **und** `ai:`-Commit
  (erzwungen in `nova/modes/modes.yaml` → GHOSTWRITE.requires).
