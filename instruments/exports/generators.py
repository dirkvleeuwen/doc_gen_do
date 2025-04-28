# instruments/exports/generators.py

from pathlib import Path
import tempfile
import subprocess
import shutil
from django.template.loader import render_to_string
from docxtpl import DocxTemplate
from weasyprint import HTML
from instruments.exports.compose_text import process_gui_data
import logging
logger = logging.getLogger(__name__)


def generate_export_file(submission, export_type):
    table_data = [[s.initials, s.lastname, s.party] for s in submission.submitters.all()]
    data = process_gui_data(
        table_data=table_data,
        instrument=submission.instrument,
        subject=submission.subject,
        date_str=submission.date.isoformat(),
        considerations=submission.considerations,
        requests=submission.requests
    )

    if export_type == "pdf":
        html_string = render_to_string("instruments/previews/template.html", data)
        pdf_file = HTML(string=html_string).write_pdf()
        return "instrument.pdf", pdf_file, "application/pdf"

    elif export_type == "txt":
        txt_string = render_to_string("instruments/previews/template.txt", data)
        return "instrument.txt", txt_string.encode("utf-8"), "text/plain"

    elif export_type == "docx":
        instrument = submission.instrument
        template_map = {
            "Schriftelijke vragen": "Format_schriftelijkevragen_SDC.docx",
            "Mondelinge vragen": "Format_mondelingevragen_SDC.docx",
            "Agendapunt": "Format_agendapunt_SDC.docx",
            "Actualiteit": "Format_actualiteit_SDC.docx",
            "Motie": "Format_motie_SDC.docx",
        }
        if instrument not in template_map:
            raise ValueError(f"Geen .docx-template gevonden voor instrument: {instrument}")

        template_path = Path("instruments/templates/instruments/docx_templates") / template_map[instrument]
        doc = DocxTemplate(template_path)
        doc.render(data)

        with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
            doc.save(tmp.name)
            content = Path(tmp.name).read_bytes()
        return "instrument.docx", content, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    elif export_type == "latex_source":
        tex = render_to_string("instruments/previews/template.tex", data)
        return "instrument.tex", tex.encode("utf-8"), "application/x-tex"

    # elif export_type == "latex":
    #     tex_string = render_to_string("instruments/previews/template.tex", data)
    #     with tempfile.TemporaryDirectory() as tmpdir:
    #         tex_path = Path(tmpdir) / "instrument.tex"
    #         pdf_path = Path(tmpdir) / "instrument.pdf"
    #         tex_path.write_text(tex_string, encoding="utf-8")

    #         logo_src = Path("instruments/templates/instruments/previews/images/Logo-Gemeente-Amsterdam.png")
    #         shutil.copy(logo_src, Path(tmpdir) / logo_src.name)

    #         subprocess.run(
    #             ["pdflatex", "-interaction=nonstopmode", "-output-directory", tmpdir, str(tex_path)],
    #             check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    #         )
    #         content = pdf_path.read_bytes()
    #     return "instrument_latex.pdf", content, "application/pdf"
    
    elif export_type == "latex":
        tex_string = render_to_string("instruments/previews/template.tex", data)

        with tempfile.TemporaryDirectory() as tmpdir:
            tex_path = Path(tmpdir) / "instrument.tex"
            pdf_path = Path(tmpdir) / "instrument.pdf"

            tex_path.write_text(tex_string, encoding="utf-8")

            # logo mee kopiëren
            logo_src = Path(
                "instruments/templates/instruments/previews/images/Logo-Gemeente-Amsterdam.png"
            )
            shutil.copy(logo_src, Path(tmpdir) / logo_src.name)

            cmd = [
                "pdflatex",
                "-interaction=nonstopmode",
                "-file-line-error",        # duidelijkere foutregels
                "-output-directory", tmpdir,
                str(tex_path),
            ]

            # Meestal twee keer compileren i.v.m. referenties
            for i in range(2):
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    logger.error(
                        "LaTeX compile-fout (run %d):\n%s",
                        i + 1,
                        result.stdout + result.stderr,
                    )
                    # Geef een nette exceptie terug – wordt door Django afgevangen
                    raise RuntimeError("LaTeX compilatie mislukt, zie server-log voor details")

            content = pdf_path.read_bytes()

        return "instrument_latex.pdf", content, "application/pdf"

    else:
        raise ValueError(f"Onbekend exporttype: {export_type}")


def generate_export_file_and_body(submission, export_type):
    table_data = [[s.initials, s.lastname, s.party] for s in submission.submitters.all()]
    data = process_gui_data(
        table_data=table_data,
        instrument=submission.instrument,
        subject=submission.subject,
        date_str=submission.date.isoformat(),
        considerations=submission.considerations,
        requests=submission.requests,
    )

    body_template = "instruments/previews/template.txt" if export_type == "txt" else "instruments/previews/template.html"
    body = render_to_string(body_template, data)

    filename, content, mimetype = generate_export_file(submission, export_type)
    return filename, content, mimetype, body
