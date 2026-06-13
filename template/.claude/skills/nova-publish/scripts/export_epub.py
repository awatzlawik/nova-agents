#!/usr/bin/env python3
"""NOVA — EPUB-Export (Phase 4, DR-21).

Baut ein valides EPUB-3 aus dem Manuskript eines Autorprojekts. **stdlib-only**
(`zipfile` + handgeschriebenes OPF/NAV-XML) — KEINE externe Dependency (NOVA-Invariante;
JSZip/EbookLib der Vorbilder bewusst verworfen). EPUB-3-Layout nach NovelGenerator
`exportAsEpub` (mimetype · META-INF/container.xml · OEBPS/{content.opf, nav.xhtml, style.css,
chapter-NN.xhtml}); Metadaten nach BMAD-CW (Titel/Autor/Sprache/Klappentext).

Reihenfolge-Disziplin: dieses Skript FORMATIERT nur vorhandenen Text. Es ist **nicht** generativ
und schreibt nie ins Manuskript/Bible — Ausgabe ausschließlich nach `projects/<p>/export/`.
Das Pre-Export-Provenienz-Gate + die Continuity-Regression laufen VORHER (nova-publish *preflight).

NOVA:AI-Provenienz-Marker (HTML-Kommentar) werden im EXPORT entfernt (im Buch unsichtbar) —
erst nachdem das Gate beide Provenienz-Spuren verifiziert hat. Quell-Manuskript + ai:-Commits behalten sie.

Exit-Codes:  0 = EPUB erzeugt / Selftest grün      1 = Selftest fehlgeschlagen
             2 = Aufruf-/Pfadfehler (kein Manuskript etc.)
"""
from __future__ import annotations
import argparse
import glob
import json
import os
import re
import sys
import uuid
import zipfile
from datetime import datetime, timezone

MARKUP_RE = re.compile(r"<!--\s*NOVA:AI[^>]*-->[ \t]*\n?")
SCENE_BREAK_RE = re.compile(r"^\s*(\*\s*\*\s*\*|\*\*\*|---|—\s*—\s*—)\s*$")
LANG_MAP = {"deutsch": "de", "german": "de", "english": "en", "englisch": "en"}


# ── Markdown → XHTML (minimal, escaped) ──────────────────────────────────────

def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(s: str) -> str:
    s = _esc(s)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"_(.+?)_", r"<em>\1</em>", s)
    return s


def _strip_markup(md: str) -> str:
    """Entfernt die NOVA:AI-Provenienz-Marker (HTML-Kommentar) aus dem EXPORT-Artefakt."""
    return MARKUP_RE.sub("", md)


def _blocks_to_xhtml(body_md: str) -> str:
    """Absatz-/Überschrift-/Szenentrenner-Blöcke → XHTML."""
    out: list[str] = []
    block: list[str] = []

    def flush():
        if not block:
            return
        joined = " ".join(l.strip() for l in block).strip()
        if joined:
            out.append(f"<p>{_inline(joined)}</p>")
        block.clear()

    for raw in body_md.splitlines():
        line = raw.rstrip()
        if not line.strip():
            flush()
            continue
        if SCENE_BREAK_RE.match(line):
            flush()
            out.append('<hr class="scene-break"/>')
            continue
        if line.startswith("## "):
            flush()
            out.append(f"<h2>{_inline(line[3:].strip())}</h2>")
            continue
        block.append(line)
    flush()
    return "\n".join(out)


def _split_chapter(md: str, fallback_title: str):
    """Erste '# …'-Zeile = Kapitel-Titel; Rest = Body."""
    title, body_lines, found = fallback_title, [], False
    for ln in md.splitlines():
        if not found and ln.startswith("# "):
            title, found = ln[2:].strip(), True
            continue
        body_lines.append(ln)
    return title, _blocks_to_xhtml("\n".join(body_lines))


# ── Metadaten ────────────────────────────────────────────────────────────────

def _yaml_top_value(text: str, key: str):
    m = re.search(rf'(?m)^\s*{re.escape(key)}\s*:\s*"?([^"#\n]+?)"?\s*(?:#.*)?$', text)
    return m.group(1).strip() if m else None


def _load_metadata(project_dir: str, title: str | None, author: str | None):
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(project_dir)))
    lang, blurb, genre = "de", "", ""
    # config.yaml: Autor + Sprache (config-getrieben, Invariante 6)
    cfg = os.path.join(repo_root, "nova", "config.yaml")
    if os.path.isfile(cfg):
        with open(cfg, encoding="utf-8") as fh:
            ct = fh.read()
        if author is None:
            author = _yaml_top_value(ct, "author_name")
        dol = _yaml_top_value(ct, "document_output_language")
        if dol:
            lang = LANG_MAP.get(dol.strip().lower(), "de")
    # premise.json: Klappentext + Genre
    prem = os.path.join(project_dir, "_memory", "story-bible", "premise.json")
    if os.path.isfile(prem):
        try:
            with open(prem, encoding="utf-8") as fh:
                p = json.load(fh)
            blurb = p.get("logline") or p.get("premise_paragraph") or ""
            genre = (p.get("genre_audience") or {}).get("genre", "")
        except (OSError, json.JSONDecodeError):
            pass
    if not title:
        title = os.path.basename(os.path.abspath(project_dir)).replace("-", " ").strip().title()
    if not author:
        author = "Autor"
    return {"title": title, "author": author, "lang": lang, "blurb": blurb, "genre": genre}


