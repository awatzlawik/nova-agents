#!/usr/bin/env python3
"""NOVA — Struktur-Gate / Developmental-Editor (Phase 3, DR-16).

Mechanische Drei-Akt-/Pacing-Analyse eines Beat-Sheets gegen die Weiland-Marken.
**Wiederverwendung (eine Quelle der Wahrheit):** importiert WEILAND_MARKS/DEFAULT_TOLERANCE/check_beats
aus `nova-beat-percentage-check` — KEIN zweites Struktur-Modell (Kohärenz-Gate-Item Phase-3-E).

Liefert Pacing-/Struktur-Abweichungen MIT %-Bezug (Developmental-Editor-DoD) und detektiert den
„sagging middle" (Overview §3/§8, Rec. 3).

Geprüft:
  1. Meilenstein-Position:  je Beat ist% vs soll% (reuse check_beats) — Abweichung > Toleranz = WARNUNG (I2).
  2. Akt-Proportionen:      Akt 1 (→first_plot_point), Akt 2 (fpp→third_plot_point), Akt 3 (tpp→100 %)
                            gegen 25/50/25 % (config.structure.act_proportions) — Abweichung = WARNUNG.
  3. Sagging Middle:        Midpoint platziert ~50 %? beide Pinch Points (37/62) vorhanden?
                            größte Lücke zwischen platzierten Akt-2-Beats (Sag-Indikator)?

**Invariante 2:** ALLES ist WARNUNG, nie Block — der Autor entscheidet bewusst (Overview Rec. 3).
Der Developmental-Editor ist read-only/CRITIQUE (NovelWriter ReviewAndRetryAgent-Vorbild):
meldet, schreibt nicht um.

Eingabe: ein Projektpfad (projects/<p>) ODER direkt ein Beat-Sheet (JSON/YAML).
Exit-Codes:  0 = ok ODER nur Warnungen (Struktur-Abweichung ist NIE ein Block)
             2 = strukturell ungültige Eingabe (Datei/Schema kaputt)
"""
from __future__ import annotations
import argparse
import json
import os
import sys

# Weiland-Marken/Toleranz + Per-Beat-Prüfung aus dem Schwester-Gate (eine Quelle; Fallback inline).
WEILAND_MARKS = {
    "inciting_incident": 12, "first_plot_point": 25, "first_pinch_point": 37,
    "midpoint": 50, "second_pinch_point": 62, "third_plot_point": 75, "climax": 88,
}
DEFAULT_TOLERANCE = 5
_check_beats = None
try:
    _sib = os.path.join(os.path.dirname(__file__), "..", "..", "nova-beat-percentage-check", "scripts")
    sys.path.insert(0, os.path.abspath(_sib))
    from check_marks import WEILAND_MARKS as _WM, DEFAULT_TOLERANCE as _TOL, check_beats as _cb  # type: ignore
    WEILAND_MARKS, DEFAULT_TOLERANCE, _check_beats = _WM, _TOL, _cb
except Exception:
    pass

# Akt-Spannen (Soll, in % der Manuskriptlänge) — synchron mit config.structure (Akt-Enden 25/75/100).
ACT_SPAN_TARGETS = {1: 25, 2: 50, 3: 25}
# Akt-2-Stützpfeiler gegen den „sagging middle" (Overview §3): Midpoint + beide Pinch Points.
ACT2_SUPPORTS = ["first_pinch_point", "midpoint", "second_pinch_point"]
SAG_GAP = 20  # % ohne platzierten Struktur-Beat innerhalb Akt 2 ⇒ Sag-Indikator (Warnung)


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        text = fh.read()
    if path.endswith((".yaml", ".yml")):
        try:
            import yaml  # optional
        except ImportError:
            raise SystemExit("FEHLER: PyYAML nicht installiert — bitte JSON-Beat-Sheet übergeben.")
        return yaml.safe_load(text)
    return json.loads(text)


def _resolve_beat_sheet(path: str) -> str:
    """Projektpfad → _memory/story-bible/beat-sheet.json; sonst Pfad unverändert."""
    cand = os.path.join(path, "_memory", "story-bible", "beat-sheet.json")
    if os.path.isdir(path) and os.path.isfile(cand):
        return cand
    return path


