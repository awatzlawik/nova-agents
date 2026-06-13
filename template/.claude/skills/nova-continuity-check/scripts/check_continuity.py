#!/usr/bin/env python3
"""NOVA — Continuity-Nachprüfung (Phase 2, DR-14) — GHOSTWRITE-`post_check` + Benchmark (Rec. 2).

Validiert eine Manuskript-Szene/Passage **mechanisch** gegen die Continuity-Register (Phase 1)
und die Drei-Akt-Position — der automatische Konsistenz-Check nach GHOSTWRITE (Overview §7 Schritt 7).
Volle LLM-Widerspruchserkennung (Zeit/Ort/Fakten-Subtext) bleibt Phase 3 (Continuity-Checker-Subagent).

Geprüft:
  1. ID-Existenz:  pov / bible_refs / im Text genannte CHAR-/WORLD-IDs existieren im Register (sonst dangling → fail).
  2. Status/POV:   POV-Figur ist nicht tot (status ∉ {dead,tot,gestorben}) — kein „toter spricht"-Widerspruch.
  3. Drei-Akt:     scene.beat_id → Weiland-Marke (Import aus nova-beat-percentage-check); Abweichung = WARNUNG (I2), nie Block.

Benchmark (Rec. 2): --benchmark misst die **False-Positive-Rate** gegen ein gelabeltes Fixture und
vergleicht mit der Schwelle (config.ghostwrite.benchmark_continuity_false_positive_threshold = 0.05).
Solange FP ≥ 5 % bleibt GHOSTWRITE-Output manuell nachzukontrollieren (ghostwrite.enabled:false).

Exit-Codes:  0 = ok / nur Warnung   1 = Widerspruch (ID-/Status-Verstoß)   2 = Aufruffehler
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys

# Drei-Akt-Marken aus dem Schwester-Gate (eine Quelle der Wahrheit; Fallback inline).
WEILAND_MARKS = {
    "inciting_incident": 12, "first_plot_point": 25, "first_pinch_point": 37,
    "midpoint": 50, "second_pinch_point": 62, "third_plot_point": 75, "climax": 88,
}
DEFAULT_TOLERANCE = 5
# Spiegelt config.ghostwrite.benchmark_continuity_false_positive_threshold (config.yaml).
DEFAULT_FP_THRESHOLD = 0.05
DEAD = {"dead", "tot", "gestorben", "verstorben", "deceased"}
ID_RE = re.compile(r"\b(?:CHAR|WORLD|SCENE|BEAT|TIME)-\d+\b")

try:  # gleiche Marken/Toleranz wie check_marks.py
    _sib = os.path.join(os.path.dirname(__file__), "..", "..", "nova-beat-percentage-check", "scripts")
    sys.path.insert(0, os.path.abspath(_sib))
    from check_marks import WEILAND_MARKS as _WM, DEFAULT_TOLERANCE as _TOL  # type: ignore
    WEILAND_MARKS, DEFAULT_TOLERANCE = _WM, _TOL
except Exception:
    pass


def _resolve_memory_dir(path: str) -> str:
    if os.path.basename(os.path.normpath(path)) == "_memory":
        return path
    return os.path.join(path, "_memory")


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _opt(path: str):
    return _load_json(path) if os.path.isfile(path) else None


def load_bible(mem_dir: str) -> dict:
    cont = os.path.join(mem_dir, "continuity")
    sb = os.path.join(mem_dir, "story-bible")
    chars = {c["id"]: c for c in (_opt(os.path.join(cont, "characters.json")) or []) if c.get("id")}
    world = {w["id"]: w for w in (_opt(os.path.join(cont, "world.json")) or []) if w.get("id")}
    bs = _opt(os.path.join(sb, "beat-sheet.json")) or {}
    beats = {b["id"]: b for b in (bs.get("beats", []) if isinstance(bs, dict) else bs) if b.get("id")}
    sl = _opt(os.path.join(sb, "scene-list.json"))
    scenes = {s["id"]: s for s in ((sl.get("scenes", sl) if isinstance(sl, dict) else sl) if sl else []) if s.get("id")}
    return {"characters": chars, "world": world, "beats": beats, "scenes": scenes}


def check_passage(bible: dict, scene: dict | None, text: str = "", tolerance: float = DEFAULT_TOLERANCE) -> list[dict]:
    """Gibt Befunde zurück; severity ∈ {ok, warning, fail}."""
    f: list[dict] = []
    chars, world, beats = bible["characters"], bible["world"], bible["beats"]

    # Referenzierte IDs sammeln: aus Szenenkarte + aus dem Text
    ref_ids: set[str] = set()
    pov = None
    if scene:
        pov = scene.get("pov")
        ref_ids.update([pov] if pov else [])
        ref_ids.update(scene.get("bible_refs") or [])
    ref_ids.update(ID_RE.findall(text))
    ref_ids.discard(None)

    # 1. ID-Existenz
    for rid in sorted(ref_ids):
        if rid.startswith("CHAR-") and rid not in chars:
            f.append({"sev": "fail", "area": "ids", "msg": f"CHAR-Ref '{rid}' existiert nicht im Register (dangling)"})
        elif rid.startswith("WORLD-") and rid not in world:
            f.append({"sev": "fail", "area": "ids", "msg": f"WORLD-Ref '{rid}' existiert nicht im Register (dangling)"})
    if ref_ids and not any(x["area"] == "ids" and x["sev"] == "fail" for x in f):
        f.append({"sev": "ok", "area": "ids", "msg": f"{len(ref_ids)} referenzierte ID(s) existieren"})

    # 2. Status/POV-Plausibilität
    if pov and pov in chars:
        status = str(chars[pov].get("status", "")).strip().lower()
        if status in DEAD:
            f.append({"sev": "fail", "area": "status",
                      "msg": f"POV '{pov}' ist '{status}' — toter/abwesender POV spricht (Widerspruch)"})
        else:
            f.append({"sev": "ok", "area": "status", "msg": f"POV '{pov}' lebend/aktiv (status={status or '—'})"})

    # 3. Drei-Akt-Position (Warnung, nie Block)
    if scene and scene.get("beat_id"):
        bid = scene["beat_id"]
        soll = WEILAND_MARKS.get(bid)
        b = beats.get(bid)
        ist = b.get("ist_prozent") if b else None
        if soll is not None and ist is not None:
            delta = abs(float(ist) - float(b.get("soll_prozent", soll)))
            sev = "warning" if delta > tolerance else "ok"
            f.append({"sev": sev, "area": "position",
                      "msg": f"beat '{bid}' @ {ist}% (Soll {b.get('soll_prozent', soll)}%, Δ {delta:.0f}%)"
                             + (" ⇒ WARNUNG, kein Block" if sev == "warning" else "")})
        elif b is None and bid:
            f.append({"sev": "fail", "area": "position", "msg": f"beat_id '{bid}' nicht im Beat-Sheet (dangling)"})
    return f


def _rc(findings: list[dict]) -> int:
    return 1 if any(x["sev"] == "fail" for x in findings) else 0


def _report(findings: list[dict]) -> int:
    icon = {"fail": "✗", "warning": "⚠", "ok": "✓"}
    order = {"fail": 0, "warning": 1, "ok": 2}
    for x in sorted(findings, key=lambda y: order[y["sev"]]):
        print(f"  {icon[x['sev']]} [{x['area']}] {x['msg']}")
    n_fail = sum(1 for x in findings if x["sev"] == "fail")
    n_warn = sum(1 for x in findings if x["sev"] == "warning")
    print(f"\n  Ergebnis: {n_fail} Widerspruch/Widersprüche, {n_warn} Warnung(en).")
    if n_fail:
        print("  ⛔ Continuity-Widerspruch — GHOSTWRITE-Passage zurück an den Autor.")
        return 1
    print("  ✅ Continuity ok (Warnungen sind kein Block — Autor entscheidet).")
    return 0


# ── Benchmark-Fixture (gelabelt) — demonstriert die FP-Messung (Rec. 2) ──────────────
def _benchmark_fixture() -> tuple[dict, list[dict]]:
    bible = {
        "characters": {"CHAR-001": {"id": "CHAR-001", "status": "alive"},
                       "CHAR-002": {"id": "CHAR-002", "status": "alive"},
                       "CHAR-009": {"id": "CHAR-009", "status": "tot"}},
        "world": {"WORLD-001": {"id": "WORLD-001"}, "WORLD-002": {"id": "WORLD-002"}},
        "beats": {"midpoint": {"id": "midpoint", "soll_prozent": 50, "ist_prozent": 50},
                  "climax": {"id": "climax", "soll_prozent": 88, "ist_prozent": 89}},
        "scenes": {},
    }
    cases = [  # label: True = konsistent (Check SOLL pass), False = inkonsistent (Check SOLL fail)
        {"label": True,  "scene": {"pov": "CHAR-001", "bible_refs": ["WORLD-001"], "beat_id": "midpoint"}, "text": "Mira zählt."},
        {"label": True,  "scene": {"pov": "CHAR-002", "bible_refs": ["WORLD-002"], "beat_id": "climax"}, "text": "Brandt fordert."},
        {"label": True,  "scene": {"pov": "CHAR-001", "bible_refs": ["CHAR-002"], "beat_id": "midpoint"}, "text": "Sie reden."},
        {"label": False, "scene": {"pov": "CHAR-009", "bible_refs": [], "beat_id": "midpoint"}, "text": "Ein Toter spricht."},
        {"label": False, "scene": {"pov": "CHAR-001", "bible_refs": ["WORLD-404"], "beat_id": "midpoint"}, "text": "Dangling WORLD-404."},
        {"label": False, "scene": {"pov": "CHAR-001", "bible_refs": [], "beat_id": "midpoint"}, "text": "Ref CHAR-777 fehlt."},
    ]
    return bible, cases


def _benchmark(threshold: float = DEFAULT_FP_THRESHOLD) -> int:
    print("Benchmark: Continuity-Gate False-Positive-Rate (Rec. 2)\n")
    bible, cases = _benchmark_fixture()
    fp = fn = n_consistent = n_inconsistent = 0
    for c in cases:
        rc = _rc(check_passage(bible, c["scene"], c["text"]))
        flagged = (rc == 1)
        if c["label"]:
            n_consistent += 1
            if flagged:
                fp += 1  # konsistent, aber geflaggt = False Positive
        else:
            n_inconsistent += 1
            if not flagged:
                fn += 1  # inkonsistent, aber durchgewunken = False Negative
        print(f"  {'FLAG' if flagged else 'pass'}  label={'konsistent' if c['label'] else 'inkonsistent'}  "
              f"pov={c['scene']['pov']}")
    fp_rate = fp / n_consistent if n_consistent else 0.0
    print(f"\n  Konsistente Fälle: {n_consistent} · False Positives: {fp} → FP-Rate {fp_rate:.0%}")
    print(f"  Inkonsistente Fälle: {n_inconsistent} · False Negatives: {fn}")
    print(f"  Schwelle (config.ghostwrite…threshold): {threshold:.0%}")
    if fp_rate < threshold:
        print("  ✅ FP-Rate < Schwelle auf diesem Demo-Fixture.")
        print("  ⚠ Hinweis: Demonstrations-Fixture, kein repräsentatives Korpus. GHOSTWRITE-Auto-Übernahme")
        print("     bleibt gesperrt (ghostwrite.enabled:false), bis der Phase-3-Continuity-Checker + ein")
        print("     echtes Korpus die < 5 % bestätigen. Bis dahin: Markup + manuelle Nachkontrolle.")
        return 0
    print("  ⛔ FP-Rate ≥ Schwelle — Auto-Übernahme gesperrt.")
    return 1


def _selftest() -> int:
    print("Selftest: Continuity-Nachprüfung (good/bad)\n")
    bible, _ = _benchmark_fixture()
    good = check_passage(bible, {"pov": "CHAR-001", "bible_refs": ["WORLD-001"], "beat_id": "midpoint"}, "ok")
    bad = check_passage(bible, {"pov": "CHAR-009", "bible_refs": ["WORLD-404"], "beat_id": "midpoint"}, "CHAR-777 taucht auf")
    rc_good, rc_bad = _rc(good), _rc(bad)
    print("[GOOD]"); _report(good)
    print("\n[BAD]"); _report(bad)
    ok = (rc_good == 0 and rc_bad == 1)
    print(f"\n{'OK' if ok else 'FEHLGESCHLAGEN'}: good→{rc_good} (erwartet 0), bad→{rc_bad} (erwartet 1)")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Continuity-Nachprüfung (Phase 2)")
    ap.add_argument("project", nargs="?", help="Projektpfad (projects/<p>)")
    ap.add_argument("--scene", help="SCENE-ID der zu prüfenden Passage")
    ap.add_argument("--file", action="append", default=[], help="Manuskript-Datei(en)/Globs der Passage")
    ap.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--benchmark", action="store_true", help="FP-Rate gegen gelabeltes Fixture (Rec. 2)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if args.benchmark:
        return _benchmark()
    if not args.project:
        ap.error("Projektpfad fehlt (oder --selftest / --benchmark).")

    try:
        bible = load_bible(_resolve_memory_dir(args.project))
        scene = bible["scenes"].get(args.scene) if args.scene else None
        if args.scene and scene is None:
            print(f"FEHLER: SCENE-ID '{args.scene}' nicht in scene-list.json.", file=sys.stderr)
            return 2
        text = ""
        for pat in args.file:
            for fp in glob.glob(pat, recursive=True):
                with open(fp, "r", encoding="utf-8") as fh:
                    text += fh.read() + "\n"
    except (OSError, json.JSONDecodeError) as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2

    print(f"NOVA Continuity-Nachprüfung — {args.project}"
          + (f" · {args.scene}" if args.scene else "") + "\n")
    return _report(check_passage(bible, scene, text, args.tolerance))


if __name__ == "__main__":
    raise SystemExit(main())
