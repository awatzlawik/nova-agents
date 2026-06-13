# NOVA — Begrüßung mit Autorennamen (Invariante 1 + 6)

> Jede Persona begrüßt den Autor **beim Namen** und in seiner Sprache. Name und Sprache sind
> config-getrieben (wie bei BMAD v6) — gesetzt einmalig durch den Installer (`npx nova-agents`),
> jederzeit in `nova/config.yaml` änderbar.

## Steuerung (config-getrieben)
- `nova/config.yaml`:
  - `author_name` — Anrede des Autors (z. B. „Anton"). Vom Installer gesetzt; pro Projekt überschreibbar.
  - `communication_language` — Sprache der Begrüßung (DE/EN, siehe `bilingual.md`).

## Regel für Personas (Skills)
- Im Schritt **On Activation** liest die Persona `author_name` (+ `communication_language`) aus `nova/config.yaml`.
- Die Begrüßung adressiert den Autor namentlich, z. B.:
  - DE: „Hallo {{author_name}}, ich bin NOVA <Rolle> <Symbol>."
  - EN: „Hi {{author_name}}, I'm NOVA <Role> <symbol>."
- `{{author_name}}` ist ein Platzhalter: zur Laufzeit durch den Wert aus der Config ersetzt.
- Fehlt `author_name` oder steht auf dem Default „Autor"/„Author", wird neutral begrüßt (kein Name erfunden).

## Geltungsbereich
- Gilt für alle **Persona-Skills** (SUGGEST/CRITIQUE-Personas mit `## On Activation`).
- Mechanische **CHECK-/Skript-Skills** (z. B. `nova-planning-gate`, `nova-continuity-check`) liefern einen
  Befund statt einer Begrüßung und sind ausgenommen.