def _ist(beats: list[dict], bid: str):
    b = next((x for x in beats if x.get("id") == bid), None)
    if b is None:
        return None
    v = b.get("ist_prozent")
    return float(v) if v is not None else None


def check_structure(beats: list[dict], tolerance: float = DEFAULT_TOLERANCE) -> list[dict]:
    """Gibt Befunde zurück; severity ∈ {ok, warning, error}. KEIN fail/Block (I2)."""
    f: list[dict] = []

    # ── 1. Meilenstein-Position (reuse check_beats) ──────────────────────────
    if _check_beats is not None:
        for x in _check_beats(beats, tolerance):
            f.append({"sev": x["severity"], "area": "position", "msg": f"{x['beat']}: {x['message']}"})
    else:  # Fallback ohne Import
        for b in beats:
            bid = b.get("id", "<ohne id>")
            ist, soll = b.get("ist_prozent"), b.get("soll_prozent", WEILAND_MARKS.get(b.get("id")))
            if ist is None or soll is None:
                continue
            delta = abs(float(ist) - float(soll))
            sev = "warning" if delta > tolerance else "ok"
            f.append({"sev": sev, "area": "position",
                      "msg": f"{bid}: @ {ist}% (Soll {soll}%, Δ {delta:.0f}%)"})

    # ── 2. Akt-Proportionen (mit %-Bezug) ────────────────────────────────────
    fpp, mid, tpp = _ist(beats, "first_plot_point"), _ist(beats, "midpoint"), _ist(beats, "third_plot_point")
    if fpp is not None and tpp is not None:
        spans = {1: fpp - 0, 2: tpp - fpp, 3: 100 - tpp}
        for akt, ist_span in spans.items():
            soll_span = ACT_SPAN_TARGETS[akt]
            delta = abs(ist_span - soll_span)
            sev = "warning" if delta > tolerance else "ok"
            f.append({"sev": sev, "area": "act-proportion",
                      "msg": f"Akt {akt}: {ist_span:.0f}% der Länge (Soll {soll_span}%, Δ {delta:.0f}%)"
                             + (" ⇒ WARNUNG, kein Block" if sev == "warning" else "")})
    else:
        f.append({"sev": "warning", "area": "act-proportion",
                  "msg": "first_plot_point/third_plot_point nicht platziert — Akt-Proportionen nicht messbar"})

    # ── 3. Sagging Middle (Overview §3: Midpoint + Pinch Points stützen Akt 2) ─
    if mid is None:
        f.append({"sev": "warning", "area": "sagging-middle",
                  "msg": "Midpoint fehlt — Hauptanker gegen die durchhängende Mitte nicht gesetzt"})
    elif abs(mid - 50) > tolerance:
        f.append({"sev": "warning", "area": "sagging-middle",
                  "msg": f"Midpoint @ {mid:.0f}% (Soll 50%, Δ {abs(mid-50):.0f}%) — Akt-2-Wendepunkt verschoben"})
    else:
        f.append({"sev": "ok", "area": "sagging-middle", "msg": f"Midpoint @ {mid:.0f}% stützt die Mitte"})

    for sup in ("first_pinch_point", "second_pinch_point"):
        if _ist(beats, sup) is None:
            f.append({"sev": "warning", "area": "sagging-middle",
                      "msg": f"{sup} fehlt — Akt 2 verliert einen Stützpfeiler (Sag-Risiko)"})

    # Lücken-Analyse: größte Strecke ohne platzierten Struktur-Beat in Akt 2 (25–75 %)
    placed = sorted({0.0, 100.0} | {p for p in (fpp, mid, tpp,
                    _ist(beats, "first_pinch_point"), _ist(beats, "second_pinch_point")) if p is not None})
    in_act2 = [p for p in placed if 20 <= p <= 80]
    max_gap, gap_at = 0.0, None
    for a, b in zip(in_act2, in_act2[1:]):
        if b - a > max_gap:
            max_gap, gap_at = b - a, (a, b)
    if gap_at and max_gap > SAG_GAP:
        f.append({"sev": "warning", "area": "sagging-middle",
                  "msg": f"größte beat-freie Strecke in Akt 2: {max_gap:.0f}% ({gap_at[0]:.0f}–{gap_at[1]:.0f}%) "
                         f"> {SAG_GAP}% ⇒ möglicher Durchhänger"})
    elif gap_at:
        f.append({"sev": "ok", "area": "sagging-middle",
                  "msg": f"Akt-2-Beats engmaschig (max. Lücke {max_gap:.0f}% ≤ {SAG_GAP}%)"})
    return f


