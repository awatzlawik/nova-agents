#!/usr/bin/env python3
"""NOVA — AI-isms-/Floskel-Scanner (Phase 2, DR-11).

Mechanischer Stil-Wächter: sucht in Manuskript-Dateien die **sprachspezifischen** Verbots-Phrasen
aus der Story Bible (Invariante 6, DE/EN getrennt):

  - style-voice-guide.json → ai_isms_de[] / ai_isms_en[]   (Autor-Floskel-Verbotsliste)
  - CHAR-*.json → voice_sheet.verbotsliste                 (figurenspezifische Verbote)

Substring-Match (case-insensitiv, an Wortgrenzen wo sinnvoll) — kein NLP, bewusst einfach/erklärbar.
Semantische Voice-Drift bleibt CRITIQUE-Aufgabe der Persona (LLM, kein Skript).

Wichtig (Invariante 2 / Autorhoheit über Stil): Treffer sind **Warnungen/Flags**, **kein** Hard-Block.
Exit 1 signalisiert „Floskeln gefunden" (der Autor entscheidet), nicht „Phase blockiert".

Exit-Codes:  0 = sauber (keine Treffer)   1 = Treffer (Flag/Warnung)   2 = Aufruffehler
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys


def _resolve_memory_dir(path: str) -> str:
    if os.path.basename(os.path.normpath(path)) == "_memory":
        return path
    return os.path.join(path, "_memory")


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_banlist(project: str) -> list[dict]:
    """Liest die Verbots-Phrasen aus der Story Bible. Gibt [{phrase, lang, source}] zurück."""
    mem = _resolve_memory_dir(project)
    sb = os.path.join(mem, "story-bible")
    ban: list[dict] = []
    svg_path = os.path.join(sb, "style-voice-guide.json")
    if os.path.isfile(svg_path):
        svg = _load_json(svg_path)
        for p in svg.get("ai_isms_de", []) or []:
            ban.append({"phrase": p, "lang": "de", "source": "style-voice-guide.ai_isms_de"})
        for p in svg.get("ai_isms_en", []) or []:
            ban.append({"phrase": p, "lang": "en", "source": "style-voice-guide.ai_isms_en"})
    for cp in sorted(glob.glob(os.path.join(sb, "CHAR-*.json"))):
        c = _load_json(cp)
        vs = c.get("voice_sheet", {}) or {}
        vl = vs.get("verbotsliste")
        # verbotsliste kann String ("a, b") oder Liste sein
        items = vl if isinstance(vl, list) else [x.strip() for x in str(vl).split(",")] if vl else []
        for p in items:
            if p:
                ban.append({"phrase": p, "lang": "*", "source": f"{c.get('id', cp)}.voice_sheet.verbotsliste"})
    return ban


def scan_text(text: str, banlist: list[dict]) -> list[dict]:
    """Gibt Treffer zurück: {line, phrase, lang, source}."""
    hits: list[dict] = []
    lines = text.splitlines()
    for b in banlist:
        phrase = b["phrase"].strip()
        if not phrase:
            continue
        pat = re.compile(re.escape(phrase), re.IGNORECASE)
        for lineno, line in enumerate(lines, 1):
            if pat.search(line):
                hits.append({"line": lineno, "phrase": phrase, "lang": b["lang"], "source": b["source"]})
    return hits


def _selftest() -> int:
    print("Selftest: AI-isms-Scan (DE/EN + verbotsliste)\n")
    ban = [
        {"phrase": "ein Tanz aus Licht und Schatten", "lang": "de", "source": "ai_isms_de"},
        {"phrase": "a testament to", "lang": "en", "source": "ai_isms_en"},
        {"phrase": "Schicksal", "lang": "*", "source": "CHAR-001.verbotsliste"},
    ]
    good = "Mira zählte die Schläge. Der Nebel roch nach Messing."
    bad = "Es war ein Tanz aus Licht und Schatten, a testament to ihr Schicksal."
    gh = scan_text(good, ban)
    bh = scan_text(bad, ban)
    ok = (len(gh) == 0 and len(bh) == 3)
    print(f"  good: {len(gh)} Treffer (erwartet 0)")
    print(f"  bad:  {len(bh)} Treffer (erwartet 3) — {[h['phrase'] for h in bh]}")
    print("OK" if ok else "FEHLGESCHLAGEN")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA AI-isms-/Floskel-Scanner (Phase 2)")
    ap.add_argument("project", nargs="?", help="Projektpfad (für Verbotsliste aus der Story Bible)")
    ap.add_argument("--file", action="append", default=[], help="Manuskript-Datei(en)/Globs")
    ap.add_argument("--phrase", action="append", default=[], help="zusätzliche Verbots-Phrase (Test)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.project and not args.phrase:
        ap.error("Projektpfad (für Banlist) oder mind. --phrase nötig (oder --selftest).")
    if not args.file:
        ap.error("--file <manuskript> fehlt.")

    try:
        banlist = load_banlist(args.project) if args.project else []
    except (OSError, json.JSONDecodeError) as e:
        print(f"FEHLER: Banlist nicht lesbar: {e}", file=sys.stderr)
        return 2
    banlist += [{"phrase": p, "lang": "*", "source": "--phrase"} for p in args.phrase]

    files: list[str] = []
    for pat in args.file:
        files.extend(glob.glob(pat, recursive=True))
    if not files:
        print("FEHLER: keine Manuskript-Dateien gefunden.", file=sys.stderr)
        return 2

    print(f"NOVA AI-isms-Scan — {len(banlist)} Verbots-Phrase(n), {len(files)} Datei(en)\n")
    total = 0
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                hits = scan_text(fh.read(), banlist)
        except OSError as e:
            print(f"  ✗ {path}: nicht lesbar ({e})")
            continue
        for h in hits:
            print(f"  ⚠ {path}:{h['line']} [{h['lang']}] „{h['phrase']}\"  ({h['source']})")
        total += len(hits)
    print(f"\n  Ergebnis: {total} Floskel-Treffer.")
    if total:
        print("  ⚠ Floskeln/AI-isms gefunden — Flag (kein Block; der Autor entscheidet über den Stil).")
        return 1
    print("  ✅ Keine Verbots-Phrasen gefunden.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
