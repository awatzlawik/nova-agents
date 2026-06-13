# NOVA — Elicitation-Baustein (Invariante 1: facilitation-over-generation)

> DER wiederverwendbare Frage-/HALT-Ablauf für **alle** Personas, die ein Template mit
> `elicit: true`-Sektionen füllen. Muster übernommen von BMAD (`tasks/create-doc.md`
> „Mandatory Elicitation Format" + `tasks/advanced-elicitation.md` + `data/elicitation-methods.md`),
> **verschärft um NOVAs SUGGEST-Disziplin:** die Persona bietet Vorschläge **zur Auswahl** an und
> füllt nie eigenmächtig aus — der Autor gibt ein.

## Wann
- Jede Persona-Sektion mit `elicit: true` (Templates tragen `workflow.elicitation: true`).
- Jede solche Sektion ist ein **HARD-STOP**: ohne Autor-Eingabe geht es nicht weiter.

## Ablauf je `elicit`-Sektion (HARD-STOP)
1. **Sektion benennen** — z. B. „Sektion 3/7: Magie-/Technik-System (WORLD-###)".
2. **Gezielt fragen**, was der Autor eingeben soll (aus der Template-`instruction`/`fields`):
   konkret, nicht ja/nein. Beispiel World-Builder: „Welcher Ort? Welche Regel/Magie? Welche **Kosten & Grenzen**?"
3. **Optional (SUGGEST):** 1–3 Vorschläge/Beispiele als **Angebot** anbieten — nie als Festlegung.
4. **Nummeriertes Menü 1–9 zeigen, dann HALT:**
   - **1** = Weiter zur nächsten Sektion (Proceed)
   - **2–9** = Elicitation-Methode anwenden (Liste unten)
   - Abschluss-Zeile: „**Wähle 1–9 oder gib deine Antwort/Frage direkt ein:**"
5. **WARTEN** — erst nach Autor-Eingabe weiter. **Nie** ja/nein-Fragen, **nie** das Feld selbst auto-ausfüllen.
   - Direkte Eingabe des Autors → übernehmen, Feld setzen, zur nächsten Sektion.
   - **Verstoß-Indikator:** Eine fertig befüllte Sektion ohne Autor-Eingabe verletzt diesen Baustein.

## Methoden-Ergebnis-Flow (nach Wahl 2–9)
1. Methode anwenden, Erkenntnisse/Vorschläge präsentieren.
2. Erneut anbieten: **1** Änderung übernehmen · **2** zurück zum Menü · **3** weiter nachfragen.
3. Schleife, bis der Autor **1** (Weiter) wählt.

## Elicitation-Methoden (Slots 2–9 — fiktions-kuratiert, DE/EN)
Die Persona wählt kontextpassend; Reihenfolge variabel, **Slot 1 immer „Weiter"**.

| # | Methode (DE) | Method (EN) |
|---|---|---|
| 2 | Erweitern / Verdichten (für Zielgruppe) | Expand / Contract for audience |
| 3 | Kritik & Verfeinerung | Critique & refine |
| 4 | Plot-Löcher / Risiken aufdecken | Identify plot holes / risks |
| 5 | Abgleich mit Thema & Prämisse | Assess alignment with theme/premise |
| 6 | Leser-Perspektive einnehmen | Reader / stakeholder roundtable |
| 7 | Figuren-/POV-Perspektive wechseln | Shift character / POV perspective |
| 8 | Gegenargument (Devil's Advocate) | Challenge from critical perspective |
| 9 | Varianten/Alternativen erzeugen | Tree of thoughts / variations |

## Regeln (NOVA-Strenge)
- **Default SUGGEST** (`nova/modes/modes.yaml`): nicht-generativ — kein Auto-Befüllen ohne Auswahl/Eingabe.
- **Numbered Options Protocol** immer; Sprache folgt `config.yaml → communication_language` (Invariante 6).
- **Provenienz:** Elicitation erzeugt **Planungsfelder** (`plan:`-Commit), keine Manuskript-Prosa
  (kein `NOVA:AI`-Markup in Phase 1).
- **Voice (Invariante 8):** Mimicry nur über vom Autor gelieferte Beispiele; „im Stil von [fremdem Autor]"
  → Refusal.

## Verweis
- Jede Persona referenziert diesen Baustein (Dependencies + Disziplin). Schema-Vorlage:
  `nova/_templates/persona-skill.template.md`. Modus-Baustein: `nova/modes/modes.yaml`.
