#!/usr/bin/env python3
"""NOVA — Drei-Akt-Meilenstein-Prüfung (Invariante 2).

Vergleicht die IST-Position jedes Beats (in % der Manuskriptlänge) gegen die
Weiland-SOLL-Marken. Abweichung > Toleranz ⇒ WARNUNG (kein Block — der Autor
entscheidet bewusst, tasks.md §1.2 / Overview Rec.3).

Eingabe: ein Beat-Sheet als JSON oder YAML (siehe nova/templates/beat-sheet-tmpl.yaml).
Erwartetes Schema (pro Beat):  { "id": str, "ist_prozent": number, "soll_prozent": number? }
Beats ohne `soll_prozent` werden über ihre `id` den Weiland-Marken zugeordnet.

Exit-Codes:  0 = ok ODER nur Warnungen (Abweichung ist kein Block)
             2 = strukturell ungültige Eingabe (Datei/Schema kaputt)
"""
from __future__ import annotations
import argparse
import json
import sys

# Weiland-Meilensteinmarken (Synchron mit nova/config.yaml → structure.milestones_percent)
WEILAND_MARKS = {
    "inciting_incident": 12,
    "first_plot_point": 25,
    "first_pinch_point": 37,
    "midpoint": 50,
    "second_pinch_point": 62,
    "third_plot_point": 75,
    "climax": 88,
}
DEFAULT_TOLERANCE = 5  # ±%


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if path.endswith((".yaml", ".yml")):
        try:
            import yaml  # optional
        except ImportError:
            raise SystemExit("FEHLER: PyYAML nicht installiert — bitte JSON-Beat-Sheet übergeben "
                             "oder `pip install pyyaml`.")
        return yaml.safe_load(text)
    return json.loads(text)


def check_beats(beats: list[dict], tolerance: float = DEFAULT_TOLERANCE) -> list[dict]:
    """Gibt eine Liste von Befunden zurück. severity ∈ {ok, warning, error}."""
    findings: list[dict] = []
    for b in beats:
        bid = b.get("id", "<ohne id>")
        ist = b.get("ist_prozent")
        soll = b.get("soll_prozent")
        if soll is None:
            soll = WEILAND_MARKS.get(bid)
        if ist is None:
            findings.append({"severity": "error", "beat": bid,
                             "message": "kein ist_prozent gesetzt"})
            continue
        if soll is None:
            findings.append({"severity": "ok", "beat": bid,
                             "message": f"frei platzierter Beat @ {ist}% (keine Soll-Marke)"})
            continue
        delta = abs(float(ist) - float(soll))
        if delta > tolerance:
            findings.append({"severity": "warning", "beat": bid,
                             "message": f"@ {ist}% (Soll {soll}%, Abweichung {delta:.1f}% > ±{tolerance}%) "
                                        f"⇒ WARNUNG, kein Block"})
        else:
            findings.append({"severity": "ok", "beat": bid,
                             "message": f"@ {ist}% (Soll {soll}%, Δ {delta:.1f}% ≤ ±{tolerance}%)"})
    return findings


def _report(findings: list[dict]) -> int:
    order = {"error": 0, "warning": 1, "ok": 2}
    icon = {"error": "✗", "warning": "⚠", "ok": "✓"}
    for f in sorted(findings, key=lambda x: order[x["severity"]]):
        print(f"  {icon[f['severity']]} {f['beat']}: {f['message']}")
    n_err = sum(1 for f in findings if f["severity"] == "error")
    n_warn = sum(1 for f in findings if f["severity"] == "warning")
    print(f"\n  Ergebnis: {n_err} Fehler, {n_warn} Warnungen, "
          f"{sum(1 for f in findings if f['severity']=='ok')} ok.")
    return 2 if n_err else 0


def _selftest() -> int:
    print("Selftest: Weiland-Marken + Toleranzlogik")
    sample = [
        {"id": "first_plot_point", "ist_prozent": 26},   # Δ1 → ok
        {"id": "midpoint", "ist_prozent": 58},            # Δ8 → warning
        {"id": "climax", "ist_prozent": 88},              # Δ0 → ok
        {"id": "freier_beat", "ist_prozent": 40},         # keine Marke → ok
        {"id": "first_pinch_point"},                      # kein ist → error
    ]
    findings = check_beats(sample)
    by = {f["beat"]: f["severity"] for f in findings}
    expected = {"first_plot_point": "ok", "midpoint": "warning",
                "climax": "ok", "freier_beat": "ok", "first_pinch_point": "error"}
    ok = by == expected
    _report(findings)
    print(("OK" if ok else "FEHLGESCHLAGEN") + f": erwartet {expected}, erhalten {by}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Drei-Akt-Meilenstein-Prüfung")
    ap.add_argument("beat_sheet", nargs="?", help="Pfad zum Beat-Sheet (JSON/YAML)")
    ap.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    ap.add_argument("--selftest", action="store_true", help="interne Logik testen (keine Datei nötig)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.beat_sheet:
        ap.error("Beat-Sheet-Pfad fehlt (oder --selftest verwenden).")

    try:
        data = _load(args.beat_sheet)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FEHLER: Beat-Sheet nicht lesbar/parsebar: {e}", file=sys.stderr)
        return 2
    beats = data.get("beats") if isinstance(data, dict) else data
    if not isinstance(beats, list):
        print("FEHLER: Beat-Sheet enthält keine 'beats'-Liste.", file=sys.stderr)
        return 2
    print(f"NOVA Drei-Akt-Prüfung — {len(beats)} Beats, Toleranz ±{args.tolerance}%\n")
    return _report(check_beats(beats, args.tolerance))


if __name__ == "__main__":
    raise SystemExit(main())
