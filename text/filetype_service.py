import os

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from docx import Document

from spot import SUPPORTED_EXTS, FILETYPES

def valid_filetype(file_path: str):
    file_path = file_path.strip().strip("{}").strip()

    if not file_path.lower().endswith(SUPPORTED_EXTS):
        return False
    if not os.path.exists(file_path):
        return False
    
    return True

def create_out_file_path(file_paths, new_out_dir:str, out_filetype: str):
    file_path = file_paths[0]
    out_dir = os.path.dirname(file_path)
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    if new_out_dir:
        out_dir = new_out_dir

    out_path = os.path.join(out_dir, base_name+out_filetype)

    return out_path
    
def to_txt(segments, output_file: str):
    with open(output_file, "w", encoding="utf-8") as f:
        for seg in segments:
            f.write(f"[{seg.start:.2f} -> {seg.end:.2f}] {seg.text}\n")


def to_pdf(segments, output_file: str):
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    import textwrap

    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter

    left = 40
    right = 40
    top = 40
    bottom = 40
    line_height = 14

    y = height - top
    max_chars = 95

    for seg in segments:
        line = f"[{seg.start:.2f} -> {seg.end:.2f}] {seg.text}"
        for wrapped in textwrap.wrap(line, width=max_chars):
            if y < bottom:
                c.showPage()
                y = height - top
            c.drawString(left, y, wrapped)
            y -= line_height

    c.save()


def to_docx(segments, output_file: str):

    doc = Document()
    for seg in segments:
        doc.add_paragraph(f"[{seg.start:.2f} -> {seg.end:.2f}] {seg.text}")
    doc.save(output_file)

def handle_filetype(filetype: str, segments: dict,  output_file: str):
    if filetype == FILETYPES[0]: #pdf
        to_pdf(segments, output_file)
    elif filetype == FILETYPES[1]: #docx
        to_docx(segments, output_file)
    elif filetype == FILETYPES[2]: #txt
        to_txt(segments, output_file)