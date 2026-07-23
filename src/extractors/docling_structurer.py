"""Docling-based NCERT structurer.

Uses Docling's ML layout model to detect sections, tables, and figures (which the
regex structurer cannot do reliably), then maps the result into the same JSON schema
the preview UI already consumes. NCERT PDFs draw heading text twice, so a dedup pass
cleans the doubled strings Docling returns.

Figures: Docling's layout model crops each captioned figure cleanly. For any figure
number that has a caption in the text but no matching Docling picture, we fall back to
the caption-anchored cropper in ``figure_extractor``.
"""

import json
import re
from pathlib import Path

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions

from .figure_extractor import extract_figures

_SUBJECT_BY_PREFIX = {"lech": "chemistry", "keph": "physics", "kebo": "biology", "kemh": "maths"}

# NCERT chapter titles live in a stylised banner *image*, so they are not reliable
# text. NCERT is a fixed corpus, so we resolve the title from a known map first.
KNOWN_TITLES = {
    # Chemistry Class 12 Part 1
    "lech101": "Solutions",
    "lech102": "Electrochemistry",
    "lech103": "Chemical Kinetics",
    "lech104": "The d- and f-Block Elements",
    "lech105": "Coordination Compounds",
    # Physics Class 11 Part 1
    "keph101": "Units and Measurement",
    "keph102": "Motion in a Straight Line",
    "keph103": "Motion in a Plane",
    "keph104": "Laws of Motion",
    "keph105": "Work, Energy and Power",
    "keph106": "System of Particles and Rotational Motion",
    "keph107": "Gravitation",
    # Biology Class 11
    "kebo101": "The Living World",
    "kebo102": "Biological Classification",
    "kebo103": "Plant Kingdom",
    "kebo104": "Animal Kingdom",
    "kebo105": "Morphology of Flowering Plants",
    "kebo106": "Anatomy of Flowering Plants",
    "kebo107": "Structural Organisation in Animals",
    "kebo108": "Cell: The Unit of Life",
    "kebo109": "Biomolecules",
    "kebo110": "Cell Cycle and Cell Division",
    "kebo111": "Photosynthesis in Higher Plants",
    "kebo112": "Respiration in Plants",
    "kebo113": "Plant Growth and Development",
    "kebo114": "Breathing and Exchange of Gases",
    "kebo115": "Body Fluids and Circulation",
    "kebo116": "Excretory Products and their Elimination",
    "kebo117": "Locomotion and Movement",
    "kebo118": "Neural Control and Coordination",
    "kebo119": "Chemical Coordination and Integration",
}


def dedupe_doubled(text: str) -> str:
    """Collapse NCERT's doubled heading text, e.g.
    '1 . 1 1 . 1 Types of Types of Solutions Solutions' -> '1.1 Types of Solutions'."""
    t = re.sub(r"\s+", " ", text).strip()
    # Join spaced section numbers first: '1 . 1' -> '1.1'
    t = re.sub(r"(\d)\s*\.\s*(\d)", r"\1.\2", t)
    words = t.split()

    n = len(words)
    if n >= 2 and n % 2 == 0 and words[: n // 2] == words[n // 2:]:
        return " ".join(words[: n // 2])

    # Drop consecutive duplicate words (case-insensitive)
    collapsed = []
    for w in words:
        if collapsed and collapsed[-1].lower() == w.lower():
            continue
        collapsed.append(w)

    # Collapse interleaved duplicate bigrams: A B A B -> A B (case-insensitive)
    def eq(a, b):
        return a.lower() == b.lower()

    res = []
    i = 0
    while i < len(collapsed):
        if i + 3 < len(collapsed) and eq(collapsed[i], collapsed[i + 2]) and eq(collapsed[i + 1], collapsed[i + 3]):
            res.extend([collapsed[i], collapsed[i + 1]])
            i += 4
        elif i + 2 < len(collapsed) and eq(collapsed[i], collapsed[i + 2]) and collapsed[i].lower() not in ("of", "a", "the", "in", "and"):
            res.append(collapsed[i])
            i += 2
        else:
            res.append(collapsed[i])
            i += 1
    return " ".join(res)


def _page(item) -> int:
    """Source page number (1-based) for a Docling item, or 0 if unknown."""
    prov = getattr(item, "prov", None)
    if prov:
        try:
            return int(prov[0].page_no)
        except (AttributeError, IndexError, ValueError, TypeError):
            return 0
    return 0


def _run_docling(pdf_path: Path):
    opts = PdfPipelineOptions()
    opts.do_ocr = False                    # NCERT is text-based; skip OCR (7min -> ~11s)
    opts.generate_picture_images = True
    opts.images_scale = 2.0
    conv = DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)}
    )
    return conv.convert(str(pdf_path)).document


