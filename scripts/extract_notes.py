#!/usr/bin/env python3
"""
Extract .docx notes -> Astro markdown pages with images preserved.

Uses python-docx (not pandoc) so leading whitespace in code blocks survives.

For each .docx in leetcode-notes-tw/:
  1. Walk the document body element-by-element
  2. Paragraph: emit text (with heading level if styled as Heading N)
  3. Table:
       - 1×1 table that looks like code (contains def/class/import) -> ```python fence
       - otherwise -> markdown table
  4. Image (inline drawing in a run) -> copy to public/notes/<slug>/media/, emit ![](...)
"""
from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn

ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = ROOT / "leetcode-notes-tw"
OUT_PAGES = ROOT / "_extracted"
OUT_MEDIA = ROOT / "public" / "notes"

DOCS = {
    "cheatsheet.docx":          ("cheatsheet",        "Cheatsheet (核心模板)"),
    "Leetcode 高频.docx":       ("high-frequency",    "Leetcode 高频题"),
    "递归 Recursion.docx":      ("recursion",         "递归 Recursion"),
    "DP.docx":                  ("dp",                "Dynamic Programming"),
    "Leetcode.docx":            ("leetcode",          "Leetcode (主笔记)"),
    "面试笔记 & logs.docx":     ("interview-logs",    "面试笔记 & Logs"),
    "OOD.docx":                 ("ood",               "Object-Oriented Design"),
    "System Design.docx":       ("system-design",     "System Design"),
    "ML.docx":                  ("ml",                "Machine Learning Interview"),
    "SegTree.docx":             ("segment-tree",      "Segment Tree"),
}


# --------------------------------------------------------------------------- #
# Image extraction
# --------------------------------------------------------------------------- #

def collect_paragraph_images(p, doc, media_dir: Path, counter: dict) -> list[str]:
    """Find inline images in a paragraph; copy them to media_dir, return markdown refs."""
    refs = []
    drawings = p._element.findall(".//" + qn("w:drawing"))
    for drawing in drawings:
        blips = drawing.findall(".//" + qn("a:blip"))
        if not blips:
            continue
        for blip in blips:
            rel_id = blip.get(qn("r:embed")) or blip.get(qn("r:link"))
            if not rel_id:
                continue
            try:
                image_part = doc.part.related_parts[rel_id]
            except KeyError:
                continue
            counter["i"] += 1
            ext = Path(image_part.partname).suffix or ".png"
            out_name = f"image{counter['i']}{ext}"
            (media_dir / out_name).write_bytes(image_part.blob)
            refs.append(f"![](/notes/{media_dir.parent.name}/media/{out_name})")
    return refs


# --------------------------------------------------------------------------- #
# Paragraph rendering
# --------------------------------------------------------------------------- #

HEADING_RE = re.compile(r"Heading\s*(\d+)", re.IGNORECASE)
LIST_BULLET_STYLES = {"List Paragraph", "ListParagraph"}

def paragraph_to_md(p, doc, media_dir: Path, counter: dict) -> str:
    text = p.text
    style_name = (p.style.name or "") if p.style else ""

    # Image-only paragraphs: emit each image on its own line
    image_refs = collect_paragraph_images(p, doc, media_dir, counter)

    parts = []

    if image_refs:
        parts.extend(image_refs)

    if not text.strip():
        return "\n".join(parts)

    # Heading?
    m = HEADING_RE.search(style_name)
    if m:
        level = min(6, max(1, int(m.group(1))))
        parts.append(f"{'#' * level} {text.strip()}")
        return "\n".join(parts)

    # Bulleted list (heuristic: "List Paragraph" + leading dash/circle in text)
    # python-docx doesn't expose list markers cleanly without extra parsing; we
    # check the numbering format if present.
    numFmt = None
    pPr = p._element.find(qn("w:pPr"))
    if pPr is not None:
        numPr = pPr.find(qn("w:numPr"))
        if numPr is not None:
            ilvl = numPr.find(qn("w:ilvl"))
            level = int(ilvl.get(qn("w:val"))) if ilvl is not None else 0
            indent = "  " * level
            parts.append(f"{indent}- {text.strip()}")
            return "\n".join(parts)

    parts.append(text)
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Table rendering
# --------------------------------------------------------------------------- #

