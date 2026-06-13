#!/usr/bin/env python3
"""NOVA — KDP-Package-Builder + Publication-Readiness-Gate (Phase 4, DR-21).

Vorbild: BMAD-CW `assemble-kdp-package` (→ design-package.md) + `publication-readiness-checklist`.
Erzeugt die **druckfertige Spezifikation** (`design-package.md`) aus Story-Bible-Metadaten und läuft die
**maschinell prüfbaren** Punkte der Publication-Readiness-Checkliste (`nova/data/publication-checklist.md`) ab.

**Bewusste Grenze (= BMAD-CW):** Package, **kein** Auto-Upload; Cover-Bild + ISBN sind Autor-Aufgaben.
Diese Checkliste **blockt nicht** (I2) — harte Export-Blocker bleiben Provenienz + Continuity (siehe nova-publish).
**stdlib-only**, keine externe Dependency. Wiederverwendung der Metadaten-Logik aus `export_epub.py` (eine Quelle).

Exit-Codes:  0 = Package erzeugt (Warnungen erlaubt)      2 = Aufruf-/Pfadfehler
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_epub import _load_metadata, _slug, _strip_markup  # eine Quelle (DR-21)


def _comparables(project_dir: str) -> list[str]:
    prem = os.path.join(project_dir, "_memory", "story-bible", "premise.json")
    if os.path.isfile(prem):
        try:
            with open(prem, encoding="utf-8") as fh:
                p = json.load(fh)
            return (p.get("genre_audience") or {}).get("comparables", []) or []
        except (OSError, json.JSONDecodeError):
            pass
    return []


def run_checklist(project_dir: str, meta: dict) -> list[dict]:
    """Maschinell prüfbare Punkte (M) der Publication-Readiness-Checkliste. severity ∈ {ok, warning}."""
    f: list[dict] = []
    man = os.path.join(project_dir, "manuscript")
    files = sorted(glob.glob(os.path.join(man, "kapitel-*.md"))) or \
        sorted(x for x in glob.glob(os.path.join(man, "*.md")) if os.path.basename(x) != "README.md")

    f.append({"sev": "ok" if meta.get("title") and meta.get("author") else "warning",
              "item": "Titel + Autor", "msg": f"Titel='{meta.get('title')}', Autor='{meta.get('author')}'"})
    f.append({"sev": "ok" if files else "warning",
              "item": "≥1 Kapitel", "msg": f"{len(files)} Kapitel-Datei(en)"})

    # Kapitel-Überschriften (H1)?
    missing_h1 = []
    for p in files:
        with open(p, encoding="utf-8") as fh:
            if not any(ln.startswith("# ") for ln in _strip_markup(fh.read()).splitlines()):
                missing_h1.append(os.path.basename(p))
    f.append({"sev": "ok" if not missing_h1 else "warning", "item": "Kapitel-Überschriften (H1)",
              "msg": "alle Kapitel mit H1" if not missing_h1 else f"ohne H1: {', '.join(missing_h1)}"})

    f.append({"sev": "ok", "item": "TOC ableitbar", "msg": f"{len(files)} Einträge aus Kapitel-Liste"})
    f.append({"sev": "ok", "item": "Sprache (dc:language)", "msg": meta.get("lang", "?")})
    f.append({"sev": "ok" if meta.get("blurb") else "warning", "item": "Klappentext",
              "msg": (meta.get("blurb") or "fehlt — premise.logline setzen")[:70]})
    f.append({"sev": "ok" if meta.get("genre") else "warning", "item": "Genre/Schlüsselwörter",
              "msg": meta.get("genre") or "fehlt — premise.genre_audience setzen"})
    return f


def _design_package_md(project_dir: str, meta: dict, comps: list[str], findings: list[dict]) -> str:
    comp_str = ", ".join(comps) if comps else "—"
    rows = "\n".join(f"| {'✓' if x['sev']=='ok' else '⚠'} | {x['item']} | {x['msg']} |" for x in findings)
    nwarn = sum(1 for x in findings if x["sev"] == "warning")
    return f"""# Design-Package — {meta['title']}

> NOVA KDP-Package (Phase 4). **Druckfertige Spezifikation**, kein Auto-Upload (Autor lädt selbst zu KDP).
> Cover-Bild + ISBN sind Autor-Aufgaben. Quelle: Story-Bible-Metadaten + `nova/data/publication-checklist.md`.

## Metadaten
| Feld | Wert |
|---|---|
| Titel | {meta['title']} |
| Autor | {meta['author']} |
| Sprache | {meta['lang']} |
| Genre | {meta['genre'] or '—'} |
| Vergleichstitel (Comparables) | {comp_str} |

