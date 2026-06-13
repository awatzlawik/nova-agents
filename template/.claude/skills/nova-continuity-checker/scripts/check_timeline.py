#!/usr/bin/env python3
"""NOVA — Continuity-Checker / Continuity-Gate (Phase 3, DR-18) — Deep-Layer.

Erweitert den mechanischen Phase-2-Kern (`check_continuity.py`: ID/Status/Position **je Szene**)
um die **projekt-weite** Zeit-/Ort-/Fakten-Konsistenz über die Register hinweg.
**Wiederverwendung (kein zweites Register, dieselben IDs/Marken):** importiert
`load_bible` + `check_passage` aus `nova-continuity-check` (das wiederum `WEILAND_MARKS` aus
`nova-beat-percentage-check` importiert). Vorbild: NovelWriter `ConsistencyAgent`
(Character/World/PlotThread-Tracking + Widerspruchs-Report).

Geprüft:
  D1 Szenen-Audit (reuse check_passage je Szene): dangling CHAR-/WORLD-Refs, toter POV;
     zusätzlich scene.ort ∈ World-Register. Position-Abweichung = WARNUNG (I2).
  D2 Timeline-Refs:   event.erzaehl_position ∈ Szenen; event.bible_refs ∈ CHAR/WORLD.
  D3 Datum/Wetter:    Events mit identischem chrono_zeit, aber abweichendem wetter_datum = Widerspruch.
  D4 Plot-Register:   plots.related_characters ∈ CHAR; .beats ∈ Beat-Sheet-IDs; .key_events ∈ TIME-IDs.

Volle LLM-**Subtext**-Widerspruchserkennung (Zeit/Ort/Fakten/POV, parallele **read-only-Subagenten**)
liegt in der Persona-Schicht (`nova-continuity-checker/SKILL.md`); dieses Skript ist die
mechanische, erklärbare **harte Garantie** (Skill-first-Philosophie, phase0/05).

**Invariante 2:** Positions-Abweichung = WARNUNG; echte Widersprüche (dangling/toter POV/Datum) = fail.
Exit-Codes:  0 = ok / nur Warnung   1 = Widerspruch   2 = Aufruffehler
"""
from __future__ import annotations
import argparse
import json
import os
import sys

# Mechanischer Kern aus der Phase-2-Nachprüfung (eine Quelle: load_bible + check_passage + Marken).
load_bible = check_passage = _resolve_memory_dir = None
try:
    _sib = os.path.join(os.path.dirname(__file__), "..", "..", "nova-continuity-check", "scripts")
    sys.path.insert(0, os.path.abspath(_sib))
    from check_continuity import (  # type: ignore
        load_bible as _lb, check_passage as _cp, _resolve_memory_dir as _rmd, DEAD,
    )
    load_bible, check_passage, _resolve_memory_dir = _lb, _cp, _rmd
except Exception:
    DEAD = {"dead", "tot", "gestorben", "verstorben", "deceased"}


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _opt(path: str):
    return _load_json(path) if os.path.isfile(path) else None


def _resolve_mem(path: str) -> str:
    if _resolve_memory_dir is not None:
        return _resolve_memory_dir(path)
    return path if os.path.basename(os.path.normpath(path)) == "_memory" else os.path.join(path, "_memory")


def load_extra(mem_dir: str) -> dict:
    """Timeline-Events + Plot-Threads (für D2–D4). Register selbst kommen aus load_bible."""
    sb, cont = os.path.join(mem_dir, "story-bible"), os.path.join(mem_dir, "continuity")
    tl = _opt(os.path.join(sb, "timeline.json")) or {}
    events = tl.get("events", tl) if isinstance(tl, (dict, list)) else []
    events = events if isinstance(events, list) else []
    plots = _opt(os.path.join(cont, "plots.json")) or []
    return {"events": events, "plots": plots}