def _report(findings: list[dict]) -> int:
    order = {"error": 0, "warning": 1, "ok": 2}
    icon = {"error": "✗", "warning": "⚠", "ok": "✓"}
    for x in sorted(findings, key=lambda y: order[y["sev"]]):
        print(f"  {icon[x['sev']]} [{x['area']}] {x['msg']}")
    n_err = sum(1 for x in findings if x["sev"] == "error")
    n_warn = sum(1 for x in findings if x["sev"] == "warning")
    n_ok = sum(1 for x in findings if x["sev"] == "ok")
    print(f"\n  Ergebnis: {n_err} Fehler, {n_warn} Warnung(en), {n_ok} ok.")
    if n_err:
        print("  ✗ Beat-Sheet strukturell unlesbar.")
        return 2
    if n_warn:
        print("  ⚠ Struktur-/Pacing-Hinweise (mit %-Bezug) — WARNUNGEN, kein Block (Autor entscheidet, I2).")
    else:
        print("  ✅ Struktur sitzt auf den Weiland-Marken; keine Pacing-Auffälligkeit.")
    return 0


def _selftest() -> int:
    print("Selftest: Struktur-Gate (gute Struktur vs. durchhängende Mitte)\n")
    good = [{"id": k, "ist_prozent": v} for k, v in WEILAND_MARKS.items()] + \
           [{"id": "resolution", "ist_prozent": 97}]
    # bad: Midpoint fehlt + second_pinch_point fehlt ⇒ Sag-Warnungen + große Akt-2-Lücke
    bad = [{"id": "inciting_incident", "ist_prozent": 12},
           {"id": "first_plot_point", "ist_prozent": 25},
           {"id": "first_pinch_point", "ist_prozent": 30},
           {"id": "third_plot_point", "ist_prozent": 75},
           {"id": "climax", "ist_prozent": 88}]
    print("[GOOD]"); rc_good = _report(check_structure(good))
    fg = check_structure(good)
    print("\n[BAD]"); rc_bad = _report(check_structure(bad))
    fb = check_structure(bad)
    good_clean = not any(x["sev"] == "warning" for x in fg)
    bad_sag = any(x["area"] == "sagging-middle" and x["sev"] == "warning" for x in fb)
    ok = (rc_good == 0 and rc_bad == 0 and good_clean and bad_sag)
    print(f"\n{'OK' if ok else 'FEHLGESCHLAGEN'}: good ohne Warnung={good_clean}, "
          f"bad meldet Sagging-Middle={bad_sag} (beide exit 0 — Abweichung blockt nie, I2)")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Struktur-Gate / Developmental-Editor (Phase 3)")
    ap.add_argument("target", nargs="?", help="Projektpfad (projects/<p>) ODER Beat-Sheet (JSON/YAML)")
    ap.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    ap.add_argument("--selftest", action="store_true", help="interne Logik testen (keine Datei nötig)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.target:
        ap.error("Projekt-/Beat-Sheet-Pfad fehlt (oder --selftest verwenden).")
    try:
        data = _load(_resolve_beat_sheet(args.target))
    except (OSError, json.JSONDecodeError) as e:
        print(f"FEHLER: Beat-Sheet nicht lesbar/parsebar: {e}", file=sys.stderr)
        return 2
    beats = data.get("beats") if isinstance(data, dict) else data
    if not isinstance(beats, list):
        print("FEHLER: Beat-Sheet enthält keine 'beats'-Liste.", file=sys.stderr)
        return 2
    print(f"NOVA Struktur-Gate — {args.target} ({len(beats)} Beats, Toleranz ±{args.tolerance}%)\n")
    return _report(check_structure(beats, args.tolerance))


if __name__ == "__main__":
    raise SystemExit(main())
