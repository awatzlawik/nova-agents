# NOVA — `nova-agents`

> **NOVA 2.0** — Novel Orchestration & Validation Architecture.
> Ein autor-zentriertes, Drei-Akt-fundiertes Framework aus Claude-Code-Agenten zum Schreiben von Romanen.
> **Copilot, nicht Autopilot.** · *An author-centric, three-act framework of Claude Code agents for writing novels. Copilot, not autopilot.*

Mit einem Befehl installierst du 23 spezialisierte Agenten (Premise-Analyst, World-Builder, Plot-Architect, Line-Editor, Continuity-Checker, Publish …) plus Konfiguration, Templates und ein Beispiel-Projekt in einen Ordner deiner Wahl.

## 📑 Inhaltsverzeichnis

- [🚀 Installation](#-installation)
- [📦 Was wird installiert?](#-was-wird-installiert)
- [▶️ Nach der Installation](#️-nach-der-installation)
- [🎬 So arbeitest du mit NOVA — Phase für Phase](#-so-arbeitest-du-mit-nova--phase-für-phase)
  - [🧭 Das mentale Modell](#-das-mentale-modell-in-30-sekunden)
  - [Die Pipeline auf einen Blick](#die-pipeline-auf-einen-blick)
  - [🧪 Phase 0 — Fundament](#-phase-0--fundament-optional-zum-warmwerden)
  - [📐 Phase 1 — Planung](#-phase-1--planung-die-story-bible-bauen)
  - [✍️ Phase 2 — Schreiben](#️-phase-2--schreiben-prosa-entsteht--von-dir)
  - [🔍 Phase 3 — Review](#-phase-3--review-read-only-kritisch-nichts-wird-umgeschrieben)
  - [📦 Phase 4 — Finalisierung](#-phase-4--finalisierung-feinschliff--export)
  - [🧠 Die vier Modi](#-die-vier-modi-warum-nova-sich-bremst)
  - [🗂️ Was wo gespeichert wird](#️-was-wo-gespeichert-wird)
  - [⚡ Befehls-Spickzettel](#-befehls-spickzettel)
- [💻 Plattform-Hinweise](#-plattform-hinweise)
- [🛠️ Für Maintainer](#️-für-maintainer-auf-npm-veröffentlichen)
- [📄 Lizenz](#-lizenz)

---

## 🚀 Installation

### Voraussetzungen
- **[Node.js](https://nodejs.org) ≥ 16.7** (für `npx`). `node --version` zum Prüfen.
- **[Claude Code](https://claude.com/claude-code)** (CLI, Desktop, VS Code oder JetBrains) — dort laufen die Agenten.
- *Optional:* **Python 3** — nur einige mechanische Prüf-Agenten (Gates) nutzen kleine Python-Skripte.

### In einem Schritt (Windows & macOS & Linux)

Direkt von GitHub — funktioniert sofort, ohne npm-Veröffentlichung:

```bash
npx github:awatzlawik/nova-agents
```

Nach Veröffentlichung auf npm zusätzlich:

```bash
npx nova-agents
```

> ℹ️ Der kurze Name `nova` ist auf npm bereits vergeben — verwende daher `nova-agents`.

### Der Installer fragt dich drei Dinge

```
◆ NOVA  ·  npx nova-agents
  NOVA installieren — autor-zentriertes Schreib-Framework für Claude Code

? Sprache der Agenten? [de/en] (de)        ← de oder en
? In welchen Ordner installieren? (…)      ← Enter = aktueller Ordner
? Wie heißt du? (Anrede der Agenten) (Autor)  ← dein Name
```

1. **Sprache** (`de` / `en`) — wird in `nova/config.yaml` als `communication_language` und `document_output_language` gesetzt.
2. **Zielordner** — Default ist der aktuelle Ordner (Enter genügt). Existiert er nicht, wird er angelegt.
3. **Dein Name** — wird als `author_name` gespeichert. **Jeder Agent begrüßt dich danach mit deinem Namen.**

### Ohne Rückfragen (CI / Skripte)

```bash
npx github:awatzlawik/nova-agents --dir ./mein-roman --lang de --name "Anton" --yes
```

| Flag | Beschreibung | Default |
|------|--------------|---------|
| `--dir <pfad>`   | Zielordner | aktueller Ordner |
| `--lang <de\|en>`| Agenten- & Dokumentsprache | `de` |
| `--name <name>`  | Anrede / `author_name` | `Autor` / `Author` |
| `-y, --yes`      | Nicht-interaktiv, Defaults/Flags übernehmen | — |
| `-h, --help`     | Hilfe anzeigen | — |
| `-v, --version`  | Version anzeigen | — |

---

## 📦 Was wird installiert?

In deinen Zielordner:

```
<zielordner>/
├── .claude/
│   └── skills/            # 23 NOVA-Agenten (nova-orchestrator, nova-plot-architect, …)
├── nova/
│   ├── config.yaml        # Sprache + Name werden hier gesetzt
│   ├── modes/             # Modus-Baustein (SUGGEST/CRITIQUE/CHECK/GHOSTWRITE)
│   ├── conventions/       # Elicitation, Zweisprachigkeit, Provenienz, Begrüßung …
│   ├── templates/         # Story-Bible-Templates (Premise, World, Beat-Sheet …)
│   └── data/              # Craft-Autoritäten, Publikations-Checkliste
└── projects/
    └── _EXAMPLE/          # Starter-Gerüst für dein erstes Projekt
```

Vorhandene NOVA-Dateien im Zielordner werden überschrieben; andere Dateien (eigene Skills, dein Manuskript) bleiben unangetastet.

---

## ▶️ Nach der Installation

1. Öffne den Ordner in **Claude Code** (oder VS Code / JetBrains mit der Claude-Erweiterung).
2. Starte den Dirigenten:

   ```
   /nova-orchestrator
   ```

3. Jeder Agent begrüßt dich nun mit deinem Namen und in deiner Sprache, z. B.:

   > „Hallo Anton, ich bin NOVA Orchestrator 🎬 …"

Die Pipeline führt dich von **Planung** (Premise → World → Character → Beat-Sheet → Scene-List → Timeline) über **Schreiben** und **Review** bis zur **Finalisierung** (EPUB / KDP-Package).

---

## 🎬 So arbeitest du mit NOVA — Phase für Phase

> Diese Sektion ist dein **Werkbuch**. Sie erklärt jede der fünf Phasen, welche Agenten du in
> welcher Reihenfolge rufst, welche Befehle wichtig sind, was dabei entsteht und welches **Gate**
> dich in die nächste Phase lässt. Lies sie einmal ganz — danach genügt der Spickzettel ganz unten.

### 🧭 Das mentale Modell (in 30 Sekunden)

NOVA besteht aus **23 spezialisierten Agenten** (in Claude Code „Skills"). Du arbeitest immer nach
demselben Muster:

| Konzept | Was es bedeutet |
|---|---|
| **🚗 Copilot, nicht Autopilot** | **Du bist Pilot.** Kein Agent startet von allein, keiner schreibt ungefragt fertige Prosa. Du gibst frei, du entscheidest. |
| **`/agent` startet, `*command` steuert** | Einen Agenten rufst du mit Slash, z. B. `/nova-premise-analyst`. **Innerhalb** seiner Sitzung steuerst du ihn mit Stern-Befehlen, z. B. `*premise`, `*save`, `*exit`. |
| **🎬 Der Orchestrator routet** | `/nova-orchestrator` ist dein Dirigent: er sagt dir, **welcher** Agent als Nächstes dran ist und ob ein Gate offen ist — **startet ihn aber nicht selbst**. Du tippst den empfohlenen Slash-Befehl. |
| **🚦 Gates blocken Phasenwechsel** | Am Ende jeder Phase steht ein mechanisches **Gate** (Python-Check, kein KI-Augenmaß). Erst wenn es grün ist **und** du `*approve <phase>` gibst, öffnet sich die nächste Phase. |
| **📖 Die Story Bible ist die Wahrheit** | Alles Geplante landet als JSON in `projects/<dein-projekt>/_memory/story-bible/`. Diese „Bibel" ist die einzige Wahrheitsquelle — jede spätere Phase baut darauf auf. |
| **🟣 Provenienz ist Pflicht** | KI-geschriebene Prosa wird **immer** markiert (`<!-- NOVA:AI … -->`) und als `ai:`-Commit verbucht. Unmarkierter KI-Text kommt nicht durch den Export. |

### Die Pipeline auf einen Blick

```
  PHASE 1 · Planung         PHASE 2 · Schreiben       PHASE 3 · Review          PHASE 4 · Finalisierung
  ─────────────────         ───────────────────       ────────────────          ──────────────────────
  💡 Premise-Analyst        ✍️ Drafting-Assistant     📐 Developmental-Editor   👓 Beta-Reader  (Hinweis)
  🌍 World-Builder    ─▶    💬 Dialogue-Specialist ─▶ ✒️ Line-Editor        ─▶  🏷️ Genre-Specialist (Hinweis)
  🧠 Character-Psych.       🛡️ Style-Guardian          🔗 Continuity-Checker     📦 Publish → EPUB + KDP
  🎯 Plot-Architect         ┄ ✒️ Ghostwrite (Flag) ┄
  🗓️ Timeline-Keeper
        │                          │                          │                          │
   🚦 GATE 1                  🚦 GATE 2                  🚦 GATE 3                  🚦 GATE 4
   Planning-Gate            Continuity-Check           3× grün (R1·R2·R3)         Publish-Preflight
   (Bibel vollständig?)     (nach Ghostwrite)          (Struktur·Voice·Conti)    (Provenienz·Continuity)
        │                          │                          │                          │
   *approve 1    ──────────▶  *approve 2   ──────────▶  *approve 3   ──────────▶  *approve 4   ──▶  📕 EPUB
```

Jede Stufe **konditioniert auf die vorige**: Der Orchestrator empfiehlt einen Schritt erst, wenn die
Artefakte seiner Vorstufe existieren. Du kannst nicht schreiben, bevor die Bibel steht — und nicht
exportieren, bevor das Review grün ist.

---

### 🧪 Phase 0 — Fundament *(optional, zum Warmwerden)*

**Ziel:** NOVA kennenlernen, prüfen dass alles lädt, und dein erstes Projekt anlegen.

1. **Schema-Beweis ausprobieren** — ruf `/nova-hello-world`. Der Agent begrüßt dich beim Namen,
   zeigt mit `*help` sein Menü und antwortet auf `*ping` mit „🧪 pong". So siehst du, wie jeder NOVA-Agent
   tickt (nummerierte Menüs, Stern-Befehle, nicht-generativ).
2. **Die Gates an Beispieldaten sehen** — im mitgelieferten `projects/_EXAMPLE/` kannst du die
   mechanischen Prüfungen ohne eigenes Material testen:
   ```bash
   # Drei-Akt-Meilenstein-Check (zeigt 1 Warnung @ Midpoint 58 %)
   python3 .claude/skills/nova-beat-percentage-check/scripts/check_marks.py \
     projects/_EXAMPLE/story-bible/sample-beat-sheet.json

   # Provenienz-Gate (1 saubere KI-Passage → Exit 0)
   python3 .claude/skills/nova-provenance-export-gate/scripts/scan_ai_prose.py \
     "projects/_EXAMPLE/manuscript/*.md"
   ```
3. **Eigenes Projekt anlegen** — kopiere `projects/_EXAMPLE/` nach `projects/<dein-projekt>/`.
   Dieses Skelett enthält schon die richtige `_memory/`-Struktur (Story Bible, Continuity, Gates).

> 💡 **Immer dein Startpunkt danach:** `/nova-orchestrator` → `*plan <dein-projekt>` zeigt dir den
> Pipeline-Stand und nennt die **nächste offene Stufe**.

---

### 📐 Phase 1 — Planung *(die Story Bible bauen)*

**Ziel:** Aus deiner Idee eine vollständige, widerspruchsfreie **Story Bible** machen — die Grundlage
für alles Weitere. Alle Agenten hier sind **SUGGEST** (nicht-generativ): Sie fragen dich gezielt
(nummerierte Menüs, HALT pro Sektion) und **füllen nie eigenmächtig aus**. Du gibst ein, sie verdichten.

**Reihenfolge (fest — jede Stufe braucht die vorige):**

| # | Agent | Aufruf | Wichtigste Befehle | Ergebnis (in `_memory/story-bible/`) |
|---|---|---|---|---|
| 1 | 💡 **Premise-Analyst** | `/nova-premise-analyst` | `*logline` · `*premise` · `*critique` · `*save` | `premise.json` — Logline, Prämisse, zentrale Frage, Stakes, Thema, Genre |
| 2 | 🌍 **World-Builder** | `/nova-world-builder` | `*world` · `*rules` · `*continuity-sync` · `*save` | `world-bible.json` — Orte, Magie-/Technik-Systeme **mit Kosten & Grenzen**, Fraktionen |
| 3 | 🧠 **Character-Psychologist** | `/nova-character-psychologist` | `*character` · `*voice-sheet` · `*arc` · `*author-voice` · `*continuity-sync` | `CHAR-###.json` je Figur (Want/Need, Lie/Truth, Arc, Voice-Sheet) + `style-voice-guide.json` (deine Autorenstimme) |
| 4 | 🎯 **Plot-Architect** | `/nova-plot-architect` | `*beat-sheet` · `*check-structure` · `*scene-list` · `*continuity-sync` · `*save` | `beat-sheet.json` (Drei-Akt-Meilensteine) + `scene-list.json` (Szenen an Beats gebunden) |
| 5 | 🗓️ **Timeline-Keeper** | `/nova-timeline-keeper` | `*timeline` · `*threads` · `*continuity-audit` · `*continuity-sync` · `*save` | `timeline.json` + **Konsolidierung** von `continuity/{characters,world,plots}.json` |

**So läuft eine typische Stufe ab:** Du rufst z. B. `/nova-premise-analyst`. Er begrüßt dich, du tippst
`*premise`. Jetzt führt er dich **Sektion für Sektion** (Logline → Prämisse → zentrale Frage → Stakes →
Thema → Genre); pro Sektion bietet er Vorschläge an, zeigt ein nummeriertes Menü `1–9` und **wartet auf
dich**. Am Ende `*save`, dann `*exit`.

> 🎯 **Tipp:** `*author-voice` beim Character-Psychologist ist Gold wert — hier hinterlegst du
> Stilproben deiner eigenen Stimme. Style-Guardian und Ghostwrite ziehen später genau daraus
> (NOVA imitiert **nur** deine Beispiele — „im Stil von [fremdem Autor]" wird abgelehnt).

#### 🚦 Gate 1 — Planning-Gate

Wenn die Bibel steht, prüft ein **mechanisches Skript** ihre Vollständigkeit & Kohärenz:

```bash
python3 .claude/skills/nova-planning-gate/scripts/check_planning.py projects/<dein-projekt>
```

Geprüft wird: Prämisse vollständig? Meilenstein-Beats platziert? Figuren-Arcs an die drei Akte gemappt?
Jede Szene an einen **echten** Beat gebunden? Alle IDs (`CHAR-`/`WORLD-`) stabil?

- **Exit 0 ✅** → Gate erfüllt. Jetzt im Orchestrator freigeben: `/nova-orchestrator` → `*approve 1`.
- **Exit 1 ⛔** → Pflichtfeld fehlt → der Befund nennt dir genau, was nachzutragen ist. **Phase 2 bleibt zu.**
- **⚠ Warnung** (z. B. Drei-Akt-Abweichung > ±5 %) ist **nie** ein Block — du entscheidest (Invariante 2).

---

### ✍️ Phase 2 — Schreiben *(Prosa entsteht — von dir)*

**Ziel:** Das Manuskript schreiben. Die Agenten hier sind dein **Co-Writer**, kein Autopilot: Sie liefern
Vorschläge, Varianten, Kontext und Voice-Checks — **die fertigen Sätze schreibst du.** (Der einzige
generative Pfad ist der geflaggte Notausgang Ghostwrite, siehe unten.)

**Deine drei ständigen Begleiter (parallel, je nach Bedarf):**

| Agent | Aufruf | Wofür | Wichtigste Befehle |
|---|---|---|---|
| ✍️ **Drafting-Assistant** | `/nova-drafting-assistant` | Dein Haupt-Co-Writer: holt Szenen-Kontext, schlägt Fortsetzungs­richtungen & Alternativen vor | `*context <SCENE-ID>` · `*draft-scene` · `*continue` · `*alt` · `*summarize` · `*track` |
| 💬 **Dialogue-Specialist** | `/nova-dialogue-specialist` | Figuren-Dialog auf Stimm-Niveau (Lexik/Rhythmus/Tics aus dem Voice-Sheet) | `*dialogue <CHAR-ID>` · `*voice-check` · `*subtext` · `*two-hander` |
| 🛡️ **Style-Guardian** | `/nova-style-guardian` | Wacht über deine Stimme: scannt KI-Floskeln (DE/EN) & meldet Voice-Drift — **flaggt nur, schreibt nie um** | `*check-aiisms <datei>` · `*drift` · `*guard` · `*banlist` |

**Typischer Schreib-Loop für eine Szene:**
1. `*context <SCENE-ID>` (Drafting) — holt die salienten Continuity-Fakten + Szenenkarte.
2. Du schreibst. Bei Bedarf `*continue` (Richtungen), `*alt` (Formulierungs-Varianten), oder
   `*dialogue` (Dialogspezialist) für eine Figur.
3. `*check-aiisms` (Style-Guardian) gegen die fertige Szene laufen lassen.
4. `*summarize <SCENE-ID>` + `*track <SCENE-ID>` (Drafting) — Szene ins **rollende Gedächtnis**
   schreiben und den Continuity-Index aktualisieren.

> ⚙️ **Im Hintergrund** arbeiten zwei stille Infrastruktur-Agenten, die du nicht direkt rufst:
> **`nova-scene-summary`** (rollendes Kurz-/Langzeitgedächtnis) und **`nova-continuity-db`**
> (Saliency-Retrieval). Drafting & Co. nutzen sie automatisch über `*summarize`/`*track`.

#### ✒️ Der Notausgang: Ghostwrite *(optional, Flag, Default AUS)*

Bei echter Schreibblockade gibt es `/nova-ghostwrite` — den **einzigen** Agenten, der fertige Prosa
erzeugt. Er ist bewusst **abgeschaltet** (`config.ghostwrite.enabled: false`) und kann technisch
nicht von selbst starten:

- **Aktivierungs-Gate:** Vor *jedem* Einsatz fragt er ausdrücklich um Bestätigung für **diese eine** Szene.
- Erzeugt **Varianten 1–6** zur Auswahl, jede **mechanisch markiert** (`<!-- NOVA:AI … -->`).
- Du wählst: `*accept` · `*revise` · `*regenerate` · `*discard`. Angenommenes wird als `ai:`-Commit verbucht.
- **Automatischer Continuity-Nachlauf** (Gate 2) prüft jede übernommene Passage.

#### 🚦 Gate 2 — Continuity-Check

Greift nach Ghostwrite automatisch (und ist auf gedrafteten Szenen aufrufbar):

```bash
python3 .claude/skills/nova-continuity-check/scripts/check_continuity.py projects/<p> --scene <SCENE-ID> --file <manuskript>
```

- **Exit 0 ✅** → kein Widerspruch → Passage bleibt. Phase freigeben: `/nova-orchestrator` → `*approve 2`.
- **Exit 1 ⛔** → Widerspruch (z. B. tote POV, dangling ID) → Passage zurück an dich.

---

### 🔍 Phase 3 — Review *(read-only, kritisch, nichts wird umgeschrieben)*

**Ziel:** Den fertigen Entwurf auf drei Achsen prüfen — **Struktur, Stimme, Continuity**. Alle drei
Agenten sind **CRITIQUE/CHECK**: Sie melden Befunde, **ändern aber nichts** am Text. Du entscheidest,
was du überarbeitest.

| # | Agent | Aufruf | Achse | Befehle | Gate-Wirkung |
|---|---|---|---|---|---|
| R1 | 📐 **Developmental-Editor** | `/nova-developmental-editor` | **Struktur & Pacing** (Meilenstein-Δ in %, „sagging middle") | `*structure` · `*pacing` · `*sagging-middle` · `*deep-review` | ⚠️ **Warnung** — blockt nie (I2) |
| R2 | ✒️ **Line-Editor** | `/nova-line-editor` | **Satz & Stimme** (Wiederholungen, KI-Floskeln) | `*repetition` · `*aiisms` · `*line-edit` · `*proof` | 🚩 **Flag** — blockt nie |
| R3 | 🔗 **Continuity-Checker** | `/nova-continuity-checker` | **Continuity** (Zeit/Ort/Fakten/POV) | `*check` · `*scene` · `*deep-check` · `*report` | ⛔ **Block** bei echtem Widerspruch (Exit 1) |

> 🧠 **Deep-Review:** `*deep-review` / `*deep-check` starten **parallele read-only-Subagenten** (je Akt
> bzw. je Dimension Zeit·Ort·Fakten·POV), führen ihre Befunde zusammen und melden — ohne je etwas
> zu ändern. Ideal für den gründlichen Schlussdurchgang.

#### 🚦 Gate 3 — Review grün

Phase 4 öffnet erst, wenn **R1 · R2 · R3** durchlaufen sind: Struktur-Abweichungen sind Warnungen,
Voice-Treffer sind Flags — **nur ein Continuity-Widerspruch (R3, Exit 1) hält** den Übergang.
Danach: `/nova-orchestrator` → `*approve 3`.

---

### 📦 Phase 4 — Finalisierung *(Feinschliff & Export)*

**Ziel:** Optionales Leser-/Markt-Feedback einholen und dann ein **valides EPUB-3 + KDP-Package** bauen.

**Optionale Hinweis-Personas (blocken nichts — reines Feedback):**

| Agent | Aufruf | Wofür | Befehle |
|---|---|---|---|
| 👓 **Beta-Reader** | `/nova-beta-reader` | Erstleser-Simulation: Verständnis, Spannungskurve, Setup↔Payoff, Plot-Löcher | `*first-read` · `*plot-holes` · `*engagement-curve` · `*promise-audit` · `*report` |
| 🏷️ **Genre-Specialist** | `/nova-genre-specialist` | Genre-Audit, Tropes, Vergleichstitel, Markt-Positionierung | `*genre-audit` · `*trope-analysis` · `*comp-titles` · `*market-position` |

**Der Export:** `/nova-publish` — **mechanisch, nicht generativ** (formatiert nur vorhandenen Text):

1. `*preflight` — **harte Gate-Kette, Reihenfolge nicht verhandelbar:**

   | # | Prüfung | Skript | Wirkung |
   |---|---|---|---|
   | 1 | 🟣 **Provenienz** | `scan_ai_prose.py` | ⛔ **Block** bei unmarkierter/defekter KI-Prosa (I5) |
   | 2 | 🔗 **Continuity** | `check_timeline.py` | ⛔ **Block** bei Widerspruch (I7) |
   | 3 | 📐 **Struktur** | `check_structure.py` | ⚠️ Warnung — Export darf weiter |
   | 4 | ✒️ **Voice** | `check_repetition.py` + `scan_ai_isms.py` | 🚩 Flag — Export darf weiter |

2. `*export` — baut `projects/<p>/export/<slug>.epub` (valides EPUB-3, **KI-Marker im Artefakt entfernt**,
   Metadaten aus `premise.json` + `config.yaml`).
3. `*kdp` — baut `export/design-package.md` (Titel/Autor/Genre/Klappentext/Trim-Size-Platzhalter +
   Publication-Readiness-Checkliste).

> 📌 **Bewusste Grenzen:** Kein Cover-Bild, kein automatischer KDP-Upload. NOVA liefert die
> **druckfertige Spezifikation** — Cover erstellen und hochladen bleibt dein Schritt.

#### 🚦 Gate 4 — Publish-Preflight

Nur wenn Preflight-Schritte 1 & 2 grün sind, entstehen EPUB & Package. Danach final:
`/nova-orchestrator` → `*approve 4`. 🎉 **Dein Roman ist fertig.**

---

### 🧠 Die vier Modi (warum NOVA sich „bremst")

Jeder Agent läuft in einem **Modus**. Der Default ist immer **nicht-generativ** — das ist der Kern von
„Copilot, nicht Autopilot". Wechseln per `*mode <NAME>`.

| Modus | Generativ? | Was er tut |
|---|---|---|
| **SUGGEST** | ❌ | Vorschläge, Fragen, alternative Formulierungen am Rand — **keine** fertige Prosa. *(Default)* |
| **CRITIQUE** | ❌ | Analyse & Feedback zu vorhandenem Text/Plan. Bewertet, schreibt nicht um. |
| **CHECK** | ❌ | Quality-Gate gegen Checkliste/Regel (meist Python). Liefert einen Befund (pass/findings). |
| **GHOSTWRITE** | ✅ | **Einziger** generativer Modus. Nur als eigener Skill, Default AUS, pro Einsatz bestätigt, immer markiert. |

### 🗂️ Was wo gespeichert wird

```
projects/<dein-projekt>/
├── story-bible/                  # (kuratierte Template-Instanzen)
├── manuscript/                   # deine Prosa (.md) — ab Phase 2
└── _memory/
    ├── story-bible/              # 📖 SSoT: premise · world-bible · CHAR-* · beat-sheet · scene-list · timeline (JSON)
    ├── continuity/               # 🔗 characters · world · plots (Fakten-Register, ID-referenziert)
    ├── summaries/                # 🧠 rollendes Szenen-Gedächtnis (ab Phase 2)
    ├── index/                    # 🔎 Saliency-Index (ab Phase 2)
    ├── provenance/ledger.json    # 🟣 zweite Provenienz-Spur (Ledger ↔ Markup)
    └── gates/checkpoint_state.json  # 🚦 Phasen-Status + user_approved
```

Die **Story Bible** (`_memory/story-bible/`) ist die alleinige Wahrheitsquelle; alles andere ist davon
abgeleitet. IDs (`CHAR-001`, `WORLD-001`, `SCENE-001`, `BEAT-…`, `TIME-001`) verknüpfen alles miteinander.

### ⚡ Befehls-Spickzettel

**Der Dirigent — `/nova-orchestrator`** (dein Cockpit für jede Phase):

| Befehl | Wirkung |
|---|---|
| `*plan [projekt]` | Pipeline-Übersicht + **nächste offene Stufe** nennen |
| `*route` | Nummeriertes Menü: zu jeder Stufe den passenden `/nova-…`-Aufruf empfehlen |
| `*gate [projekt]` | Auf das phasen-richtige Gate verweisen und den Befund einordnen |
| `*status [projekt]` | Phasen-/Gate-Stand aus `checkpoint_state.json` melden (inkl. `user_approved`) |
| `*approve <phase>` | Nach **deiner** Freigabe das Gate öffnen (`user_approved: true`) |
| `*party <ids…>` | Mehrere Personas nacheinander in **einer** Sitzung moderieren |

**Überall gültig (in jedem Agenten):** `*help` (Menü) · `*mode <SUGGEST\|CRITIQUE\|CHECK>` (Modus wechseln) · `*exit` (Persona verlassen).

> 🚀 **Der schnellste Weg durch eine Session:** `/nova-orchestrator` → `*plan` → er nennt die nächste
> Stufe → du tippst den empfohlenen `/nova-…`-Befehl → arbeiten → `*save`/`*exit` → Gate prüfen →
> `*approve <phase>` → zurück zu `*plan`. Loop bis 📕.

---

## 💻 Plattform-Hinweise

- **Windows:** PowerShell, CMD oder Windows Terminal. Der Installer ist reines Node.js (keine Shell-Abhängigkeiten) und nutzt `readline` — Eingaben funktionieren überall.
- **macOS / Linux:** Terminal genügt.
- Farben werden automatisch deaktiviert, wenn die Ausgabe kein TTY ist oder `NO_COLOR` gesetzt ist.

---

## 🛠️ Für Maintainer: auf npm veröffentlichen

Damit `npx nova-agents` (ohne `github:`) funktioniert:

```bash
npm login
npm publish --access public
```

`package.json` → `files` liefert nur `bin/`, `template/`, `README.md`, `LICENSE` aus. Vor dem Publish lokal testen:

```bash
node bin/cli.js --help
npm pack --dry-run        # zeigt den Paketinhalt
```

---

## 📄 Lizenz

MIT © Anton Watzlawik. Siehe [LICENSE](./LICENSE).

---

<sub>**EN — quick version.** Install with `npx github:awatzlawik/nova-agents` (works today) or `npx nova-agents` (after npm publish). The installer asks for **language** (`de`/`en`), **target folder** (default: current), and **your name** — then writes them into `nova/config.yaml` so every agent greets you by name. Non-interactive: `npx github:awatzlawik/nova-agents --dir . --lang en --name "Sam" --yes`. Then open the folder in Claude Code and run `/nova-orchestrator`. The phase-by-phase workbook above (**🎬 So arbeitest du mit NOVA**) walks you through all five phases — Planning → Writing → Review → Finalization — with every agent, command and gate in order.</sub>
