#!/usr/bin/env python3
"""NOVA — Continuity-DB live (Phase 2, DR-13).

Liest die **unveränderten** Phase-1-Register (NovelWriter-Schema) — keine Umbenennung der IDs:

    projects/<p>/_memory/continuity/{characters,world,plots}.json
    projects/<p>/_memory/summaries/*.json            (Long-Memory aus nova-scene-summary)

Zwei Pfade (RecurrentGPT-Retrieval + NovelGenerator-Register):

  retrieve <projekt> [--refs IDs] [--pov ID] [--query "text"] [-k 5] [--json]
      Saliency-Pfad: Top-k saliente Records (Score = ID-Overlap×Gewicht + Term-Overlap),
      gibt ein token-armes Kontext-Bündel zurück (nur saliente Fakten in den Kontext, I4).
      Vektor-Embedding ist deferred (memory.md) → lexikalische Salienz, stdlib-only.

  update <projekt> --scene SCENE-ID
      Schreib-Pfad: setzt last_seen_scene für pov/bible_refs-Figuren (live-Tracking à la
      NovelGenerator `location`/Development); baut _memory/index/saliency.json neu.

Exit-Codes:  0 = ok   1 = inkonsistente Eingabe (z. B. unbekannte SCENE-ID)   2 = Aufruffehler
"""
from __future__ import annotations
import argparse
import json
import os
import re
import sys

ID_WEIGHT = 3.0   # Gewicht je geteilter Bible-ID (ID-Salienz > Term-Salienz)
SELF_WEIGHT = 4.0  # Bonus, wenn die Record-ID selbst angefragt ist
_STOP = {"der", "die", "das", "und", "ein", "eine", "den", "dem", "des", "mit", "für",
         "von", "aus", "auf", "ist", "the", "and", "for", "with", "her", "his", "she", "he"}


def _resolve_memory_dir(path: str) -> str:
    if os.path.basename(os.path.normpath(path)) == "_memory":
        return path
    return os.path.join(path, "_memory")


def _load_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def _opt(path: str):
    return _load_json(path) if os.path.isfile(path) else None


def _tok(text: str) -> set[str]:
    return {t for t in re.split(r"[^0-9A-Za-zÄÖÜäöüß]+", (text or "").lower())
            if len(t) >= 3 and t not in _STOP}


def build_records(mem_dir: str) -> list[dict]:
    """Flacher Retrieval-Korpus aus Registern + Summaries: {id, type, text, ids[]}."""
    cont = os.path.join(mem_dir, "continuity")
    recs: list[dict] = []

    for c in (_opt(os.path.join(cont, "characters.json")) or []):
        rel = c.get("relationships", {}) or {}
        text = " ".join([c.get("name", ""), c.get("status", ""),
                         " ".join(c.get("development_arc", []) or []),
                         " ".join(f"{k}:{v}" for k, v in rel.items())])
        recs.append({"id": c.get("id"), "type": "character", "text": text.strip(),
                     "ids": [c.get("id"), *rel.keys()], "raw": c})
    for w in (_opt(os.path.join(cont, "world.json")) or []):
        text = " ".join([w.get("name", ""), w.get("type", ""),
                         " ".join(w.get("rules", []) or []), w.get("kosten_grenzen", "")])
        recs.append({"id": w.get("id"), "type": "world", "text": text.strip(),
                     "ids": [w.get("id")], "raw": w})
    for p in (_opt(os.path.join(cont, "plots.json")) or []):
        text = " ".join([p.get("name", ""), p.get("status", ""),
                         " ".join(p.get("key_events", []) or []), " ".join(p.get("beats", []) or [])])
        recs.append({"id": p.get("id"), "type": "plot", "text": text.strip(),
                     "ids": [p.get("id"), *(p.get("related_characters", []) or [])], "raw": p})

    sum_dir = os.path.join(mem_dir, "summaries")
    if os.path.isdir(sum_dir):
        for fn in sorted(os.listdir(sum_dir)):
            if not fn.endswith(".json") or fn == "_state.json":
                continue
            s = _load_json(os.path.join(sum_dir, fn))
            text = " ".join([s.get("summary", ""), " ".join(s.get("key_facts", []) or [])])
            recs.append({"id": s.get("scene_id"), "type": "summary", "text": text.strip(),
                         "ids": [s.get("scene_id"), *(s.get("salient_ids", []) or [])], "raw": s})
    return recs


