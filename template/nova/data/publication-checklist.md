# NOVA — Publication-Readiness-Checkliste (Phase 4, DE/EN)

> Format-Vorbild: BMAD-CW `publication-readiness-checklist` + `ebook-formatting-checklist`.
> **Konsument:** `nova-publish` / `build_kdp_package.py` läuft die **maschinell prüfbaren** Punkte (M) als
> ausführbare Checkliste ab (Exit-Befund); die **Autor-Punkte** (A) bleiben menschliche Freigabe (kein LLM-Häkchen).
> Diese Checkliste **blockt nicht** — sie ist Warn-/Hinweis-Ebene (I2). Harte Export-Blocker sind nur
> Provenienz (`nova-provenance-export-gate`) + Continuity (`nova-continuity-checker`).

## 1. Front-/Back-Matter
- [M] **Titel + Autor** ableitbar (`--title` / `config.yaml author_name`). · *Title + author present.*
- [A] **Widmung / Danksagung / Über den Autor** vorhanden? · *Dedication / acknowledgments / about-author present?*
- [A] **Copyright-/Impressum-Seite** vorhanden (rechtlich)? · *Copyright / imprint page present?*

## 2. Struktur & Navigation
- [M] **≥ 1 Kapitel** im Manuskript (`manuscript/kapitel-*.md`). · *At least one chapter.*
- [M] **Kapitel nummeriert / mit H1-Überschrift** (erste `# …`-Zeile je Datei). · *Chapter headings present.*
- [M] **Inhaltsverzeichnis (TOC)** ableitbar (EPUB `nav.xhtml` aus Kapitel-Liste). · *TOC linked (digital).*

## 3. Metadaten
- [M] **Sprache** gesetzt (`document_output_language` → `dc:language`). · *Language metadata set.*
- [M] **Klappentext/Beschreibung** (aus `premise.logline`). · *Blurb/description.*
- [M] **Genre/Schlüsselwörter** (aus `premise.genre_audience` + `comparables`). · *Genre/keywords.*
- [A] **ISBN** (vom Autor/Verlag/KDP vergeben — Platzhalter im Package). · *ISBN embedded.*

## 4. eBook-Format (EPUB)
- [M] **Valides EPUB-3** (mimetype zuerst+unkomprimiert, container.xml, content.opf, nav, ≥1 Kapitel-XHTML).
- [M] **Provenienz-Marker entfernt** im Export-Artefakt (Quelle behält sie). · *Provenance markers stripped in output.*
- [A] **EPUBCheck / Kindle Previewer** bestanden (externes Tool, Autor-Schritt). · *Passes EPUBCheck/Previewer.*
- [A] **Schriften lizenziert/entfernt · Bilder komprimiert + Alt-Text** (falls vorhanden). · *Fonts/images.*

## 5. Cover & KDP (Spezifikation, kein Auto-Upload)
- [A] **Cover** erstellt (Trim-Size/Bleed/DPI laut `design-package.md`). · *Cover meets KDP specs.*
- [A] **Back-Cover** (Klappentext + Comparables + Autor-Bio) bestätigt. · *Back-cover content.*
- [A] **Upload zu KDP/Store** (vom Autor; NOVA liefert nur das druckfertige Package). · *Author uploads.*

## 6. Provenienz & Recht (hart bzw. nicht verhandelbar)
- [M] **Pre-Export-Provenienz-Gate grün** (`nova-provenance-export-gate`): keine unmarkierte/defekte KI-Prosa (Rec. 5).
- [M] **Continuity-Gate grün** (`nova-continuity-checker`): keine Widersprüche (I5/I7).
- [A] **Refusal/Kennzeichnung** (I8): kein „im Stil von [fremdem Autor]"; Fine-Tuning nur mit Einwilligung.

**Legende:** `[M]` = maschinell geprüft (Skript) · `[A]` = Autor-Freigabe (menschlich).
