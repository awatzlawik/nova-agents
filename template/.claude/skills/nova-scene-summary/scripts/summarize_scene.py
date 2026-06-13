#!/usr/bin/env python3
"""NOVA — Szenen-Summary-Pipeline (Phase 2, DR-12).

Deterministische Memory-I/O für Szenen-Summaries nach dem RecurrentGPT-Muster
(Kurz-/Langzeit-Memory): pro Szene ein **Long-Memory**-Record, dazu eine fortlaufend
aktualisierte **Short-Memory** (rollende Gesamt-Summary, token-arm).

Wichtig (Invariante 1): der **Inhalt** der Summary kommt vom Autor / von der Persona
(SUGGEST, In-Context). Dieses Skript besorgt nur die **Mechanik** (Append / Roll / Index) —
kein LLM-Augenmaß. Geschrieben wird ins Phase-0-Memory-Layout (nova/conventions/memory.md):

    projects/<p>/_memory/summaries/<SCENE-ID>.json   # Long-Memory-Record je Szene
    projects/<p>/_memory/summaries/_state.json       # { short_memory, long_memory_order[] }

Subcommands:
    write <projekt> --scene SCENE-ID --summary "…" [--key-facts a,b] [--salient CHAR-001,WORLD-002]
    show  <projekt>

Exit-Codes:  0 = ok        1 = inkonsistente Eingabe (z. B. SCENE-ID nicht in scene-list)
             2 = Aufruffehler (Pfad/JSON kaputt)

Short-Memory rollt über die zuletzt geschriebenen Summaries bis zu einem Wort-Budget
(Default 400, wie RecurrentGPTs ~400-Wort-Kurzgedächtnis).
"""
from __future__ import annotations
import argparse
import json
import os
import sys

DEFAULT_SHORT_BUDGET = 400  # Wörter (RecurrentGPT short_memory ≈ 400)


def _resolve_memory_dir(path: str) -> str:
    """Akzeptiert projects/<p>, projects/<p>/_memory oder einen _memory-Ordner."""
    if os.path.basename(os.path.normpath(path)) == "_memory":
        return path
    cand = os.path.join(path, "_memory")
    if os.path.isdir(cand):
        return cand
    return cand  # noch nicht existent → wird angelegt


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _scene_card(mem_dir: str, scene_id: str) -> dict | None:
    """Liest beat_id/pov/akt aus story-bible/scene-list.json (Kontext-Anreicherung)."""
    sl = os.path.join(mem_dir, "story-bible", "scene-list.json")
    if not os.path.isfile(sl):
        return None
    data = _load_json(sl)
    scenes = data.get("scenes", data) if isinstance(data, dict) else data
    for s in scenes:
        if s.get("id") == scene_id:
            return s
    return None


def _roll_short_memory(mem_dir: str, order: list[str], budget: int) -> str:
    """Rollende Kurz-Summary: jüngste Records zuerst, bis Wort-Budget erschöpft."""
    parts: list[str] = []
    words = 0
    for sid in reversed(order):
        rec_path = os.path.join(mem_dir, "summaries", f"{sid}.json")
        if not os.path.isfile(rec_path):
            continue
        rec = _load_json(rec_path)
        text = (rec.get("summary") or "").strip()
        if not text:
            continue
        n = len(text.split())
        if words + n > budget and parts:
            break
        parts.append(f"[{sid}] {text}")
        words += n
    parts.reverse()  # chronologisch ausgeben
    return "\n".join(parts)


def write_summary(project: str, scene_id: str, summary: str,
                  key_facts: list[str], salient: list[str],
                  budget: int = DEFAULT_SHORT_BUDGET) -> int:
    mem_dir = _resolve_memory_dir(project)
    sum_dir = os.path.join(mem_dir, "summaries")
    os.makedirs(sum_dir, exist_ok=True)

    card = _scene_card(mem_dir, scene_id)
    if card is None and os.path.isfile(os.path.join(mem_dir, "story-bible", "scene-list.json")):
        print(f"  ✗ {scene_id}: nicht in scene-list.json (unbekannte SCENE-ID)")
        return 1

    # salient_ids: explizit + aus der Szenenkarte (bible_refs/pov) abgeleitet
    salient_ids = list(dict.fromkeys(
        [*salient, *(card.get("bible_refs", []) if card else []),
         *([card["pov"]] if card and card.get("pov") else [])]
    ))
    chars = [i for i in salient_ids if str(i).startswith("CHAR-")]

    record = {
        "scene_id": scene_id,
        "beat_id": card.get("beat_id") if card else None,
        "pov": card.get("pov") if card else None,
        "akt": card.get("akt") if card else None,
        "summary": summary.strip(),
        "key_facts": key_facts,
        "salient_ids": salient_ids,
        "chars": chars,
    }
    with open(os.path.join(sum_dir, f"{scene_id}.json"), "w", encoding="utf-8") as fh:
        json.dump(record, fh, ensure_ascii=False, indent=2)

    # _state.json: long_memory_order anhängen (idempotent), short_memory rollen
    state_path = os.path.join(sum_dir, "_state.json")
    state = _load_json(state_path) if os.path.isfile(state_path) else {"short_memory": "", "long_memory_order": []}
    order = state.get("long_memory_order", [])
    if scene_id not in order:
        order.append(scene_id)
    state["long_memory_order"] = order
    state["short_memory"] = _roll_short_memory(mem_dir, order, budget)
    with open(state_path, "w", encoding="utf-8") as fh:
        json.dump(state, fh, ensure_ascii=False, indent=2)

    print(f"  ✓ Long-Memory: summaries/{scene_id}.json (beat={record['beat_id']}, pov={record['pov']})")
    print(f"  ✓ Short-Memory aktualisiert ({len(order)} Szene(n), Budget ±{budget} Wörter)")
    if salient_ids:
        print(f"  ✓ Saliente IDs: {', '.join(salient_ids)}")
    return 0


