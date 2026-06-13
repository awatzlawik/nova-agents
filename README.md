# NOVA — `nova-agents`

> **NOVA 2.0** — Novel Orchestration & Validation Architecture.
> Ein autor-zentriertes, Drei-Akt-fundiertes Framework aus Claude-Code-Agenten zum Schreiben von Romanen.
> **Copilot, nicht Autopilot.** · *An author-centric, three-act framework of Claude Code agents for writing novels. Copilot, not autopilot.*

Mit einem Befehl installierst du 23 spezialisierte Agenten (Premise-Analyst, World-Builder, Plot-Architect, Line-Editor, Continuity-Checker, Publish …) plus Konfiguration, Templates und ein Beispiel-Projekt in einen Ordner deiner Wahl.

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

<sub>**EN — quick version.** Install with `npx github:awatzlawik/nova-agents` (works today) or `npx nova-agents` (after npm publish). The installer asks for **language** (`de`/`en`), **target folder** (default: current), and **your name** — then writes them into `nova/config.yaml` so every agent greets you by name. Non-interactive: `npx github:awatzlawik/nova-agents --dir . --lang en --name "Sam" --yes`. Then open the folder in Claude Code and run `/nova-orchestrator`.</sub>
