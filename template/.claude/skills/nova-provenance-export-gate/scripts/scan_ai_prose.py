#!/usr/bin/env python3
"""NOVA — Provenienz-Scanner / Pre-Export-Gate (Invariante 5, Overview Rec.5).

Scannt Manuskript-Dateien nach NOVA-KI-Provenienz-Markern:

    <!-- NOVA:AI start agent=<id> mode=GHOSTWRITE ts=<iso> -->
    ... KI-Prosa ...
    <!-- NOVA:AI end -->

Aufgaben:
  1. Marker-Balance prüfen (jedes start hat genau ein end; keine Verschachtelung).      [Phase 0]
  2. KI-Spannen auflisten (Datei, Zeilen, Agent, ts, Text).
  3. **Ledger↔Markup-Abgleich** (Phase 4, DR-22): IDs/Spannen, die laut Provenienz-Ledger
     als KI **akzeptiert** gelten, MÜSSEN im Manuskript markiert sein. Akzeptierte, aber
     **unmarkierte** KI-Prosa ⇒ BLOCK (Overview Rec.5). Ledger-Quelle: Git-Commits
     (`--git`, Trailer `NOVA-Provenance: ghostwrite`) ODER Datei (`--ledger ledger.json`).

Das "harte" Gate: **unbalancierte/kaputte Marker ODER unmarkierte akzeptierte KI-Prosa ⇒ BLOCK** (Exit 1).
So kann vor Export keine still entmarkte oder zerbrochene KI-Provenienz durchrutschen.

Die zwei Provenienz-Spuren (nova/conventions/provenance.md) bleiben das Schema:
Inline-Markup **und** `ai:`-Commit. Dieser Scanner ist die EINE Quelle — er wird erweitert, nicht ersetzt.

Exit-Codes:  0 = sauber           1 = BLOCK (kaputte Marker ODER unmarkierte akzeptierte KI-Prosa)
             2 = Aufruffehler (keine Dateien etc.)
"""
from __future__ import annotations
import argparse
import glob
import hashlib
import json
import re
import subprocess
import sys

START_RE = re.compile(r"<!--\s*NOVA:AI\s+start(?P<attrs>[^>]*)-->")
END_RE = re.compile(r"<!--\s*NOVA:AI\s+end\s*-->")
ATTR_RE = re.compile(r"(\w+)=([^\s]+)")


def _norm(s: str) -> str:
    """Whitespace-/Case-normalisiert für stabilen Text-Vergleich (Markup ↔ Ledger)."""
    return re.sub(r"\s+", " ", (s or "")).strip().lower()


def _sha(s: str) -> str:
    return hashlib.sha256(_norm(s).encode("utf-8")).hexdigest()


def scan_text(text: str):
    """Gibt (spans, errors) zurück. spans: erkannte KI-Passagen (inkl. ts + Text); errors: Marker-Defekte."""
    spans, errors = [], []
    open_at = None  # {"line": int, "attrs": dict, "lines": [str]}
    for lineno, line in enumerate(text.splitlines(), 1):
        has_start = bool(START_RE.search(line))
        has_end = bool(END_RE.search(line))
        for m in START_RE.finditer(line):
            if open_at is not None:
                errors.append(f"Zeile {lineno}: 'start' ohne vorheriges 'end' "
                              f"(offener Marker seit Zeile {open_at['line']}) — Verschachtelung unzulässig")
            attrs = dict(ATTR_RE.findall(m.group("attrs") or ""))
            open_at = {"line": lineno, "attrs": attrs, "lines": []}
        # Reine Prosa-Zeile (kein Marker) innerhalb einer offenen Spanne ⇒ zum KI-Text zählen.
        if open_at is not None and not has_start and not has_end:
            open_at["lines"].append(line)
        for _ in END_RE.finditer(line):
            if open_at is None:
                errors.append(f"Zeile {lineno}: 'end' ohne offenes 'start'")
            else:
                a = open_at["attrs"]
                spans.append({"start_line": open_at["line"], "end_line": lineno,
                              "agent": a.get("agent", "?"), "mode": a.get("mode", "?"),
                              "ts": a.get("ts", "?"), "variant": a.get("variant"),
                              "text": "\n".join(open_at["lines"]).strip()})
                open_at = None
    if open_at is not None:
        errors.append(f"Zeile {open_at['line']}: 'start' nie geschlossen (kein 'end')")
    return spans, errors


# ─────────────────────────────────────────────────────────────────────────────
# Phase 4 (DR-22): Ledger↔Markup-Abgleich
# ─────────────────────────────────────────────────────────────────────────────