# ── EPUB-Bau (stdlib zipfile) ─────────────────────────────────────────────────

def _container_xml() -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
            '  <rootfiles>\n'
            '    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n'
            '  </rootfiles>\n</container>\n')


def _content_opf(meta: dict, chapters: list[dict], book_uuid: str, modified: str) -> str:
    items = '\n'.join(f'    <item id="{c["id"]}" href="{c["href"]}" media-type="application/xhtml+xml"/>'
                      for c in chapters)
    spine = '\n'.join(f'    <itemref idref="{c["id"]}"/>' for c in chapters)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">\n'
            '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
            f'    <dc:identifier id="bookid">urn:uuid:{book_uuid}</dc:identifier>\n'
            f'    <dc:title>{_esc(meta["title"])}</dc:title>\n'
            f'    <dc:creator>{_esc(meta["author"])}</dc:creator>\n'
            f'    <dc:language>{meta["lang"]}</dc:language>\n'
            + (f'    <dc:description>{_esc(meta["blurb"])}</dc:description>\n' if meta["blurb"] else '')
            + (f'    <dc:subject>{_esc(meta["genre"])}</dc:subject>\n' if meta["genre"] else '')
            + f'    <meta property="dcterms:modified">{modified}</meta>\n'
            '  </metadata>\n'
            '  <manifest>\n'
            '    <item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>\n'
            '    <item id="css" href="style.css" media-type="text/css"/>\n'
            f'{items}\n'
            '  </manifest>\n'
            '  <spine>\n'
            f'{spine}\n'
            '  </spine>\n</package>\n')


def _nav_xhtml(meta: dict, chapters: list[dict]) -> str:
    lis = '\n'.join(f'      <li><a href="{c["href"]}">{_esc(c["title"])}</a></li>' for c in chapters)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" lang="{meta["lang"]}">\n'
            '<head><meta charset="utf-8"/><title>Inhalt</title></head>\n'
            '<body>\n'
            '  <nav epub:type="toc" id="toc">\n'
            '    <h1>Inhalt</h1>\n'
            f'    <ol>\n{lis}\n    </ol>\n'
            '  </nav>\n</body>\n</html>\n')


def _chapter_xhtml(meta: dict, title: str, body: str) -> str:
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE html>\n'
            f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{meta["lang"]}">\n'
            f'<head><meta charset="utf-8"/><title>{_esc(title)}</title>'
            '<link rel="stylesheet" type="text/css" href="style.css"/></head>\n'
            f'<body>\n  <section class="chapter">\n    <h1>{_esc(title)}</h1>\n{body}\n  </section>\n</body>\n</html>\n')


_CSS = ("@charset \"utf-8\";\n"
        "body { font-family: Georgia, 'Times New Roman', serif; line-height: 1.6; margin: 5%; }\n"
        "section.chapter { page-break-before: always; }\n"
        "h1 { text-align: center; margin: 2em 0 1.5em; font-weight: normal; }\n"
        "h2 { text-align: center; font-weight: normal; }\n"
        "p { text-align: justify; text-indent: 1.25em; margin: 0; }\n"
        "p:first-of-type, h1 + p, h2 + p, hr + p { text-indent: 0; }\n"
        "hr.scene-break { border: none; text-align: center; margin: 1.5em 0; }\n"
        "hr.scene-break::after { content: '* * *'; }\n")


def build_epub(project_dir: str, out_path: str, title: str | None = None, author: str | None = None) -> int:
    man_dir = os.path.join(project_dir, "manuscript")
    files = sorted(glob.glob(os.path.join(man_dir, "kapitel-*.md")))
    if not files:
        files = sorted(f for f in glob.glob(os.path.join(man_dir, "*.md")) if os.path.basename(f) != "README.md")
    if not files:
        print(f"FEHLER: kein Manuskript unter {man_dir}/ (kapitel-*.md).", file=sys.stderr)
        return 2

    meta = _load_metadata(project_dir, title, author)
    chapters = []
    for i, path in enumerate(files, 1):
        with open(path, encoding="utf-8") as fh:
            raw = fh.read()
        ch_title, body = _split_chapter(_strip_markup(raw), f"Kapitel {i}")
        chapters.append({"id": f"ch{i:02d}", "href": f"chapter-{i:02d}.xhtml", "title": ch_title, "body": body})

    book_uuid = str(uuid.uuid4())
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype MUSS erste Datei + unkomprimiert sein (EPUB-OCF-Spec).
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", _container_xml())
        zf.writestr("OEBPS/content.opf", _content_opf(meta, chapters, book_uuid, modified))
        zf.writestr("OEBPS/nav.xhtml", _nav_xhtml(meta, chapters))
        zf.writestr("OEBPS/style.css", _CSS)
        for c in chapters:
            zf.writestr(f"OEBPS/{c['href']}", _chapter_xhtml(meta, c["title"], c["body"]))

    print(f"  ✅ EPUB erzeugt: {out_path}")
    print(f"     Titel: {meta['title']} · Autor: {meta['author']} · Sprache: {meta['lang']} · {len(chapters)} Kapitel")
    if meta["blurb"]:
        print(f"     Klappentext: {meta['blurb'][:90]}{'…' if len(meta['blurb']) > 90 else ''}")
    return 0


