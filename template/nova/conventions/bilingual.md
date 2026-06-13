# NOVA — Zweisprachigkeit DE/EN (Invariante 6)

> Muster übernommen von BMAD v6 (config-getriebene Sprache), erweitert um sprachspezifische
> Floskel-Listen.

## Steuerung (config-getrieben)
- `nova/config.yaml`:
  - `communication_language` — Sprache, in der Personas mit dem Autor sprechen.
  - `document_output_language` — Sprache erzeugter Dokumente.
  - `supported_languages: [de, en]`.
- Der Autor wählt die **Manuskriptsprache pro Projekt**.

## Strukturierte Mehrsprachigkeit in Artefakten
- Templates: `lang: [de, en]`; Sektionstitel/Instruktionen als `*_de` / `*_en`.
- Personas (Skills): Body referenziert `communication_language`; Greeting in dieser Sprache.

## Sprachspezifische Listen
- **AI-isms / Floskeln getrennt** je Sprache (`style-voice-guide-tmpl.yaml` → `ai_isms_de`, `ai_isms_en`).
  Deutsche Floskeln/Anglizismen separat von englischen erfasst.
- **Struktur-/Beat-Terminologie zweisprachig** gepflegt (z. B. „First Plot Point / Erster Wendepunkt").
  Glossar: `nova/data/craft-authorities.md`.

## Regel
- Craft-Quellen sind überwiegend englisch → Terminologie immer mit DE-Entsprechung im Glossar führen.
- Kein Mischen innerhalb eines Ausgabedokuments außer als ausgewiesenes Glossar/Term-Paar.