def deep_check(bible: dict, extra: dict, tolerance: float = 5) -> list[dict]:
    """Projekt-weite Befunde. severity ∈ {ok, warning, fail}."""
    f: list[dict] = []
    chars, world, beats, scenes = bible["characters"], bible["world"], bible["beats"], bible["scenes"]
    char_ids, world_ids = set(chars), set(world)
    scene_ids, beat_ids = set(scenes), set(beats)

    # ── D1: Szenen-Audit (reuse check_passage) + ort-Existenz ────────────────
    audited = 0
    for sid, s in scenes.items():
        for x in (check_passage(bible, s, "", tolerance) if check_passage else []):
            if x["sev"] in ("fail", "warning"):
                f.append({"sev": x["sev"], "area": f"scene/{sid}", "msg": x["msg"]})
        ort = s.get("ort")
        if ort and str(ort).startswith("WORLD-") and ort not in world_ids:
            f.append({"sev": "fail", "area": f"scene/{sid}", "msg": f"ort '{ort}' existiert nicht im World-Register (dangling)"})
        audited += 1
    if audited and not any(x["sev"] == "fail" and x["area"].startswith("scene/") for x in f):
        f.append({"sev": "ok", "area": "scenes", "msg": f"{audited} Szenen auditiert: IDs/POV/ort konsistent"})

    # ── D2: Timeline-Referenzen ──────────────────────────────────────────────
    events = extra["events"]
    for e in events:
        eid = e.get("id", "<TIME-?>")
        ep = e.get("erzaehl_position")
        if ep and ep not in scene_ids:
            f.append({"sev": "fail", "area": f"timeline/{eid}", "msg": f"erzaehl_position '{ep}' ist keine existierende SCENE"})
        for ref in e.get("bible_refs") or []:
            if ref.startswith("CHAR-") and ref not in char_ids:
                f.append({"sev": "fail", "area": f"timeline/{eid}", "msg": f"bible_ref '{ref}' nicht im Character-Register"})
            elif ref.startswith("WORLD-") and ref not in world_ids:
                f.append({"sev": "fail", "area": f"timeline/{eid}", "msg": f"bible_ref '{ref}' nicht im World-Register"})

    # ── D3: Datum/Wetter-Widerspruch (gleiche chrono_zeit → gleiches wetter_datum) ─
    by_chrono: dict[str, set[str]] = {}
    chrono_event: dict[str, str] = {}
    for e in events:
        cz, wd = e.get("chrono_zeit"), e.get("wetter_datum")
        if cz and wd:
            by_chrono.setdefault(cz, set()).add(wd)
            chrono_event.setdefault(cz, e.get("id", "?"))
    for cz, wds in by_chrono.items():
        if len(wds) > 1:
            f.append({"sev": "fail", "area": "timeline/datum",
                      "msg": f"chrono_zeit '{cz}' hat widersprüchliche wetter_datum: {sorted(wds)}"})
    if events and not any(x["area"].startswith("timeline") and x["sev"] == "fail" for x in f):
        f.append({"sev": "ok", "area": "timeline", "msg": f"{len(events)} Timeline-Events: Refs + Datum/Wetter konsistent"})

    # ── D4: Plot-Register-Integrität ─────────────────────────────────────────
    plots = extra["plots"]
    time_ids = {e.get("id") for e in events if e.get("id")}
    for p in plots:
        pid = p.get("id", "<PLOT-?>")
        for c in p.get("related_characters") or []:
            if c not in char_ids:
                f.append({"sev": "fail", "area": f"plot/{pid}", "msg": f"related_character '{c}' nicht im Register"})
        for b in p.get("beats") or []:
            if beat_ids and b not in beat_ids:
                f.append({"sev": "fail", "area": f"plot/{pid}", "msg": f"beat '{b}' nicht im Beat-Sheet (dangling)"})
        for k in p.get("key_events") or []:
            if time_ids and k not in time_ids:
                f.append({"sev": "fail", "area": f"plot/{pid}", "msg": f"key_event '{k}' nicht in der Timeline (dangling)"})
    if plots and not any(x["area"].startswith("plot/") and x["sev"] == "fail" for x in f):
        f.append({"sev": "ok", "area": "plots", "msg": f"{len(plots)} Plot-Threads: Char/Beat/Event-Refs integer"})
    return f


def _report(findings: list[dict]) -> int:
    order = {"fail": 0, "warning": 1, "ok": 2}
    icon = {"fail": "✗", "warning": "⚠", "ok": "✓"}
    for x in sorted(findings, key=lambda y: order[y["sev"]]):
        print(f"  {icon[x['sev']]} [{x['area']}] {x['msg']}")
    n_fail = sum(1 for x in findings if x["sev"] == "fail")
    n_warn = sum(1 for x in findings if x["sev"] == "warning")
    print(f"\n  Ergebnis: {n_fail} Widerspruch/Widersprüche, {n_warn} Warnung(en).")
    if n_fail:
        print("  ⛔ Continuity-Widerspruch (Zeit/Ort/Fakten/POV) — zurück an den Autor.")
        return 1
    print("  ✅ Continuity konsistent (Warnungen sind kein Block — Autor entscheidet, I2).")
    return 0


