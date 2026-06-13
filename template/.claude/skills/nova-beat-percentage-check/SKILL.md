---
name: nova-beat-percentage-check
description: "NOVA three-act milestone gate. Use when the user asks to check beat placement / three-act percentages / Weiland marks against a beat sheet."
disable-model-invocation: true
allowed-tools: Bash
---

# NOVA — Drei-Akt-Meilenstein-Gate (CHECK)

> **Modus:** CHECK (nicht-generativ). Harte, **mechanische** Prüfung via Skript — kein LLM-Augenmaß.
> **Invariante 2:** Marken 12/25/37/50/62/75/88 %; Abweichung > ±5 % ⇒ **WARNUNG, kein Block**.

## Zweck
Prüft die IST-Position der Beats eines Beat-Sheets gegen die Weiland-SOLL-Marken
(`nova/data/craft-authorities.md`, gespiegelt in `nova/config.yaml`).

## Ausführung
1. Beat-Sheet liegt als JSON/YAML vor (Schema: `nova/templates/beat-sheet-tmpl.yaml`).
2. Führe aus (Lazy: Skript erst jetzt aufrufen):
   ```
   python3 .claude/skills/nova-beat-percentage-check/scripts/check_marks.py <beat-sheet> [--tolerance 5]
   ```
3. Selbsttest der Logik (ohne Datei): `… check_marks.py --selftest`
4. Interpretiere den Befund für den Autor:
   - `⚠ WARNUNG` = Beat weicht > ±Toleranz ab → dem Autor melden, **nicht** blockieren.
   - `✗ Fehler` = strukturell kaputtes Beat-Sheet (fehlende Werte) → zur Korrektur zurückgeben.
   - `✓ ok` = im Toleranzband.

## Disziplin
- Liefert ausschließlich Befund (CHECK). Erzeugt/ändert keine Prosa, kein Beat-Sheet.
- Abweichung ist nie ein Hard-Block (Autor-Souveränität, Overview Rec.3).
