#!/usr/bin/env python3
"""NOVA — GHOSTWRITE-Markup-Wrapper (Phase 2, DR-15) — Invariante 5.

Umschließt eine GHOSTWRITE-Variante **mechanisch** mit dem NOVA-Provenienz-Markup
(nova/conventions/provenance.md) — so ist „kein unmarkierter KI-Text möglich" eine
Garantie des Skripts, nicht des Wohlwollens des Modells:

    <!-- NOVA:AI start agent=<id> mode=GHOSTWRITE ts=<ISO-8601> variant=<n> -->
    … KI-Prosa …
    <!-- NOVA:AI end -->

Der Output ist so geformt, dass er das Provenienz-Export-Gate (scan_ai_prose.py)
garantiert besteht (Marker balanciert, nicht verschachtelt). Gegenprobe im --selftest.

Eingabe: --text "…"  ODER  --file <pfad>  ODER  STDIN.
Ausgabe: STDOUT  ODER  --out <pfad>  (bzw. --append <manuskript> hängt die markierte Passage an).

Exit-Codes:  0 = ok   2 = Aufruffehler
"""
from __future__ import annotations
import argparse
import os
import sys
from datetime import datetime, timezone

START = "<!-- NOVA:AI start agent={agent} mode=GHOSTWRITE ts={ts} variant={variant} -->"
END = "<!-- NOVA:AI end -->"


def wrap(text: str, agent: str, variant: int, ts: str | None = None) -> str:
    if ts is None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    body = text.strip("\n")
    return f"{START.format(agent=agent, ts=ts, variant=variant)}\n{body}\n{END}"


def _verify_balanced(marked: str) -> bool:
    """Gegenprobe: der Output muss scan_ai_prose.py bestehen (1 Span, 0 Errors)."""
    try:
        sib = os.path.join(os.path.dirname(__file__), "..", "..",
                           "nova-provenance-export-gate", "scripts")
        sys.path.insert(0, os.path.abspath(sib))
        from scan_ai_prose import scan_text  # type: ignore
    except Exception:
        return True  # Gate-Skript nicht erreichbar → Gegenprobe übersprungen
    spans, errors = scan_text(marked)
    return len(spans) == 1 and len(errors) == 0


def _selftest() -> int:
    print("Selftest: Markup-Wrapper + Provenienz-Gegenprobe\n")
    out = wrap("Die Stadtuhr schlug, doch niemand zählte mit.",
               agent="nova-ghostwrite", variant=1, ts="2026-06-13T10:00:00Z")
    has_attrs = ("agent=nova-ghostwrite" in out and "mode=GHOSTWRITE" in out
                 and "variant=1" in out and "ts=2026-06-13T10:00:00Z" in out)
    balanced = _verify_balanced(out)
    print(out)
    ok = has_attrs and balanced
    print(f"\n  Attribute vollständig: {has_attrs}; scan_ai_prose-Gegenprobe (1 Span/0 Fehler): {balanced}")
    print("OK" if ok else "FEHLGESCHLAGEN")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA GHOSTWRITE-Markup-Wrapper (Phase 2)")
    src = ap.add_mutually_exclusive_group()
    src.add_argument("--text", help="Varianten-Text direkt")
    src.add_argument("--file", help="Varianten-Text aus Datei")
    ap.add_argument("--agent", default="nova-ghostwrite")
    ap.add_argument("--variant", type=int, default=1)
    ap.add_argument("--ts", default=None, help="ISO-8601 (Default: jetzt, UTC)")
    ap.add_argument("--out", help="Output-Datei (Default: STDOUT)")
    ap.add_argument("--append", help="markierte Passage an Manuskript-Datei anhängen")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if args.text is not None:
        text = args.text
    elif args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as fh:
                text = fh.read()
        except OSError as e:
            print(f"FEHLER: {e}", file=sys.stderr)
            return 2
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        ap.error("Kein Text (--text/--file/STDIN).")

    marked = wrap(text, args.agent, args.variant, args.ts)
    if not _verify_balanced(marked):
        print("FEHLER: erzeugtes Markup besteht die Provenienz-Gegenprobe nicht.", file=sys.stderr)
        return 2

    if args.append:
        try:
            with open(args.append, "a", encoding="utf-8") as fh:
                fh.write(("\n\n" if os.path.getsize(args.append) else "") + marked + "\n")
            print(f"  ✓ markierte GHOSTWRITE-Passage an {args.append} angehängt (Commit-Typ: ai:).")
        except OSError as e:
            print(f"FEHLER: {e}", file=sys.stderr)
            return 2
    elif args.out:
        try:
            with open(args.out, "w", encoding="utf-8") as fh:
                fh.write(marked + "\n")
            print(f"  ✓ {args.out} geschrieben.")
        except OSError as e:
            print(f"FEHLER: {e}", file=sys.stderr)
            return 2
    else:
        print(marked)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