def _label(item) -> str:
    lab = getattr(item, "label", "")
    return getattr(lab, "value", lab) or ""


def _text(item) -> str:
    return (getattr(item, "text", "") or "").strip()


class DoclingStructurer:
    """Structure an NCERT chapter with Docling and emit the preview JSON schema."""

    def __init__(self, book_code: str, pdf_path: Path, base_dir: Path = None):
        self.book_code = book_code
        self.pdf_path = Path(pdf_path)
        self.base_dir = base_dir or Path("data/extracted") / book_code
        self.subject = _SUBJECT_BY_PREFIX.get(book_code[:4].lower(), "unknown")
        self.chapter_num = self._chapter_number()

    def _chapter_number(self) -> int:
        try:
            return int(self.book_code[-2:])
        except ValueError:
            return 1

    def structure(self) -> dict:
        doc = _run_docling(self.pdf_path)
        ordered = list(doc.iterate_items())

        result = {
            "book_code": self.book_code,
            "subject": self.subject,
            "class": 11 if self.book_code[4] == "1" else 12,
            "unit_number": self.chapter_num,
            "unit_title": self._chapter_title(ordered),
            "qr_code": "",
            "objectives": self._objectives(ordered),
            "hook_quote": "",
            "introduction": self._introduction(ordered),
            "sections": self._sections(ordered),
            "key_terms": [],
            "laws_principles": [],
            "equations": [],
            "tables": self._tables(doc),
            "figures": self._figures(doc),
            "examples": self._examples(ordered),
            "intext_questions": self._intext(ordered),
            "summary": self._summary(ordered),
            "exercises": self._exercises(ordered),
            "answers": {},
        }
        result["page_index"] = self._page_index(result)
        result["statistics"] = self._stats(result)
        result["_engine"] = "docling"
        return result

    def _page_index(self, result: dict) -> list:
        """Group every extracted element by the page it came from.

        Produces: [{"page": N, "elements": [{"type","ref","label"}, ...]}, ...]
        so the JSON itself shows, page by page, exactly what was extracted.
        """
        by_page = {}

        def add(page, etype, ref, label):
            page = int(page or 0)
            if page <= 0:
                return
            by_page.setdefault(page, []).append({"type": etype, "ref": str(ref), "label": label[:80]})

        for s in result["sections"]:
            add(s.get("page"), "section", s["number"], s["title"])
        for ex in result["examples"]:
            add(ex.get("page"), "example", ex["number"], (ex.get("problem") or "")[:80])
        for q in result["intext_questions"]:
            add(q.get("page"), "intext_question", q["number"], (q.get("text") or "")[:80])
        for t in result["tables"]:
            add(t.get("page"), "table", t.get("number") or "?", t.get("title", ""))
        for f in result["figures"]:
            add(f.get("page"), "figure", f["number"], f.get("caption", ""))
        for x in result["exercises"]:
            add(x.get("page"), "exercise", x["number"], (x.get("text") or "")[:80])

        return [{"page": p, "elements": by_page[p]} for p in sorted(by_page)]

    # --- helpers over the ordered item stream ---

    def _chapter_title(self, ordered) -> str:
        # 1) Known NCERT title (most reliable — title is a banner image, not text).
        if self.book_code in KNOWN_TITLES:
            return KNOWN_TITLES[self.book_code]

        # 2) Reuse the regex structurer's title if it found a real one.
        regex_file = self.base_dir / "final_output.regex.json"
        if regex_file.exists():
            try:
                t = json.loads(regex_file.read_text()).get("unit_title", "")
                if t and t.lower() not in ("unknown", self.book_code.lower()):
                    return t
            except (ValueError, OSError):
                pass

        # 3) Fallback: first real section header that isn't a labelled block.
        skip = ("example", "objective", "intext", "summary", "table", "fig", "answer", "solution")
        for item, _ in ordered:
            if _label(item) in ("title", "section_header"):
                txt = dedupe_doubled(_text(item))
                low = txt.lower()
                if txt and not re.match(r"^\d", txt) and not any(low.startswith(s) for s in skip):
                    return txt
        return self.book_code

    def _objectives(self, ordered) -> list:
        objectives, capturing = [], False
        for item, _ in ordered:
            lab = _label(item)
            if lab == "section_header":
                header = dedupe_doubled(_text(item)).lower()
                if header.startswith("objective"):
                    capturing = True
                    continue
                if capturing:
                    break
            elif capturing and lab == "list_item":
                obj = re.sub(r"\s+", " ", _text(item)).strip(" ;.")
                if len(obj) > 8:
                    objectives.append(obj)
        return objectives

    def _introduction(self, ordered) -> str:
        """Capture the opening prose that appears before the first numbered section
        (unit intro + chapter intro). These paragraphs are otherwise dropped because
        no section is 'current' yet."""
        paras = []
        for item, _ in ordered:
            lab = _label(item)
            txt = re.sub(r"\s+", " ", _text(item)).strip()
            if lab == "section_header" and re.match(rf"^{self.chapter_num}\.\d+(?!\d)\s", txt):
                break  # reached the first real section
            # Substantial prose only — skips TOC entries, banners, short labels.
            if lab == "text" and len(txt) > 60:
                paras.append(txt)
        return "\n\n".join(paras)[:4000]

    def _regex_section_titles(self) -> dict:
        """Section number -> title from the regex structurer output, if available.
        Used to name section headers Docling mislabels or drops."""
        regex_file = self.base_dir / "final_output.regex.json"
        titles = {}
        if regex_file.exists():
            try:
                for s in json.loads(regex_file.read_text()).get("sections", []):
                    if s.get("number") and s.get("title"):
                        titles[s["number"]] = s["title"]
            except (ValueError, OSError):
                pass
        return titles

    def _sections(self, ordered) -> list:
        sections = []
        by_number = {}
        current = None
        regex_titles = self._regex_section_titles()

        def ensure_section(number, title, page):
            sec = by_number.get(number)
            if sec is None:
                sec = {
                    "number": number, "title": title or regex_titles.get(number, ""),
                    "page": page, "content": "", "content_truncated": False,
                    "subsections": [], "examples": [],
                }
                by_number[number] = sec
                sections.append(sec)
            elif title and not sec["title"]:
                sec["title"] = title
            return sec

        for item, _ in ordered:
            lab = _label(item)
            if lab == "section_header":
                title = dedupe_doubled(_text(item))
                m = re.match(r"^(\d+\.\d+)(?!\.\d)\s+(.*)", title)
                sub = re.match(r"^(\d+\.\d+)\.\d+\s+(.*)", title)
                if m and int(m.group(1).split(".")[0]) == self.chapter_num:
                    # Prefer the regex structurer's cleaner title when available.
                    clean = regex_titles.get(m.group(1)) or m.group(2).strip()
                    current = ensure_section(m.group(1), clean, _page(item))
                elif sub and int(sub.group(1).split(".")[0]) == self.chapter_num:
                    # Subsection: attach to its parent, creating the parent if Docling
                    # dropped it (e.g. section 1.6). Parent title comes from regex output.
                    parent_num = sub.group(1)
                    parent = ensure_section(parent_num, regex_titles.get(parent_num, ""), _page(item))
                    full = re.match(r"^(\d+\.\d+\.\d+)\s+(.*)", title)
                    if full:
                        parent["subsections"].append({"number": full.group(1), "title": full.group(2).strip()})
                    current = parent
            elif lab in ("text", "list_item") and current is not None:
                body = _text(item)
                if body:
                    current["content"] = (current["content"] + " " + body).strip()[:3000]

        sections.sort(key=lambda s: [int(p) for p in s["number"].split(".")])
        return sections

    def _examples(self, ordered) -> list:
        """Detect examples from headers AND text items (Docling tags only some as
        section headers), keyed by number so each example is captured once."""
        examples, by_num, cur = [], {}, None
        for item, _ in ordered:
            lab = _label(item)
            body = re.sub(r"\s+", " ", dedupe_doubled(_text(item))).strip()
            start = re.match(r"^Example\s+(\d+\.\d+)\s*(.*)", body, re.IGNORECASE)
            if start:
                num = start.group(1)
                cur = by_num.get(num)
                if cur is None:
                    cur = {"number": num, "problem": "", "solution": "", "page": _page(item)}
                    by_num[num] = cur
                    examples.append(cur)
                rest = start.group(2).strip()
                if rest:
                    cur["problem"] = rest[:1000]
                continue
            if cur is not None and lab in ("text", "list_item"):
                if not body:
                    continue
                # A new section header ends the current example
                if lab == "section_header":
                    cur = None
                    continue
                if re.match(r"^(Solution|Answer)\b", body, re.IGNORECASE) or cur["problem"]:
                    cur["solution"] = (cur["solution"] + " " + body).strip()[:2000]
                else:
                    cur["problem"] = (cur["problem"] + " " + body).strip()[:1000]
            elif lab == "section_header" and not start:
                cur = None
        examples.sort(key=lambda e: [int(p) for p in e["number"].split(".")])
        return examples

    def _intext(self, ordered) -> list:
        questions, capturing = [], False
        for item, _ in ordered:
            lab = _label(item)
            if lab == "section_header":
                header = dedupe_doubled(_text(item)).lower()
                capturing = header.startswith("intext")
                continue
            if capturing and lab in ("list_item", "text"):
                body = re.sub(r"\s+", " ", _text(item)).strip()
                m = re.match(r"^(\d+\.\d+)\s+(.*)", body)
                if m:
                    questions.append({"number": m.group(1), "text": m.group(2).strip()[:300], "page": _page(item)})
        return questions

    def _summary(self, ordered) -> list:
        points, capturing = [], False
        for item, _ in ordered:
            lab = _label(item)
            if lab == "section_header":
                header = dedupe_doubled(_text(item)).lower()
                if header.startswith("summary"):
                    capturing = True
                    continue
                if capturing:
                    break
            elif capturing and lab in ("text", "list_item"):
                pt = re.sub(r"\s+", " ", _text(item)).strip()
                if len(pt) > 20:
                    points.append(pt[:400])
        return points

    def _exercises(self, ordered) -> list:
        """Exercises are the numbered questions after the Summary section.

        Chemistry/physics number them 'X.Y'; biology uses plain integers '1.', '2.'.
        """
        exercises, after_summary, seen = [], False, set()
        if self.subject == "biology":
            # Docling strips the "1." list markers, so take substantial list items
            # after the EXERCISES header and number them sequentially.
            for item, _ in ordered:
                lab = _label(item)
                if lab == "section_header" and dedupe_doubled(_text(item)).lower().startswith("exercise"):
                    after_summary = True
                elif after_summary and lab == "list_item":
                    body = re.sub(r"\s+", " ", _text(item)).strip()
                    # Skip sub-parts "(a)/(i)" and short fragments
                    if re.match(r"^\([a-z0-9ivx]+\)", body) or len(body) < 25:
                        continue
                    exercises.append({"number": str(len(exercises) + 1), "text": body[:1000], "sub_parts": [], "page": _page(item)})
            return exercises

        pat = re.compile(r"^(\d+\.\d+)\s+(.+)")
        for item, _ in ordered:
            lab = _label(item)
            if lab == "section_header":
                header = dedupe_doubled(_text(item)).lower()
                if header.startswith("summary") or header.startswith("exercise"):
                    after_summary = True
            elif after_summary and lab in ("list_item", "text"):
                body = re.sub(r"\s+", " ", _text(item)).strip()
                m = pat.match(body)
                if m and m.group(1) not in seen and len(m.group(2)) > 15:
                    seen.add(m.group(1))
                    exercises.append({"number": m.group(1), "text": m.group(2).strip()[:1000], "sub_parts": [], "page": _page(item)})
        return exercises

    def _tables(self, doc) -> list:
        tables = []
        for tbl in doc.tables:
            caption = ""
            try:
                caption = dedupe_doubled(tbl.caption_text(doc) or "")
            except Exception:
                pass
            num_match = re.search(r"Table\s+(\d+\.\d+)", caption)
            try:
                df = tbl.export_to_dataframe(doc)
            except Exception:
                try:
                    df = tbl.export_to_dataframe()
                except Exception:
                    continue

            # Make headers unique so duplicate-named columns don't collide.
            raw_headers = [str(c) for c in df.columns]
            headers, seen = [], {}
            for h in raw_headers:
                if h in seen:
                    seen[h] += 1
                    headers.append(f"{h} ({seen[h]})")
                else:
                    seen[h] = 1
                    headers.append(h)

            # Positional cell access avoids pandas returning a Series on dup columns.
            rows = []
            for record in df.itertuples(index=False, name=None):
                rows.append({headers[i]: str(v) for i, v in enumerate(record) if i < len(headers)})

            # Skip noise: small blocks with no real caption and index-only headers
            # (0,1,2...) are option-lists Docling misread as tables.
            numeric_headers = all(re.fullmatch(r"\d+", h) for h in raw_headers)
            if not num_match and numeric_headers:
                continue

            if headers:
                tables.append({
                    "number": num_match.group(1) if num_match else "",
                    "title": re.sub(r"\s+", " ", caption).strip()[:150] or "Table",
                    "headers": headers, "rows": rows, "row_count": len(rows),
                    "page": _page(tbl),
                })
        return tables

    def _figures(self, doc) -> list:
        """Save Docling's clean captioned figure crops; fill gaps with the
        caption-anchored cropper without clobbering Docling's better crops."""
        import shutil

        fig_dir = self.base_dir / "figures"
        fig_dir.mkdir(parents=True, exist_ok=True)
        figures, fig_map = [], {}
        captions, pages = {}, {}

        for pic in doc.pictures:
            caption = ""
            try:
                caption = pic.caption_text(doc) or ""
            except Exception:
                pass
            m = re.search(r"Fig(?:ure)?\.?\s*(\d+\.\d+)", caption)
            if not m or m.group(1) in fig_map:
                continue
            num = m.group(1)
            img = pic.get_image(doc)
            if img is None or img.width < 60 or img.height < 40:
                continue
            fname = f"fig_{num.replace('.', '_')}.png"
            img.save(fig_dir / fname)
            fig_map[num] = fname
            captions[num] = re.sub(r"\s+", " ", caption).strip()[:200]
            pages[num] = _page(pic)

        # Fallback for figure numbers Docling missed: crop into a temp dir, then copy
        # only the missing ones so Docling's clean crops are never overwritten.
        try:
            tmp = self.base_dir / "_figures_fallback"
            fb = extract_figures(self.pdf_path, tmp)
            for num, fname in fb.items():
                if num not in fig_map:
                    shutil.copy(tmp / fname, fig_dir / fname)
                    fig_map[num] = fname
                    captions[num] = ""
            if tmp.exists():
                shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass

        for num, fname in fig_map.items():
            figures.append({"number": num, "caption": captions.get(num, ""), "page": pages.get(num, 0)})
        (self.base_dir / "figures_map.json").write_text(json.dumps(fig_map, indent=2))
        figures.sort(key=lambda f: [int(p) for p in f["number"].split(".")])
        return figures

    def _stats(self, result: dict) -> dict:
        return {
            "section_count": len(result["sections"]),
            "objective_count": len(result["objectives"]),
            "key_term_count": 0,
            "law_count": 0,
            "equation_count": 0,
            "table_count": len(result["tables"]),
            "figure_count": len(result["figures"]),
            "example_count": len(result["examples"]),
            "intext_question_count": len(result["intext_questions"]),
            "exercise_count": len(result["exercises"]),
            "summary_point_count": len(result["summary"]),
        }

    def save(self, output_file: Path = None) -> Path:
        result = self.structure()
        output_file = output_file or self.base_dir / "final_output.json"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2))
        return output_file


def structure_chapter_docling(book_code: str, pdf_path: Path, base_dir: Path = None) -> dict:
    structurer = DoclingStructurer(book_code, pdf_path, base_dir)
    out = structurer.save()
    print(f"Structured (docling): {out}")
    return structurer.structure()
