"""Convert PDFs to markdown sidecars (one `## Page N` section per page) so qmd can index them.

Usage: .venv/bin/python pdf_to_markdown.py <dir_output> <pdf> [<pdf> ...]

Uses the PDF's embedded text layer via PyMuPDF. Skips PDFs whose sidecar is newer than the PDF.

epsilon's copy of the Mac's ~/.local/share/qmd-pdf/pdf_to_markdown.py, minus OCR: the Mac OCRs
pages without a text layer with PaddleOCR-VL on MLX, which needs Metal. Here those pages are left
out, and counted in the output. The sidecars the Mac already wrote (with OCR) are copied over once,
see README.md → qmd.
"""

import sys
from pathlib import Path

import pymupdf

CNT_CHARS_MIN_TEXT_LAYER = 50


def convert(path_pdf: Path, dir_output: Path) -> None:
    path_output = dir_output / f"{path_pdf.stem}.md"
    if path_output.exists() and path_output.stat().st_mtime > path_pdf.stat().st_mtime:
        print(f"skip (up to date): {path_pdf.name}")
        return

    # Use the text layer; leave out pages whose text layer is missing or nearly empty
    sections = []
    cnt_pages_without_text = 0
    with pymupdf.open(path_pdf) as document:
        for idx, page in enumerate(document):
            # Dehyphenate so words split across line breaks still match keyword search
            text = page.get_text(flags=pymupdf.TEXTFLAGS_TEXT | pymupdf.TEXT_DEHYPHENATE)
            is_text_layer_usable = len("".join(text.split())) >= CNT_CHARS_MIN_TEXT_LAYER
            if not is_text_layer_usable:
                cnt_pages_without_text += 1
                continue
            sections.append(f"## Page {idx + 1}\n\n{text.strip()}\n")

    # Frontmatter points back to the source PDF; page headings let search hits be cited by page
    header = f"---\nsource_pdf: \"{path_pdf}\"\n---\n\n# {path_pdf.stem}\n\n"
    path_output.write_text(header + "\n".join(sections), encoding="utf-8")
    print(f"wrote: {path_output.name} ({len(sections)} pages, {cnt_pages_without_text} left out without a text layer)", flush=True)


if __name__ == "__main__":
    assert len(sys.argv) >= 3, __doc__
    dir_output = Path(sys.argv[1])
    dir_output.mkdir(parents=True, exist_ok=True)
    for arg in sys.argv[2:]:
        convert(Path(arg).resolve(), dir_output)