def _match_span(entry: dict, spans: list[dict]):
    """Findet die markierte Spanne zu einem Ledger-Eintrag (agent+ts, sonst Text-Hash)."""
    et, ea = entry.get("ts"), entry.get("agent")
    eh = entry.get("text_sha256") or (_sha(entry["text"]) if entry.get("text") else None)
    for s in spans:
        if et and ea and s.get("ts") == et and s.get("agent") == ea:
            return s
        if eh and s.get("text") and _sha(s["text"]) == eh:
            return s
    return None


def reconcile_ledger(full_text: str, spans: list[dict], entries: list[dict]) -> list[str]:
    """Gleicht den Provenienz-Ledger gegen die markierten Spannen ab.

    Regel (Rec.5):
      - 'accepted'-Eintrag OHNE markierte Spanne, dessen Text aber im Manuskript steht ⇒ unmarked-ai ⇒ BLOCK.
        (Text gar nicht im Manuskript ⇒ der Autor hat die Passage überschrieben — erlaubt, kein Block.)
      - 'discarded'-Eintrag, dessen Text dennoch im Manuskript steht ⇒ verworfene KI-Prosa eingeschlichen ⇒ BLOCK.
    """
    errors: list[str] = []
    norm_full = _norm(full_text)
    for e in entries:
        status = e.get("status", "accepted")
        etext = e.get("text")
        present = bool(etext) and _norm(etext) in norm_full
        if status == "accepted":
            if _match_span(e, spans):
                continue  # sauber markiert
            if present:
                errors.append(f"Ledger {e.get('ts','?')}/{e.get('agent','?')} (Szene {e.get('scene','?')}): "
                              f"akzeptierte KI-Prosa steht im Manuskript, ist aber NICHT markiert ⇒ unmarked-ai")
            # nicht präsent ⇒ vom Autor überschrieben (erlaubt, provenance.md §4) — kein Block.
        elif status == "discarded":
            if present:
                errors.append(f"Ledger {e.get('ts','?')}/{e.get('agent','?')}: als 'discarded' geführt, "
                              f"aber im Manuskript gefunden ⇒ verworfene KI-Prosa eingeschlichen")
    return errors