## Klappentext (Back-Cover-Blurb)
{meta['blurb'] or '*(kein Klappentext — premise.logline setzen)*'}

## Cover-Brief (für externe Cover-Erstellung)
- **Stimmung/Genre-Anker:** {meta['genre'] or 'n/a'}; Vergleichstitel-Look: {comp_str}.
- **Trim-Size (Platzhalter):** z. B. 12,7 × 20,32 cm (5×8") oder 13,34 × 20,32 cm (5,25×8") — vom Autor wählen.
- **Bleed:** 0,3175 cm (0,125") an den drei äußeren Kanten (KDP-Vorgabe).
- **Auflösung:** ≥ 300 DPI; **Farbprofil:** für Print CMYK, für eBook RGB.
- **Barcode/ISBN:** Platzhalter — KDP vergibt kostenlose ISBN ODER eigene eintragen.

## Back-Cover-Sektionen
1. **Klappentext** (siehe oben).
2. **Vergleichstitel/Positionierung:** {comp_str}.
3. **Autor-Bio:** *(vom Autor — Platzhalter)*.
4. **ISBN/Barcode-Zone:** unten rechts *(Platzhalter)*.

## Publication-Readiness-Check (maschinell, [M]-Punkte)
| Status | Punkt | Befund |
|---|---|---|
{rows}

**Ergebnis:** {nwarn} Warnung(en). Diese Checkliste blockt **nicht** (I2). Verbleibende `[A]`-Punkte
(Cover, ISBN, EPUBCheck, Impressum, Refusal/Kennzeichnung) sind **Autor-Freigaben** — siehe
`nova/data/publication-checklist.md`. Harte Export-Blocker (Provenienz + Continuity) laufen im `nova-publish *preflight`.
"""


def build_package(project_dir: str, out_path: str, title: str | None, author: str | None) -> int:
    meta = _load_metadata(project_dir, title, author)
    comps = _comparables(project_dir)
    findings = run_checklist(project_dir, meta)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        fh.write(_design_package_md(project_dir, meta, comps, findings))

    icon = {"ok": "✓", "warning": "⚠"}
    for x in findings:
        print(f"  {icon[x['sev']]} [{x['item']}] {x['msg']}")
    nwarn = sum(1 for x in findings if x["sev"] == "warning")
    print(f"\n  ✅ KDP-Package: {out_path}  ({nwarn} Warnung(en), kein Block — I2)")
    return 0


def _selftest() -> int:
    import tempfile
    print("Selftest: KDP-Package + Checkliste")
    ok = True
    with tempfile.TemporaryDirectory() as td:
        man = os.path.join(td, "manuscript")
        os.makedirs(man)
        with open(os.path.join(man, "kapitel-01.md"), "w", encoding="utf-8") as fh:
            fh.write("# Kapitel 1\n\nText.\n")
        sb = os.path.join(td, "_memory", "story-bible")
        os.makedirs(sb)
        with open(os.path.join(sb, "premise.json"), "w", encoding="utf-8") as fh:
            json.dump({"logline": "Eine Testlogline.",
                       "genre_audience": {"genre": "Testgenre", "comparables": ["Buch A", "Buch B"]}}, fh)
        out = os.path.join(td, "export", "design-package.md")
        rc = build_package(td, out, title="Selbsttest-Buch", author="Test-Autor")
        ok &= (rc == 0 and os.path.isfile(out))
        txt = open(out, encoding="utf-8").read()
        for sec in ["## Metadaten", "## Klappentext", "## Cover-Brief", "Publication-Readiness-Check",
                    "Selbsttest-Buch", "Eine Testlogline.", "Buch A, Buch B"]:
            present = sec in txt
            ok &= present
            if not present:
                print(f"    FEHLT: {sec}")
    print("\n" + ("OK" if ok else "FEHLGESCHLAGEN"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA KDP-Package-Builder (Phase 4)")
    ap.add_argument("project", nargs="?", help="Projektpfad (projects/<p>)")
    ap.add_argument("--title")
    ap.add_argument("--author")
    ap.add_argument("--out", help="Default: projects/<p>/export/design-package.md")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.project:
        ap.error("Projektpfad fehlt (oder --selftest).")
    if not os.path.isdir(args.project):
        print(f"FEHLER: Projektpfad nicht gefunden: {args.project}", file=sys.stderr)
        return 2
    out = args.out or os.path.join(args.project, "export", "design-package.md")
    return build_package(args.project, out, args.title, args.author)


if __name__ == "__main__":
    raise SystemExit(main())