def _score(rec: dict, q_ids: set[str], q_tok: set[str]) -> float:
    rid = {i for i in rec.get("ids", []) if i}
    score = ID_WEIGHT * len(rid & q_ids)
    if rec.get("id") in q_ids:
        score += SELF_WEIGHT
    if q_tok:
        score += len(_tok(rec["text"]) & q_tok)
    return score


def retrieve(project: str, refs: list[str], pov: str | None, query: str, k: int, as_json: bool) -> int:
    mem_dir = _resolve_memory_dir(project)
    recs = build_records(mem_dir)
    q_ids = {x for x in [*refs, pov] if x}
    q_tok = _tok(query)
    if not q_ids and not q_tok:
        print("  ✗ weder --refs/--pov noch --query angegeben — keine Saliency-Anfrage.")
        return 1
    scored = sorted(((_score(r, q_ids, q_tok), r) for r in recs), key=lambda x: -x[0])
    top = [(sc, r) for sc, r in scored if sc > 0][:k]
    if as_json:
        print(json.dumps([{"id": r["id"], "type": r["type"], "score": sc, "text": r["text"]}
                          for sc, r in top], ensure_ascii=False, indent=2))
        return 0
    print(f"  Saliency-Bündel (Query-IDs: {', '.join(sorted(q_ids)) or '—'}; Top {k}):\n")
    if not top:
        print("  (keine salienten Records — leeres Register oder kein Treffer)")
        return 0
    for sc, r in top:
        print(f"  • [{r['type']}/{r['id']}] (score {sc:.0f}) {r['text'][:160]}")
    return 0


def update(project: str, scene_id: str) -> int:
    mem_dir = _resolve_memory_dir(project)
    sl = _opt(os.path.join(mem_dir, "story-bible", "scene-list.json"))
    scenes = (sl.get("scenes", sl) if isinstance(sl, dict) else sl) if sl else []
    scene = next((s for s in scenes if s.get("id") == scene_id), None)
    if scene is None:
        print(f"  ✗ {scene_id}: nicht in scene-list.json (unbekannte SCENE-ID)")
        return 1

    # Schreib-Pfad: last_seen_scene für pov + CHAR-bible_refs setzen
    char_path = os.path.join(mem_dir, "continuity", "characters.json")
    chars = _opt(char_path) or []
    touched = {scene.get("pov"), *[r for r in (scene.get("bible_refs") or []) if str(r).startswith("CHAR-")]}
    touched.discard(None)
    n = 0
    for c in chars:
        if c.get("id") in touched:
            c["last_seen_scene"] = scene_id
            n += 1
    if chars:
        with open(char_path, "w", encoding="utf-8") as fh:
            json.dump(chars, fh, ensure_ascii=False, indent=2)

    # Saliency-Index in _memory/index/ neu bauen (memory.md: index/ ab Phase 2 aktiv)
    idx_dir = os.path.join(mem_dir, "index")
    os.makedirs(idx_dir, exist_ok=True)
    recs = build_records(mem_dir)
    with open(os.path.join(idx_dir, "saliency.json"), "w", encoding="utf-8") as fh:
        json.dump([{"id": r["id"], "type": r["type"], "ids": r["ids"], "text": r["text"]} for r in recs],
                  fh, ensure_ascii=False, indent=2)

    print(f"  ✓ last_seen_scene={scene_id} für {n} Figur(en): {', '.join(sorted(touched))}")
    print(f"  ✓ index/saliency.json neu gebaut ({len(recs)} Records)")
    return 0