def git_ledger(pathspec: str = "projects/*/manuscript/*.md") -> list[dict]:
    """Leitet Ledger-Einträge aus `ai:`-Commits (Trailer NOVA-Provenance: ghostwrite) ab.

    Pro Commit ein Eintrag {agent, ts, status: accepted, text}: die hinzugefügten Prosa-Zeilen
    (ohne Marker-Kommentare). Produktivpfad — greift, sobald das Repo solche Commits hat.
    Defensiv: kein Git / keine Treffer ⇒ leere Liste (kein Fehler).
    """
    def _git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout

    try:
        out = _git("log", "--grep=NOVA-Provenance: ghostwrite", "--format=%H|%cI")
    except (OSError, subprocess.CalledProcessError):
        return []
    entries: list[dict] = []
    for line in filter(None, out.splitlines()):
        h, _, ts = line.partition("|")
        try:
            diff = _git("show", "--format=", "--unified=0", h, "--", pathspec)
        except (OSError, subprocess.CalledProcessError):
            continue
        added = [ln[1:] for ln in diff.splitlines()
                 if ln.startswith("+") and not ln.startswith("+++")
                 and "NOVA:AI" not in ln]
        text = "\n".join(added).strip()
        if text:
            entries.append({"agent": "nova-ghostwrite", "ts": ts, "status": "accepted",
                            "text": text, "scene": h[:8], "_source": "git"})
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA Provenienz-Export-Gate")
    ap.add_argument("paths", nargs="*", help="Manuskript-Dateien oder Globs")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--ledger", metavar="JSON", help="Provenienz-Ledger (Datei) für den Markup-Abgleich")
    ap.add_argument("--git", action="store_true",
                    help="Ledger aus `ai:`-Commits ableiten (Trailer NOVA-Provenance: ghostwrite)")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    files: list[str] = []
    for p in args.paths:
        files.extend(sorted(glob.glob(p, recursive=True)))
    if not files:
        print("FEHLER: keine Dateien angegeben/gefunden.", file=sys.stderr)
        return 2

    total_spans, all_spans, total_errors = 0, [], 0
    full_text_parts: list[str] = []
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
            spans, errors = scan_text(content)
            full_text_parts.append(content)
        except OSError as e:
            print(f"  ✗ {path}: nicht lesbar ({e})")
            total_errors += 1
            continue
        for s in spans:
            print(f"  • {path}:{s['start_line']}-{s['end_line']} KI-Prosa "
                  f"(agent={s['agent']}, mode={s['mode']}, ts={s['ts']})")
        for e in errors:
            print(f"  ✗ {path}: {e}")
        all_spans.extend(spans)
        total_spans += len(spans)
        total_errors += len(errors)

    print(f"\n  {len(files)} Datei(en), {total_spans} markierte KI-Passage(n), {total_errors} Marker-Defekt(e).")

    # ── Ledger↔Markup-Abgleich (Phase 4) ────────────────────────────────────
    ledger_errors: list[str] = []
    entries: list[dict] = []
    if args.ledger:
        try:
            with open(args.ledger, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            entries = data.get("entries", data) if isinstance(data, (dict, list)) else []
            if isinstance(entries, dict):
                entries = entries.get("entries", [])
        except (OSError, json.JSONDecodeError) as e:
            print(f"  ✗ Ledger nicht lesbar/parsebar: {e}")
            return 1
    if args.git:
        entries = entries + git_ledger()
    if args.ledger or args.git:
        full_text = "\n".join(full_text_parts)
        ledger_errors = reconcile_ledger(full_text, all_spans, entries)
        acc = sum(1 for e in entries if e.get("status", "accepted") == "accepted")
        print(f"  Ledger: {len(entries)} Eintrag/Einträge ({acc} akzeptiert), {len(ledger_errors)} Verstoß/Verstöße.")
        for e in ledger_errors:
            print(f"  ✗ {e}")

    if total_errors or ledger_errors:
        print("  ⛔ EXPORT BLOCKIERT — Provenienz-Marker defekt/unbalanciert oder unmarkierte akzeptierte KI-Prosa.")
        return 1
    print("  ✅ Provenienz sauber: Marker balanciert" + (" + Ledger abgeglichen." if (args.ledger or args.git) else "."))
    return 0


def _selftest() -> int:
    print("Selftest 1: Marker-Balance")
    good = ("Mensch.\n<!-- NOVA:AI start agent=nova-ghostwrite mode=GHOSTWRITE ts=2026-06-13T09:00:00Z -->\n"
            "KI-Satz eins. KI-Satz zwei.\n<!-- NOVA:AI end -->\nMensch.")
    bad = ("<!-- NOVA:AI start agent=x mode=GHOSTWRITE -->\nKI ohne Ende.")
    gs, ge = scan_text(good)
    bs, be = scan_text(bad)
    print(f"  good: {len(gs)} span(s), {len(ge)} error(s) — erwartet 1/0")
    print(f"  bad:  {len(bs)} span(s), {len(be)} error(s) — erwartet 0/1")
    s1 = len(gs) == 1 and len(ge) == 0 and len(bs) == 0 and len(be) == 1
    text_ok = gs and "KI-Satz eins. KI-Satz zwei." in gs[0]["text"]
    print(f"  Spann-Text erfasst: {bool(text_ok)} — erwartet True")

    print("\nSelftest 2: Ledger↔Markup-Abgleich (Phase 4 / Rec.5)")
    ki_text = "KI-Satz eins. KI-Satz zwei."
    ledger = [{"agent": "nova-ghostwrite", "ts": "2026-06-13T09:00:00Z",
               "status": "accepted", "scene": "SCENE-001", "text": ki_text}]
    # (a) konsistent: dieselbe KI-Spanne markiert ⇒ 0 Verstöße
    cons_errs = reconcile_ledger(good, gs, ledger)
    # (b) NEGATIV: Markup entfernt, KI-Text aber im Manuskript geblieben ⇒ Block
    stripped = "Mensch.\n" + ki_text + "\nMensch."
    sspans, _ = scan_text(stripped)
    neg_errs = reconcile_ledger(stripped, sspans, ledger)
    # (c) verworfen, aber präsent ⇒ Block
    disc = [{"agent": "nova-ghostwrite", "ts": "x", "status": "discarded", "text": ki_text}]
    disc_errs = reconcile_ledger(stripped, sspans, disc)
    # (d) akzeptiert, aber vom Autor überschrieben (Text weg) ⇒ KEIN Block
    overwritten = "Mensch hat alles neu geschrieben."
    ow_spans, _ = scan_text(overwritten)
    ow_errs = reconcile_ledger(overwritten, ow_spans, ledger)
    print(f"  (a) konsistent markiert:           {len(cons_errs)} Verstoß/Verstöße — erwartet 0")
    print(f"  (b) Markup entfernt, Text bleibt:  {len(neg_errs)} Verstoß/Verstöße — erwartet 1 (BLOCK)")
    print(f"  (c) 'discarded', aber im Text:     {len(disc_errs)} Verstoß/Verstöße — erwartet 1 (BLOCK)")
    print(f"  (d) akzeptiert + überschrieben:    {len(ow_errs)} Verstoß/Verstöße — erwartet 0 (erlaubt)")
    s2 = (len(cons_errs) == 0 and len(neg_errs) == 1 and len(disc_errs) == 1 and len(ow_errs) == 0)

    passed = bool(s1 and text_ok and s2)
    print("\n" + ("OK" if passed else "FEHLGESCHLAGEN")
          + f": Balance={s1}, Text-Erfassung={bool(text_ok)}, Ledger-Reconcile={s2}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
