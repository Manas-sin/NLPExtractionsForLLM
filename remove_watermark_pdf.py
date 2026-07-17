#!/usr/bin/env python3
"""
NCERT Watermark Remover — PDF-level, lossless.

Removes the "not to be republished" / "© NCERT" watermark by deleting the
watermark image XObjects from the PDF itself, BEFORE any rendering.

Why not the pixel approach (remove_watermark.py):
    The old script masks light-cyan pixels in HSV and inpaints. That is actively
    DANGEROUS for physics, where cyan (#00AEEF) IS the content colour — section
    headers, example boxes, the Points to Ponder box, and most diagrams are cyan.
    Inpainting them destroys the page.

    It also can't work in principle: the watermark is NOT cyan. It is a 1-bit
    ImageMask stencil painted in BLACK at 10% alpha (measured: fill=(0,0,0),
    alpha_fill=0.1). It renders as grey, not cyan.

How this works instead:
    The watermark ships as two image XObjects present on EVERY page:
        2480 x 3508  — full-page diagonal "not to be republished"
        1894 x 1894  — square "© NCERT" stamp
    Verified identical across all 10 physics PDFs AND chemistry (lech101).

    Each page holds its own copy (xrefs differ per page), so detection is by
    DIMENSIONS + "appears on every page", not by xref.

    Deleting them is lossless: text, vectors, colours and geometry are untouched.
    Measured on keph101 p5: text 2798 -> 2798 chars, watermark gone.

Usage:
    python remove_watermark_pdf.py keph101.pdf                 # -> keph101_clean.pdf
    python remove_watermark_pdf.py keph101.pdf -o out.pdf
    python remove_watermark_pdf.py uploads/ --batch            # whole folder
    python remove_watermark_pdf.py keph101.pdf --dry-run       # report only
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("PyMuPDF required:  pip install pymupdf")


# Known NCERT watermark stencil dimensions (width, height), measured from source.
KNOWN_WATERMARK_DIMS = {
    (2480, 3508),  # full-page diagonal "not to be republished"
    (1894, 1894),  # square "© NCERT" stamp
}

# Text boilerplate. NOTE: on physics PDFs the watermark is an IMAGE, so these
# strings do NOT appear in get_text(). Kept because chemistry PDFs do embed some
# of it as text. Never rely on these alone.
TEXT_BOILERPLATE = [
    r"not\s+to\s+be\s+republished",
    r"©\s*NCERT",
    r"Reprint\s+\d{4}-\d{2}",
]


def find_watermark_dims(doc: fitz.Document, strict: bool = True) -> set[tuple[int, int]]:
    """
    Identify watermark images.

    Heuristic: an image appearing on EVERY page is boilerplate, not content.
    Real figures never appear on all pages.

    strict=True  -> only accept dims that are also in KNOWN_WATERMARK_DIMS.
                    Safer: won't nuke a legitimate recurring logo.
    strict=False -> accept any image present on every page.
    """
    counts: Counter = Counter()
    for page in doc:
        # set() so an image placed twice on one page still counts once
        for dims in {(im[2], im[3]) for im in page.get_images()}:
            counts[dims] += 1

    n = doc.page_count
    every_page = {d for d, c in counts.items() if c == n}

    if strict:
        return every_page & KNOWN_WATERMARK_DIMS
    return every_page


def remove_watermark(
    src: Path,
    dst: Path | None = None,
    strict: bool = True,
    dry_run: bool = False,
) -> dict:
    """
    Delete watermark images from a PDF. Returns a report dict.

    Lossless: only image XObjects are dropped. Text/vectors are never touched.
    """
    doc = fitz.open(src)
    dims = find_watermark_dims(doc, strict=strict)

    report = {
        "file": src.name,
        "pages": doc.page_count,
        "watermark_dims": sorted(dims),
        "placements_removed": 0,
        "text_before": 0,
        "text_after": 0,
        "text_preserved": True,
        "output": None,
    }

    if not dims:
        report["note"] = "no watermark detected"
        doc.close()
        return report

    report["text_before"] = sum(len(p.get_text()) for p in doc)

    if dry_run:
        report["placements_removed"] = sum(
            1 for p in doc for im in p.get_images() if (im[2], im[3]) in dims
        )
        report["note"] = "dry run — nothing written"
        doc.close()
        return report

    removed = 0
    for page in doc:
        for im in page.get_images():
            if (im[2], im[3]) in dims:
                try:
                    page.delete_image(im[0])
                    removed += 1
                except Exception as e:  # noqa: BLE001
                    print(f"  warn: could not delete xref {im[0]} on p{page.number + 1}: {e}")
    report["placements_removed"] = removed

    if dst is None:
        dst = src.with_name(f"{src.stem}_clean.pdf")

    # garbage=4 drops the now-orphaned image objects; deflate re-compresses.
    #
    # Do NOT add clean=True. It rewrites content streams and silently mutates
    # text — measured: keph101 p7 "Reprint 2026-27" -> "Reprint 2026-2" (-1 char),
    # and up to -5 chars on keph106. garbage+deflate alone is fully lossless
    # across all 11 source PDFs.
    doc.save(dst, garbage=4, deflate=True)
    doc.close()

    # Verify text survived — this is the safety check that the pixel approach
    # can never make.
    after = fitz.open(dst)
    report["text_after"] = sum(len(p.get_text()) for p in after)
    after.close()
    report["text_preserved"] = report["text_after"] == report["text_before"]
    report["output"] = str(dst)

    return report


def main() -> int:
    ap = argparse.ArgumentParser(description="Remove NCERT watermarks losslessly at PDF level.")
    ap.add_argument("path", help="PDF file, or folder with --batch")
    ap.add_argument("-o", "--output", help="output PDF (single-file mode)")
    ap.add_argument("--batch", action="store_true", help="process every PDF in a folder")
    ap.add_argument("--outdir", help="output folder for --batch (default: alongside source)")
    ap.add_argument("--dry-run", action="store_true", help="report only, write nothing")
    ap.add_argument(
        "--loose",
        action="store_true",
        help="accept ANY image present on every page (default: only known NCERT dims)",
    )
    args = ap.parse_args()

    src = Path(args.path)
    strict = not args.loose

    if args.batch:
        if not src.is_dir():
            return _err(f"{src} is not a folder")
        pdfs = sorted(p for p in src.glob("*.pdf") if not p.stem.endswith("_clean"))
        if not pdfs:
            return _err(f"no PDFs in {src}")

        outdir = Path(args.outdir) if args.outdir else None
        if outdir:
            outdir.mkdir(parents=True, exist_ok=True)

        print(f"{'file':<14}{'pages':>6}{'removed':>9}{'text':>16}  status")
        ok = True
        for p in pdfs:
            dst = (outdir / f"{p.stem}_clean.pdf") if outdir else None
            r = remove_watermark(p, dst, strict=strict, dry_run=args.dry_run)
            status = _status(r)
            ok &= r["text_preserved"]
            text_col = f"{r['text_before']}→{r['text_after']}"
            print(
                f"{r['file']:<14}{r['pages']:>6}{r['placements_removed']:>9}"
                f"{text_col:>16}  {status}"
            )
        return 0 if ok else 1

    if not src.exists():
        return _err(f"{src} not found")

    dst = Path(args.output) if args.output else None
    r = remove_watermark(src, dst, strict=strict, dry_run=args.dry_run)

    print(f"file:        {r['file']}")
    print(f"pages:       {r['pages']}")
    print(f"watermark:   {r['watermark_dims'] or 'none detected'}")
    print(f"removed:     {r['placements_removed']} placements")
    if not args.dry_run and r["watermark_dims"]:
        print(f"text:        {r['text_before']} → {r['text_after']} chars")
        print(f"lossless:    {'YES' if r['text_preserved'] else 'NO — TEXT CHANGED, INVESTIGATE'}")
        print(f"output:      {r['output']}")
    if r.get("note"):
        print(f"note:        {r['note']}")

    return 0 if r["text_preserved"] else 1


def _status(r: dict) -> str:
    if not r["watermark_dims"]:
        return "no watermark"
    if not r["text_preserved"]:
        return "TEXT CHANGED — investigate"
    return "clean"


def _err(msg: str) -> int:
    print(f"error: {msg}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