def _slug(s: str) -> str:
    s = re.sub(r"[^\w\s-]", "", s.lower())
    return re.sub(r"[\s_-]+", "-", s).strip("-") or "buch"


def _selftest() -> int:
    import tempfile
    print("Selftest: EPUB-Bau + ZIP-Struktur + Markup-Strip")
    ok = True
    with tempfile.TemporaryDirectory() as td:
        man = os.path.join(td, "manuscript")
        os.makedirs(man)
        with open(os.path.join(man, "kapitel-01.md"), "w", encoding="utf-8") as fh:
            fh.write("# Kapitel 1 — Auftakt\n\nEin **Mensch**-Satz.\n\n"
                     "<!-- NOVA:AI start agent=nova-ghostwrite mode=GHOSTWRITE ts=2026-06-13T09:00:00Z -->\n"
                     "Eine markierte KI-Zeile.\n<!-- NOVA:AI end -->\n\n* * *\n\nNach dem Trenner.\n")
        with open(os.path.join(man, "kapitel-02.md"), "w", encoding="utf-8") as fh:
            fh.write("# Kapitel 2 — Wende\n\n## Eine Szene\n\nZweites Kapitel, *kursiv* getestet.\n")
        out = os.path.join(td, "export", "test.epub")
        rc = build_epub(td, out, title="Testbuch", author="Test-Autor")
        ok &= (rc == 0 and os.path.isfile(out))

        with zipfile.ZipFile(out) as zf:
            names = zf.namelist()
            info0 = zf.infolist()[0]
            first_ok = info0.filename == "mimetype" and info0.compress_type == zipfile.ZIP_STORED
            mime_ok = zf.read("mimetype").decode() == "application/epub+zip"
            struct_ok = all(n in names for n in
                            ["META-INF/container.xml", "OEBPS/content.opf", "OEBPS/nav.xhtml",
                             "OEBPS/style.css", "OEBPS/chapter-01.xhtml", "OEBPS/chapter-02.xhtml"])
            opf = zf.read("OEBPS/content.opf").decode()
            ch1 = zf.read("OEBPS/chapter-01.xhtml").decode()
            # XML wohlgeformt?
            import xml.dom.minidom as _x
            try:
                _x.parseString(zf.read("OEBPS/content.opf"))
                _x.parseString(zf.read("OEBPS/nav.xhtml"))
                _x.parseString(ch1.encode())
                xml_ok = True
            except Exception as e:  # noqa: BLE001
                xml_ok = False
                print(f"    XML-Parse-Fehler: {e}")
            markup_stripped = "NOVA:AI" not in ch1
            ki_text_kept = "Eine markierte KI-Zeile." in ch1
            meta_ok = "<dc:title>Testbuch</dc:title>" in opf and "<dc:creator>Test-Autor</dc:creator>" in opf

        print(f"  mimetype zuerst+stored: {first_ok} | inhalt: {mime_ok}")
        print(f"  Pflicht-Dateien vorhanden: {struct_ok}")
        print(f"  XML wohlgeformt: {xml_ok}")
        print(f"  Metadaten (Titel/Autor) gesetzt: {meta_ok}")
        print(f"  NOVA:AI-Markup entfernt: {markup_stripped} | KI-Text erhalten: {ki_text_kept}")
        ok &= first_ok and mime_ok and struct_ok and xml_ok and meta_ok and markup_stripped and ki_text_kept

    print("\n" + ("OK" if ok else "FEHLGESCHLAGEN"))
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description="NOVA EPUB-Export (Phase 4)")
    ap.add_argument("project", nargs="?", help="Projektpfad (projects/<p>)")
    ap.add_argument("--title", help="Buchtitel (Default: Projektname)")
    ap.add_argument("--author", help="Autor (Default: nova/config.yaml author_name)")
    ap.add_argument("--out", help="Ausgabepfad (Default: projects/<p>/export/<slug>.epub)")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()
    if not args.project:
        ap.error("Projektpfad fehlt (oder --selftest).")
    if not os.path.isdir(args.project):
        print(f"FEHLER: Projektpfad nicht gefunden: {args.project}", file=sys.stderr)
        return 2
    meta_title = args.title or os.path.basename(os.path.abspath(args.project)).replace("-", " ").title()
    out = args.out or os.path.join(args.project, "export", f"{_slug(meta_title)}.epub")
    return build_epub(args.project, out, title=args.title, author=args.author)


if __name__ == "__main__":
    raise SystemExit(main())
