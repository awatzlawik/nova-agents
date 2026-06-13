#!/usr/bin/env python3
"""NOVA — Wiederholungs-Scanner / Line-Editor (Phase 3, DR-17).

Mechanischer Satz-/Wortebenen-Repetitions-Detektor (stdlib-only). Ergänzt den AI-isms-Scan
(`scan_ai_isms.py` beim Style-Guardian — EINE Floskel-Quelle, Wiederverwendung im Skill) um die
**Wiederholungs-Ebene** des Line-Editors. Format-Vorbild: BMAD-CW `line-edit-quality-checklist.md`
+ Editor-Agent (`*prose-rhythm`/`*tighten-prose`); read-only/CRITIQUE (NovelWriter ReviewAndRetryAgent).

Detektiert (sprachneutral, mechanisch):
  - overused : Inhaltswörter über Häufigkeits-Schwelle (Stoppwörter DE/EN raus).
  - openers  : gleicher Satzanfang (erstes Wort) ≥ k-mal (monotone Satzeröffnung).
  - echo     : wiederholte 3-Gramme (Phrasen-Echo), nicht rein aus Stoppwörtern.
  - doubled  : direkt verdoppeltes Wort („der der").

**Invariante 2 (Geist):** Treffer sind Flags/Warnungen — KEIN Hard-Block (Stil = Autorhoheit,
exakt wie `scan_ai_isms.py`). Der Line-Editor meldet, schreibt nicht um.

Exit-Codes:  0 = sauber (keine Treffer)   1 = Treffer (Flag/Warnung)   2 = Aufruffehler
"""
from __future__ import annotations
import argparse
import glob
import re
import sys
from collections import Counter

# Stoppwörter DE/EN (bewusst kompakt; Inhaltswort-Heuristik, kein NLP).
_STOP = {
    "der", "die", "das", "den", "dem", "des", "ein", "eine", "einen", "einem", "einer", "eines",
    "und", "oder", "aber", "mit", "für", "von", "aus", "auf", "an", "in", "im", "zu", "zum", "zur",
    "ist", "war", "sind", "sein", "hat", "hatte", "wird", "werden", "sich", "nicht", "auch", "noch",
    "wie", "als", "so", "es", "er", "sie", "ihr", "ihm", "ihn", "ihre", "ihrem", "ihren", "dann",
    "da", "dass", "weil", "wenn", "schon", "nur", "über", "vor", "nach", "bei", "durch", "um",
    "the", "and", "or", "but", "with", "for", "from", "of", "to", "in", "on", "at", "a", "an",
    "is", "was", "are", "be", "has", "had", "will", "she", "he", "it", "her", "his", "they",
    "this", "that", "not", "as", "so", "then", "there", "their", "them",
}
_SENT_SPLIT = re.compile(r"(?<=[.!?…])\s+")
_WORD = re.compile(r"[0-9A-Za-zÄÖÜäöüß]+")
# Verdoppelung NUR bei reiner Whitespace-Nähe (echter Tippfehler „der der");
# Wiederholung über ein Satzzeichen (z. B. Anadiplose „…ließ, ließ…") ist Stil → kein Treffer.
_DOUBLED = re.compile(r"\b([0-9A-Za-zÄÖÜäöüß]{2,})\s+\1\b", re.IGNORECASE)


def _words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def _content(words: list[str]) -> list[str]:
    return [w for w in words if len(w) >= 4 and w not in _STOP]