def _fixture(consistent: bool) -> tuple[dict, dict]:
    """Mini-Register; consistent=False enthält die EINGEBAUTEN Test-Widersprüche (DoD G-Item 2)."""
    bible = {
        "characters": {"CHAR-001": {"id": "CHAR-001", "status": "alive"},
                       "CHAR-002": {"id": "CHAR-002", "status": "alive"},
                       "CHAR-009": {"id": "CHAR-009", "status": "tot"}},
        "world": {"WORLD-001": {"id": "WORLD-001"}, "WORLD-002": {"id": "WORLD-002"}},
        "beats": {"midpoint": {"id": "midpoint", "soll_prozent": 50, "ist_prozent": 50}},
        "scenes": {
            "SCENE-001": {"id": "SCENE-001", "pov": "CHAR-001", "ort": "WORLD-001",
                          "bible_refs": ["WORLD-001"], "beat_id": "midpoint"},
        },
    }
    if not consistent:
        # (a) toter POV spricht, (b) dangling ort
        bible["scenes"]["SCENE-002"] = {"id": "SCENE-002", "pov": "CHAR-009", "ort": "WORLD-404",
                                        "bible_refs": [], "beat_id": "midpoint"}
        events = [
            {"id": "TIME-001", "erzaehl_position": "SCENE-001", "chrono_zeit": "Tag 5",
             "wetter_datum": "Tag 5, Sonne", "bible_refs": ["WORLD-001"]},
            # (c) gleiche chrono_zeit, widersprüchliches Wetter
            {"id": "TIME-002", "erzaehl_position": "SCENE-001", "chrono_zeit": "Tag 5",
             "wetter_datum": "Tag 5, Schneesturm", "bible_refs": ["CHAR-001"]},
            # (d) dangling erzaehl_position
            {"id": "TIME-003", "erzaehl_position": "SCENE-777", "chrono_zeit": "Tag 6",
             "wetter_datum": "Tag 6", "bible_refs": []},
        ]
        # (e) dangling key_event
        plots = [{"id": "PLOT-001", "related_characters": ["CHAR-001"], "beats": ["midpoint"],
                  "key_events": ["TIME-404"]}]
    else:
        events = [{"id": "TIME-001", "erzaehl_position": "SCENE-001", "chrono_zeit": "Tag 5",
                   "wetter_datum": "Tag 5, Sonne", "bible_refs": ["WORLD-001"]}]
        plots = [{"id": "PLOT-001", "related_characters": ["CHAR-001"], "beats": ["midpoint"],
                  "key_events": ["TIME-001"]}]
    return bible, {"events": events, "plots": plots}


def _selftest() -> int:
    if check_passage is None:
        print("FEHLER: konnte check_continuity nicht importieren (Schwester-Skill fehlt?).", file=sys.stderr)
        return 1
    print("Selftest: Deep-Continuity (konsistent vs. eingebaute Test-Widersprüche)\n")
    gb, ge = _fixture(True)
    bb, be = _fixture(False)
    print("[KONSISTENT]"); rc_good = _report(deep_check(gb, ge))
    bad = deep_check(bb, be)
    print("\n[EINGEBAUTE WIDERSPRÜCHE]"); rc_bad = _report(bad)
    areas = {x["area"].split("/")[0] for x in bad if x["sev"] == "fail"}
    # erwartet: toter POV/dangling ort (scene), Datum-Wetter (timeline), dangling key_event (plot)
    ok = (rc_good == 0 and rc_bad == 1 and {"scene", "timeline", "plot"} <= areas)
    print(f"\n{'OK' if ok else 'FEHLGESCHLAGEN'}: good→{rc_good} (erwartet 0), bad→{rc_bad} (erwartet 1); "
          f"Widerspruchs-Bereiche={sorted(areas)}")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Continuity-Checker / Deep-Continuity-Gate (Phase 3)")
    ap.add_argument("project", nargs="?", help="Projektpfad (projects/<p>)")
    ap.add_argument("--tolerance", type=float, default=5)
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.project:
        ap.error("Projektpfad fehlt (oder --selftest verwenden).")
    if load_bible is None:
        print("FEHLER: konnte check_continuity (load_bible) nicht importieren.", file=sys.stderr)
        return 2
    try:
        mem = _resolve_mem(args.project)
        bible = load_bible(mem)
        extra = load_extra(mem)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2
    print(f"NOVA Continuity-Checker (deep) — {args.project}\n")
    return _report(deep_check(bible, extra, args.tolerance))


if __name__ == "__main__":
    raise SystemExit(main())