def _selftest() -> int:
    import tempfile
    print("Selftest: Continuity-DB (Retrieval-Ranking + last_seen-Update)\n")
    with tempfile.TemporaryDirectory() as tmp:
        cont = os.path.join(tmp, "_memory", "continuity")
        sb = os.path.join(tmp, "_memory", "story-bible")
        os.makedirs(cont); os.makedirs(sb)
        with open(os.path.join(cont, "characters.json"), "w", encoding="utf-8") as fh:
            json.dump([{"id": "CHAR-001", "name": "Mira Halt", "status": "alive",
                        "relationships": {"CHAR-002": "Rivale"}, "development_arc": ["Trauer"]},
                       {"id": "CHAR-002", "name": "Brandt", "status": "alive", "development_arc": ["Gier"]}], fh)
        with open(os.path.join(cont, "world.json"), "w", encoding="utf-8") as fh:
            json.dump([{"id": "WORLD-002", "name": "Zeitmechanik", "type": "magic_system",
                        "rules": ["Zeit zurückdrehen"], "kosten_grenzen": "kostet Lebenszeit"}], fh)
        with open(os.path.join(cont, "plots.json"), "w", encoding="utf-8") as fh:
            json.dump([], fh)
        with open(os.path.join(sb, "scene-list.json"), "w", encoding="utf-8") as fh:
            json.dump({"scenes": [{"id": "SCENE-005", "pov": "CHAR-001",
                                   "bible_refs": ["CHAR-001", "WORLD-002"]}]}, fh)
        # Retrieval: Query nach CHAR-001 → CHAR-001 muss top sein
        recs = build_records(_resolve_memory_dir(tmp))
        scored = sorted(((_score(r, {"CHAR-001"}, set()), r) for r in recs), key=lambda x: -x[0])
        top_is_char1 = scored[0][1]["id"] == "CHAR-001" and scored[0][0] >= SELF_WEIGHT
        rc_up = update(tmp, "SCENE-005")
        c1 = next(c for c in _load_json(os.path.join(cont, "characters.json")) if c["id"] == "CHAR-001")
        idx_built = os.path.isfile(os.path.join(tmp, "_memory", "index", "saliency.json"))
        rc_bad = update(tmp, "SCENE-999")  # unbekannt → 1
        ok = (top_is_char1 and rc_up == 0 and c1.get("last_seen_scene") == "SCENE-005"
              and idx_built and rc_bad == 1)
        print(f"  Retrieval top={scored[0][1]['id']} (erwartet CHAR-001); last_seen={c1.get('last_seen_scene')}")
        print(f"  index gebaut={idx_built}; bad→{rc_bad} (erwartet 1)")
        print("OK" if ok else "FEHLGESCHLAGEN")
        return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Continuity-DB (Phase 2)")
    sub = ap.add_subparsers(dest="cmd")

    r = sub.add_parser("retrieve", help="Saliency-Retrieval (Kontext-Bündel)")
    r.add_argument("project")
    r.add_argument("--refs", default="", help="kommagetrennte Bible-IDs")
    r.add_argument("--pov", default=None)
    r.add_argument("--query", default="")
    r.add_argument("-k", type=int, default=5)
    r.add_argument("--json", action="store_true")

    u = sub.add_parser("update", help="Schreib-Pfad: last_seen + Saliency-Index")
    u.add_argument("project")
    u.add_argument("--scene", required=True)

    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    try:
        if args.cmd == "retrieve":
            refs = [x.strip() for x in args.refs.split(",") if x.strip()]
            print(f"NOVA Continuity-DB retrieve — {args.project}\n")
            return retrieve(args.project, refs, args.pov, args.query, args.k, args.json)
        if args.cmd == "update":
            print(f"NOVA Continuity-DB update — {args.project} · {args.scene}\n")
            return update(args.project, args.scene)
    except (OSError, json.JSONDecodeError) as e:
        print(f"FEHLER: {e}", file=sys.stderr)
        return 2
    ap.error("Subcommand fehlt (retrieve|update) oder --selftest verwenden.")


if __name__ == "__main__":
    raise SystemExit(main())
