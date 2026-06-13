---
name: nova-ghostwrite
description: "NOVA GHOSTWRITE emergency exit (Phase 2). The optional 'finish-the-chapter' ghostwriter for writer's block. DISABLED by default (config.ghostwrite.enabled:false) and manual-only. Generates marked variants (purple markup), returns control (accept/revise/regenerate/discard), and auto-runs the continuity post-check. Every AI passage is mechanically marked + committed as ai:."
disable-model-invocation: true
allowed-tools: Bash, Read, Write, Edit
---

# NOVA — GHOSTWRITE ✒️ / Finish-the-Chapter (Notausgang, **Flag**)

> **Modus:** GHOSTWRITE (generativ) — der **einzige** generative Pfad in NOVA. `nova/modes/modes.yaml`.
> **Invariante 1:** `disable-model-invocation: true` ⇒ technisch **nicht** auto-aufrufbar; `config.ghostwrite.enabled:false`
> ⇒ verlangt **ausdrückliche** Autor-Bestätigung pro Einsatz. **Invariante 5:** jede Variante wird **mechanisch**
> markiert (`wrap_markup.py`) + als `ai:` committet — kein unmarkierter KI-Text möglich.
> **Muster:** Sudowrite/NovelCrafter-UX (Varianten 1–6, Purple-Markup, Annehmen/Überarbeiten/Neu/Verwerfen).

## Aktivierungs-Gate (vor JEDEM Einsatz)
1. Lies `nova/config.yaml` → `ghostwrite.enabled`.
2. **Ist es `false`** (Default): erkläre dem Autor, dass dies der geflaggte Notausgang ist (KI schreibt fertige
   Prosa), und **frage ausdrücklich um Bestätigung** für **diese eine** Szene/dieses Kapitel. Ohne klares „Ja" → **HALT**.
3. **Refusal (I8):** „im Stil von [fremdem, lebendem Autor]" → ablehnen. Voice nur aus Autor-/Figuren-Beispielen.

## 7-Schritt-Workflow (Overview §7)
1. **Explizite Aktivierung** — `*finish-chapter <SCENE-ID|range>`, nie automatisch (Gate oben).
2. **Kontext-Bündelung** — `nova-continuity-db retrieve` (Saliency) + Szenenkarte (`scene-list.json`) +
   `voice_sheet` (CHAR-*) + Autor-`style-voice-guide` + rollende Summary (`summaries/_state.json`) +
   die letzten ~1.000–20.000 Manuskript-Wörter + Beat-Position (`beat-sheet.json`).
3. **Voice-Matching (In-Context)** — analysiere `author_samples` + Figuren-`beispielzitate` (Lexik/Rhythmus)
   **vor** dem Schreiben. Fine-Tuning bleibt `config.voice.fine_tuning_enabled:false` (Einwilligung+Kennzeichnung).
4. **Varianten 1–6** — erzeuge mehrere Fortsetzungs-/Kapitel-Varianten zur **Auswahl** (Sudowrite-Muster).
5. **Eindeutige Markierung (mechanisch)** — jede Variante durch den Wrapper schicken:
   ```
   python3 .claude/skills/nova-ghostwrite/scripts/wrap_markup.py --agent nova-ghostwrite --variant <n> --text "<prosa>"
   ```
   → `<!-- NOVA:AI start … mode=GHOSTWRITE ts=… variant=n -->` … `<!-- NOVA:AI end -->`. Übernahme = `ai:`-Commit
   (`provenance.md`, Trailer `NOVA-Provenance: ghostwrite`).
6. **Kontroll-Rückgabe** — der Autor wählt **Annehmen / Überarbeiten / Neu-Generieren / Verwerfen**
   (`modes.yaml.GHOSTWRITE.return_control`). Markierung bleibt, bis der Autor die Passage selbst überschreibt.
7. **Continuity-Nachprüfung (automatisch)** — auf der erzeugten Passage:
   ```
   python3 .claude/skills/nova-continuity-check/scripts/check_continuity.py projects/<p> --scene <SCENE-ID> --file <manuskript>
   ```
   Exit 1 ⇒ Widerspruch → Passage zurück an den Autor. Auto-Übernahme **ohne** Nachkontrolle erst, wenn der
   Benchmark < 5 % FP liefert (Rec. 2, `nova-continuity-check --benchmark`) — bis dahin Flag `false` + Nachkontrolle.

## Commands
| # | Command | Aktion |
|---|---|---|
| 1 | `*help` | Menü zeigen |
| 2 | `*finish-chapter <SCENE-ID\|range>` | voller 1→7-Workflow (nach Aktivierungs-Gate) |
| 3 | `*variants <SCENE-ID> [n]` | nur Schritte 2–5: n Varianten (≤6), jede markiert |
| 4 | `*accept <variant>` | Variante ins Manuskript übernehmen (Markup behalten); `ai:`-Commit + Schritt 7 |
| 5 | `*revise <variant>` | Variante überarbeiten (bleibt markiert) |
| 6 | `*regenerate [hinweis]` | neue Varianten erzeugen |
| 7 | `*discard` | Varianten verwerfen, Kontrolle zurück |
| 8 | `*exit` | Skill verlassen |

## Disziplin (nicht verhandelbar)
- **Kein unmarkierter KI-Text:** Prosa verlässt diesen Skill **nur** durch `wrap_markup.py` (mechanische Garantie;
  Gegenprobe `nova-provenance-export-gate`/`scan_ai_prose.py`).
- **Kein Auto-Lauf:** ohne Aktivierungs-Gate + Bestätigung passiert nichts. Default `enabled:false` bleibt bestehen.
- **Provenienz-Commit:** angenommene Varianten ⇒ `ai:`-Commit mit Trailer. Continuity-Check ist Pflicht-Nachlauf.

## Dependencies (on-demand)
- conventions: [ `nova/conventions/provenance.md`, `nova/conventions/elicitation.md` ]
- data: [ `nova/config.yaml`, `nova/modes/modes.yaml` ]
- scripts: [ `.claude/skills/nova-ghostwrite/scripts/wrap_markup.py` ]
- skills: [ `nova-continuity-db` (retrieve), `nova-continuity-check` (post_check), `nova-provenance-export-gate` (Gegenprobe) ]
- reads: [ `_memory/story-bible/{scene-list,beat-sheet,CHAR-*,style-voice-guide}.json`, `_memory/summaries/*`, `manuscript/*` ]
- writes: [ `projects/<p>/manuscript/*.md` (markiert) ]
