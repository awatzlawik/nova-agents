#!/usr/bin/env python3
"""NOVA — Planungs-Gate (Phase 1, CHECK).

Mechanische Prüfung der Story-Bible-Shards eines Projekts gegen die **realen** Template-Felder
(nova/templates/*-tmpl.yaml). Erfüllt das Kohärenz-Gate-Item „Planungs-Gate referenziert reale Felder".

Geprüft (tasks.md Phase-1-G + DR-7):
  1. Prämisse vollständig?  premise.json: logline, premise_paragraph, central_question, stakes
  2. Beats platziert?       beat-sheet.json: Meilenstein-Beats haben ist_prozent
                            (Abweichung > Toleranz ⇒ WARNUNG, kein Gate-Block — Invariante 2)
  3. Arcs an Akte gemappt?  CHAR-*.json: arc_mapping.{akt1_zustand, akt2_wende, akt3_zustand}
  4. Szenen↔Beats integer?  scene-list.json: jede scene.beat_id ∈ beat-sheet.beats[].id
  5. Bible-Refs/IDs stabil? scene.pov/bible_refs referenzieren existierende CHAR-/WORLD-IDs

Eingabe: ein Projektpfad (projects/<p>) ODER direkt ein story-bible-Ordner.
Severity:  ok | warning | fail | error
Exit-Codes: 0 = Gate erfüllt (nur Warnungen erlaubt)
            1 = Gate NICHT erfüllt (Pflichtartefakt unvollständig/inkohärent — Phasenübergang hält)
            2 = strukturell ungültige Eingabe (Datei/JSON kaputt)

Drei-Akt-Abweichung führt NIE allein zu Exit 1 (Autor-Souveränität, Invariante 2).
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import sys

# Weiland-Meilensteinmarken — synchron mit nova/config.yaml und nova-beat-percentage-check.
# Bevorzugt aus dem Schwester-Gate importiert (eine Quelle der Wahrheit); Fallback inline.
WEILAND_MARKS = {
    "inciting_incident": 12, "first_plot_point": 25, "first_pinch_point": 37,
    "midpoint": 50, "second_pinch_point": 62, "third_plot_point": 75, "climax": 88,
}
DEFAULT_TOLERANCE = 5

try:  # Reuse: dieselbe Toleranz-/Marken-Logik wie das Drei-Akt-Gate (DR-7 „Delegation")
    _sib = os.path.join(os.path.dirname(__file__), "..", "..",
                        "nova-beat-percentage-check", "scripts")
    sys.path.insert(0, os.path.abspath(_sib))
    from check_marks import WEILAND_MARKS as _WM, DEFAULT_TOLERANCE as _TOL  # type: ignore
    WEILAND_MARKS, DEFAULT_TOLERANCE = _WM, _TOL
except Exception:
    pass  # Fallback auf die inline-Kopie oben (bleibt synchron zu config.yaml)

REQUIRED_PREMISE = ["logline", "premise_paragraph", "central_question", "stakes"]
ARC_FIELDS = ["akt1_zustand", "akt2_wende", "akt3_zustand"]


def _truthy(v) -> bool:
    if v is None:
        return False
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (list, dict)):
        return len(v) > 0
    return True


def check_planning(bible: dict, tolerance: float = DEFAULT_TOLERANCE) -> list[dict]:
    """bible = { premise:{}, world:[], characters:[], beats:[], scenes:[], timeline:[] }.
    Gibt Befunde zurück; severity ∈ {ok, warning, fail, error}."""
    f: list[dict] = []

    # ── 1. Prämisse vollständig? ─────────────────────────────────────────────
    premise = bible.get("premise") or {}
    missing = [k for k in REQUIRED_PREMISE if not _truthy(premise.get(k))]
    if not premise:
        f.append({"sev": "fail", "area": "premise", "msg": "premise.json fehlt oder leer"})
    elif missing:
        f.append({"sev": "fail", "area": "premise",
                  "msg": f"Pflichtfelder fehlen: {', '.join(missing)}"})
    else:
        f.append({"sev": "ok", "area": "premise", "msg": "logline/premise/frage/stakes vollständig"})

    # IDs sammeln (für Ref-Prüfung)
    char_ids = {c.get("id") for c in bible.get("characters", []) if c.get("id")}
    world_ids = {w.get("id") for w in bible.get("world", []) if w.get("id")}
    beats = bible.get("beats", [])
    beat_ids = {b.get("id") for b in beats if b.get("id")}

    # ── 2. Beats platziert? (+ Abweichung = WARNUNG) ─────────────────────────
    if not beats:
        f.append({"sev": "fail", "area": "beats", "msg": "beat-sheet.json fehlt/keine beats[]"})
    else:
        for mid, soll in WEILAND_MARKS.items():
            b = next((x for x in beats if x.get("id") == mid), None)
            if b is None:
                f.append({"sev": "fail", "area": "beats", "msg": f"Meilenstein '{mid}' fehlt im Beat-Sheet"})
                continue
            ist = b.get("ist_prozent")
            if ist is None:
                f.append({"sev": "fail", "area": "beats", "msg": f"Meilenstein '{mid}' nicht platziert (ist_prozent leer)"})
                continue
            soll_b = b.get("soll_prozent", soll)
            delta = abs(float(ist) - float(soll_b))
            if delta > tolerance:
                f.append({"sev": "warning", "area": "beats",
                          "msg": f"'{mid}' @ {ist}% (Soll {soll_b}%, Δ {delta:.0f}% > ±{tolerance}%) ⇒ WARNUNG, kein Block"})
            else:
                f.append({"sev": "ok", "area": "beats", "msg": f"'{mid}' @ {ist}% (Δ {delta:.0f}% ≤ ±{tolerance}%)"})

    # ── 3. Arcs an Akte gemappt? ─────────────────────────────────────────────
    chars = bible.get("characters", [])
    if not chars:
        f.append({"sev": "warning", "area": "arcs", "msg": "keine Figuren — Arc-Mapping nicht prüfbar"})
    for c in chars:
        cid = c.get("id", "<ohne id>")
        if not str(cid).startswith("CHAR-"):
            f.append({"sev": "fail", "area": "ids", "msg": f"Figur ohne gültige CHAR-ID: {cid}"})
        arc = c.get("arc_mapping") or {}
        miss = [a for a in ARC_FIELDS if not _truthy(arc.get(a))]
        if miss:
            f.append({"sev": "fail", "area": "arcs", "msg": f"{cid}: Arc nicht an Akte gemappt ({', '.join(miss)})"})
        else:
            f.append({"sev": "ok", "area": "arcs", "msg": f"{cid}: Arc akt1/akt2/akt3 gesetzt"})

    # ── 4./5. Szenen↔Beats + Refs ────────────────────────────────────────────
    scenes = bible.get("scenes", [])
    if not scenes:
        f.append({"sev": "fail", "area": "scenes", "msg": "scene-list.json fehlt/keine scenes[]"})
    for s in scenes:
        sid = s.get("id", "<ohne id>")
        if not str(sid).startswith("SCENE-"):
            f.append({"sev": "fail", "area": "ids", "msg": f"Szene ohne gültige SCENE-ID: {sid}"})
        bid = s.get("beat_id")
        if bid is None:
            f.append({"sev": "fail", "area": "scenes", "msg": f"{sid}: kein beat_id"})
        elif bid not in beat_ids:
            f.append({"sev": "fail", "area": "scenes", "msg": f"{sid}: beat_id '{bid}' existiert nicht im Beat-Sheet (dangling)"})
        pov = s.get("pov")
        if pov and char_ids and pov not in char_ids:
            f.append({"sev": "fail", "area": "refs", "msg": f"{sid}: pov '{pov}' ist keine existierende CHAR-ID"})
        for ref in s.get("bible_refs") or []:
            if ref.startswith("CHAR-") and char_ids and ref not in char_ids:
                f.append({"sev": "warning", "area": "refs", "msg": f"{sid}: bible_ref '{ref}' nicht in Character-Bible"})
            elif ref.startswith("WORLD-") and world_ids and ref not in world_ids:
                f.append({"sev": "warning", "area": "refs", "msg": f"{sid}: bible_ref '{ref}' nicht in World-Bible"})
    if scenes and not any(x["sev"] in ("fail", "error") and x["area"] in ("scenes", "refs") for x in f):
        f.append({"sev": "ok", "area": "scenes", "msg": f"{len(scenes)} Szenen: beat_id/Refs integer"})

    return f


def _report(findings: list[dict]) -> int:
    order = {"error": 0, "fail": 1, "warning": 2, "ok": 3}
    icon = {"error": "✗", "fail": "✗", "warning": "⚠", "ok": "✓"}
    for x in sorted(findings, key=lambda y: order[y["sev"]]):
        print(f"  {icon[x['sev']]} [{x['area']}] {x['msg']}")
    n_err = sum(1 for x in findings if x["sev"] == "error")
    n_fail = sum(1 for x in findings if x["sev"] == "fail")
    n_warn = sum(1 for x in findings if x["sev"] == "warning")
    n_ok = sum(1 for x in findings if x["sev"] == "ok")
    print(f"\n  Ergebnis: {n_err} Fehler, {n_fail} Gate-Verstöße, {n_warn} Warnungen, {n_ok} ok.")
    if n_err:
        return 2
    if n_fail:
        print("  ⛔ Planungs-Gate NICHT erfüllt — Pflichtartefakte vervollständigen (Phasenübergang hält).")
        return 1
    print("  ✅ Planungs-Gate erfüllt — Warnungen sind kein Block (Autor entscheidet).")
    return 0


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _resolve_bible_dir(path: str) -> str:
    cand = os.path.join(path, "_memory", "story-bible")
    if os.path.isdir(cand):
        return cand
    return path  # bereits ein story-bible-Ordner


def _load_project(path: str) -> dict:
    d = _resolve_bible_dir(path)
    bible: dict = {"premise": {}, "world": [], "characters": [], "beats": [], "scenes": [], "timeline": []}

    def opt(name):
        p = os.path.join(d, name)
        return _load_json(p) if os.path.isfile(p) else None

    prem = opt("premise.json")
    if prem:
        bible["premise"] = prem
    wb = opt("world-bible.json")
    if wb:
        bible["world"] = wb.get("entries", wb) if isinstance(wb, dict) else wb
    bs = opt("beat-sheet.json")
    if bs:
        bible["beats"] = bs.get("beats", bs) if isinstance(bs, dict) else bs
    sl = opt("scene-list.json")
    if sl:
        bible["scenes"] = sl.get("scenes", sl) if isinstance(sl, dict) else sl
    tl = opt("timeline.json")
    if tl:
        bible["timeline"] = tl.get("events", tl) if isinstance(tl, dict) else tl
    for cp in sorted(glob.glob(os.path.join(d, "CHAR-*.json"))):
        bible["characters"].append(_load_json(cp))
    return bible


def _selftest() -> int:
    print("Selftest: Planungs-Gate-Logik (good/bad)\n")
    good = {
        "premise": {"logline": "x", "premise_paragraph": "x", "central_question": "x", "stakes": {"a": 1}},
        "world": [{"id": "WORLD-001"}],
        "characters": [{"id": "CHAR-001", "arc_mapping": {"akt1_zustand": "a", "akt2_wende": "b", "akt3_zustand": "c"}}],
        "beats": [{"id": k, "ist_prozent": v} for k, v in WEILAND_MARKS.items()],
        "scenes": [{"id": "SCENE-001", "beat_id": "midpoint", "pov": "CHAR-001", "bible_refs": ["WORLD-001"]}],
    }
    bad = {
        "premise": {"logline": "x"},  # fehlt premise_paragraph/central_question/stakes
        "world": [], "characters": [{"id": "CHAR-001", "arc_mapping": {"akt1_zustand": "a"}}],  # Arc unvollständig
        "beats": [{"id": "midpoint", "ist_prozent": None}],  # nicht platziert + Meilensteine fehlen
        "scenes": [{"id": "SCENE-001", "beat_id": "ghost_beat", "pov": "CHAR-099"}],  # dangling beat_id + pov
    }
    print("[GOOD]"); rc_good = _report(check_planning(good))
    print("\n[BAD]"); rc_bad = _report(check_planning(bad))
    ok = (rc_good == 0 and rc_bad == 1)
    print(f"\n{'OK' if ok else 'FEHLGESCHLAGEN'}: good→{rc_good} (erwartet 0), bad→{rc_bad} (erwartet 1)")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Planungs-Gate (Phase 1)")
    ap.add_argument("project", nargs="?", help="Projektpfad (projects/<p>) oder story-bible-Ordner")
    ap.add_argument("--tolerance", type=float, default=DEFAULT_TOLERANCE)
    ap.add_argument("--selftest", action="store_true", help="interne Logik testen (keine Dateien nötig)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.project:
        ap.error("Projektpfad fehlt (oder --selftest verwenden).")
    try:
        bible = _load_project(args.project)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FEHLER: Story-Bible nicht lesbar/parsebar: {e}", file=sys.stderr)
        return 2
    print(f"NOVA Planungs-Gate — {args.project} (Toleranz ±{args.tolerance}%)\n")
    return _report(check_planning(bible, args.tolerance))


if __name__ == "__main__":
    raise SystemExit(main())