def show(project: str) -> int:
    mem_dir = _resolve_memory_dir(project)
    state_path = os.path.join(mem_dir, "summaries", "_state.json")
    if not os.path.isfile(state_path):
        print("  (keine Summaries — _state.json fehlt)")
        return 0
    state = _load_json(state_path)
    order = state.get("long_memory_order", [])
    print(f"  Long-Memory: {len(order)} Szene(n) — {', '.join(order) or '—'}\n")
    print("  Short-Memory (rollend):")
    for line in (state.get("short_memory") or "  —").splitlines():
        print(f"    {line}")
    return 0


def _selftest() -> int:
    import tempfile
    print("Selftest: Summary-Pipeline (Append / Roll / Index)\n")
    with tempfile.TemporaryDirectory() as tmp:
        # Minimal-Szenenliste anlegen, damit Anreicherung greift
        sb = os.path.join(tmp, "_memory", "story-bible")
        os.makedirs(sb, exist_ok=True)
        with open(os.path.join(sb, "scene-list.json"), "w", encoding="utf-8") as fh:
            json.dump({"scenes": [
                {"id": "SCENE-001", "beat_id": "hook", "pov": "CHAR-001", "akt": 1, "bible_refs": ["WORLD-001"]},
                {"id": "SCENE-002", "beat_id": "inciting_incident", "pov": "CHAR-001", "akt": 1, "bible_refs": ["WORLD-001"]},
            ]}, fh)
        rc1 = write_summary(tmp, "SCENE-001", "Mira bemerkt den Aussetzer.", ["uhr stockt"], ["CHAR-001"])
        rc2 = write_summary(tmp, "SCENE-002", "Die Stadtuhr bleibt stehen.", [], [])
        rc_bad = write_summary(tmp, "SCENE-999", "Geisterszene.", [], [])  # nicht in scene-list → 1
        state = _load_json(os.path.join(tmp, "_memory", "summaries", "_state.json"))
        rec1 = _load_json(os.path.join(tmp, "_memory", "summaries", "SCENE-001.json"))
        order_ok = state["long_memory_order"] == ["SCENE-001", "SCENE-002"]
        enrich_ok = rec1["beat_id"] == "hook" and "WORLD-001" in rec1["salient_ids"]
        short_ok = "SCENE-002" in state["short_memory"]
        ok = (rc1 == 0 and rc2 == 0 and rc_bad == 1 and order_ok and enrich_ok and short_ok)
        print(f"\n  order={state['long_memory_order']} (erwartet SCENE-001,SCENE-002)")
        print(f"  Anreicherung beat/refs: {enrich_ok}; bad→{rc_bad} (erwartet 1)")
        print("OK" if ok else "FEHLGESCHLAGEN")
        return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Szenen-Summary-Pipeline (Phase 2)")
    sub = ap.add_subparsers(dest="cmd")

    w = sub.add_parser("write", help="Summary einer Szene schreiben + Memory aktualisieren")
    w.add_argument("project", help="Projektpfad (projects/<p>)")
    w.add_argument("--scene", required=True, help="SCENE-ID")
    w.add_argument("--summary", required=True, help="Summary-Text (vom Autor/Persona)")
    w.add_argument("--key-facts", default="", help="kommagetrennt")
    w.add_argument("--salient", default="", help="kommagetrennte IDs (CHAR-/WORLD-…)")
    w.add_argument("--short-budget", type=int, default=DEFAULT_SHORT_BUDGET)

    s = sub.add_parser("show", help="Memory-Übersicht (short + Reihenfolge)")
    s.add_argument("project")

    ap.add_argument("--selftest", action="store_true", help="interne Logik testen (tmp, keine Projektdaten nötig)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if args.cmd == "write":
        kf = [x.strip() for x in args.key_facts.split(",") if x.strip()]
        sal = [x.strip() for x in args.salient.split(",") if x.strip()]
        try:
            print(f"NOVA Szenen-Summary — {args.project} · {args.scene}\n")
            return write_summary(args.project, args.scene, args.summary, kf, sal, args.short_budget)
        except (OSError, json.JSONDecodeError) as e:
            print(f"FEHLER: {e}", file=sys.stderr)
            return 2
    if args.cmd == "show":
        try:
            print(f"NOVA Szenen-Summary — {args.project}\n")
            return show(args.project)
        except (OSError, json.JSONDecodeError) as e:
            print(f"FEHLER: {e}", file=sys.stderr)
            return 2
    ap.error("Subcommand fehlt (write|show) oder --selftest verwenden.")


if __name__ == "__main__":
    raise SystemExit(main())