def scan_text(text: str, *, min_count: int = 6, min_openers: int = 4,
              ngram: int = 3, min_echo: int = 2) -> list[dict]:
    """Gibt Treffer zurück: {kind, item, count, detail}. Reihenfolge: kind, dann Häufigkeit."""
    hits: list[dict] = []
    words = _words(text)

    # overused: häufige Inhaltswörter
    for w, c in Counter(_content(words)).most_common():
        if c >= min_count:
            hits.append({"kind": "overused", "item": w, "count": c,
                         "detail": f"Inhaltswort {c}× (Schwelle {min_count})"})

    # doubled: direkt (whitespace-) verdoppeltes Wort — auch Stoppwörter („der der" = klassischer Tippfehler)
    for m in _DOUBLED.finditer(text):
        w = m.group(1).lower()
        hits.append({"kind": "doubled", "item": w, "count": 2, "detail": f"„{w} {w}" + "\""})

    # openers: gleiches erstes Wort vieler Sätze
    openers = [s.strip().split()[0].lower() for s in _SENT_SPLIT.split(text)
               if s.strip() and s.strip().split()]
    for w, c in Counter(openers).most_common():
        if c >= min_openers:
            hits.append({"kind": "openers", "item": w, "count": c,
                         "detail": f"{c} Sätze beginnen mit „{w}" + "\""})

    # echo: wiederholte n-Gramme (nicht rein Stoppwort)
    grams = [" ".join(words[i:i + ngram]) for i in range(len(words) - ngram + 1)]
    for g, c in Counter(grams).most_common():
        if c >= min_echo and any(t not in _STOP and len(t) >= 3 for t in g.split()):
            hits.append({"kind": "echo", "item": g, "count": c,
                         "detail": f"{ngram}-Gramm {c}× wiederholt"})
    return hits


def _selftest() -> int:
    print("Selftest: Wiederholungs-Scanner (good/bad)\n")
    good = ("Der Nebel roch nach Messing. Mira zählte die Schläge, die nicht kamen. "
            "Über dem Platz hob niemand den Kopf. Zeit ist ein Versprechen aus Zahnrädern.")
    bad = ("Die Schatten tanzten. Die Schatten flüsterten. Die Schatten lachten. Die Schatten warteten. "
           "Es war war ein Tanz der Schatten, ein Tanz der Schatten, ein Tanz der Schatten überall.")
    gh = scan_text(good)
    bh = scan_text(bad)
    kinds = {h["kind"] for h in bh}
    ok = (len(gh) == 0 and {"overused", "openers", "echo", "doubled"} <= kinds)
    print(f"  good: {len(gh)} Treffer (erwartet 0)")
    print(f"  bad:  {len(bh)} Treffer; Arten={sorted(kinds)} (erwartet alle 4)")
    for h in bh:
        print(f"    ⚠ [{h['kind']}] „{h['item']}\" — {h['detail']}")
    print("OK" if ok else "FEHLGESCHLAGEN")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Wiederholungs-Scanner / Line-Editor (Phase 3)")
    ap.add_argument("--file", action="append", default=[], help="Manuskript-Datei(en)/Globs")
    ap.add_argument("--min-count", type=int, default=6, help="overused-Schwelle (Inhaltswort-Häufigkeit)")
    ap.add_argument("--min-openers", type=int, default=4, help="gleiche Satzanfänge")
    ap.add_argument("--ngram", type=int, default=3)
    ap.add_argument("--min-echo", type=int, default=2)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.file:
        ap.error("--file <manuskript> fehlt (oder --selftest verwenden).")

    files: list[str] = []
    for pat in args.file:
        files.extend(glob.glob(pat, recursive=True))
    if not files:
        print("FEHLER: keine Manuskript-Dateien gefunden.", file=sys.stderr)
        return 2

    print(f"NOVA Wiederholungs-Scan — {len(files)} Datei(en)\n")
    total = 0
    for path in sorted(files):
        try:
            with open(path, "r", encoding="utf-8") as fh:
                hits = scan_text(fh.read(), min_count=args.min_count, min_openers=args.min_openers,
                                 ngram=args.ngram, min_echo=args.min_echo)
        except OSError as e:
            print(f"  ✗ {path}: nicht lesbar ({e})")
            continue
        if hits:
            print(f"  {path}:")
            for h in sorted(hits, key=lambda x: (x["kind"], -x["count"])):
                print(f"    ⚠ [{h['kind']}] „{h['item']}\"  ({h['detail']})")
        total += len(hits)
    print(f"\n  Ergebnis: {total} Wiederholungs-Treffer.")
    if total:
        print("  ⚠ Wiederholungen gefunden — Flag (kein Block; der Autor entscheidet über den Stil, I2).")
        return 1
    print("  ✅ Keine auffälligen Wiederholungen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
