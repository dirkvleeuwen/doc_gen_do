# instruments/exports/responses.py

from django.http import HttpResponse, Http404
from pathlib import Path
from io import BytesIO
import zipfile
from instruments.exports.generators import generate_export_file


def serve_export_file(filename, content, mimetype):
    response = HttpResponse(content, content_type=mimetype)
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def export_submission_zip_response(submission, pk):
    zip_buffer = BytesIO()

    export_types = [
        ("pdf", f"instrument_{pk}_html.pdf"),
        ("latex_source", f"instrument_{pk}.tex"),
        ("latex", f"instrument_{pk}_latex.pdf"),
        ("docx", f"instrument_{pk}.docx"),
    ]

    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for export_type, zip_filename in export_types:
            try:
                _, content, _mimetype = generate_export_file(submission, export_type)
                zip_file.writestr(zip_filename, content)
            except Exception as e:
                zip_file.writestr(f"{export_type}_error.txt", str(e))

        # Logo toevoegen
        logo_path = Path("instruments/templates/instruments/previews/images/Logo-Gemeente-Amsterdam.png")
        if logo_path.exists():
            with open(logo_path, "rb") as logo_file:
                zip_file.writestr("Logo-Gemeente-Amsterdam.png", logo_file.read())
        else:
            zip_file.writestr("logo_error.txt", "Logo bestand niet gevonden.")

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type="application/zip")
    response["Content-Disposition"] = f'attachment; filename="instrument_{pk}_export.zip"'
    return response