CODE_KEYWORDS_RE = re.compile(
    r"\b(def|class|return|self|import|from|lambda|None|True|False|while|for|"
    r"if |elif |else:|print\(|range\(|len\(|append|public|private|static|void|int |"
    r"function|var |let |const )\b"
)

def table_to_md(tbl, doc, media_dir: Path, counter: dict) -> str:
    rows = list(tbl.rows)
    n_rows = len(rows)
    n_cols = max((len(r.cells) for r in rows), default=0)

    # 1x1 "table" — almost always a code block in these notes
    if n_rows == 1 and n_cols == 1:
        cell_text = rows[0].cells[0].text
        # Also collect images from inside this cell.
        image_refs = []
        for p in rows[0].cells[0].paragraphs:
            image_refs.extend(collect_paragraph_images(p, doc, media_dir, counter))
        is_code = bool(CODE_KEYWORDS_RE.search(cell_text)) or "    " in cell_text
        if is_code and cell_text.strip():
            lang = "python" if re.search(r"\b(def|class|self|import|from|lambda|None|True|False)\b", cell_text) else ""
            block = f"```{lang}\n{cell_text}\n```"
            return ("\n".join(image_refs) + "\n\n" + block).strip() if image_refs else block
        # not code-looking — render as a quote-block so it reads as a callout
        if image_refs:
            return "\n".join(image_refs) + "\n\n" + cell_text.strip()
        return cell_text.strip()

    # Multi-row / multi-col — render as a markdown table
    md_rows = []
    for ri, row in enumerate(rows):
        cells = [_one_line(cell.text) for cell in row.cells]
        md_rows.append("| " + " | ".join(cells) + " |")
        if ri == 0:
            md_rows.append("| " + " | ".join(["---"] * n_cols) + " |")
    return "\n".join(md_rows)


def _one_line(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " <br> ").strip()


# --------------------------------------------------------------------------- #
# Document driver
# --------------------------------------------------------------------------- #

def doc_to_markdown(doc, slug: str, media_dir: Path) -> tuple[str, int]:
    out_blocks = []
    counter = {"i": 0}
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            from docx.text.paragraph import Paragraph
            p = Paragraph(child, doc.part)
            md = paragraph_to_md(p, doc, media_dir, counter)
            if md.strip() or md.startswith("!["):
                out_blocks.append(md)
        elif tag == "tbl":
            from docx.table import Table
            tbl = Table(child, doc.part)
            md = table_to_md(tbl, doc, media_dir, counter)
            if md.strip():
                out_blocks.append(md)
        elif tag == "sectPr":
            continue
        # Other tags (sectPr, etc.) ignored.

    return ("\n\n".join(out_blocks).strip() + "\n", counter["i"])


def process_one(docx_name: str) -> tuple[str, int, int]:
    info = DOCS.get(docx_name)
    if info is None:
        return (docx_name, 0, 0)
    slug, title = info
    docx_path = SRC_DIR / docx_name
    if not docx_path.exists():
        print(f"  ! missing: {docx_name}", file=sys.stderr)
        return (slug, 0, 0)

    media_dir = OUT_MEDIA / slug / "media"
    if media_dir.exists():
        shutil.rmtree(media_dir)
    media_dir.mkdir(parents=True, exist_ok=True)

    doc = Document(docx_path)
    body_md, n_images = doc_to_markdown(doc, slug, media_dir)

    frontmatter = (
        f"---\n"
        f"layout: ../../layouts/Layout.astro\n"
        f"title: {title}\n"
        f"---\n\n"
    )
    out_path = OUT_PAGES / f"{slug}.md"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(frontmatter + body_md, encoding="utf-8")

    return (slug, len(body_md.splitlines()), n_images)


def main(argv: list[str]) -> int:
    targets = argv[1:] if len(argv) > 1 else list(DOCS.keys())
    for name in targets:
        if name not in DOCS:
            print(f"  ? unknown doc: {name} (skipping)", file=sys.stderr)
            continue
        slug, lines, images = process_one(name)
        print(f"  {slug:18s} {lines:6d} lines, {images:4d} images")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
