"""
Module: instruments/export_and_email_views.py
Beschrijving: Verwerkt exportfuncties voor instrument submissions, zoals CSV, PDF, DOCX, LaTeX en ZIP,
en verzorgt tevens de e-mailing van exportbestanden.
"""

import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.urls import reverse_lazy

# Import weasyprint voor PDF-generatie
from weasyprint import HTML

from instruments.models import InstrumentSubmission
from instruments.exports.generators import generate_export_file, generate_export_file_and_body
from instruments.exports.responses import serve_export_file, export_submission_zip_response
from mailer.utils import send_instrument_export_email
# Hergebruik de filteringlogica uit de list view
from instruments.views import InstrumentSubmissionListView


def export_submissions_csv(request):
    """
    Exporteer een CSV-bestand met een lijst van instrument submissions.
    """
    submissions_view = InstrumentSubmissionListView()
    submissions_view.request = request
    queryset = submissions_view.get_queryset()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="instrumenten.csv"'
    writer = csv.writer(response)
    writer.writerow(["Onderwerp", "Instrument", "Datum", "Laatst bewerkt", "Aantal indieners", "Indieners"])

    for submission in queryset:
        indieners = ", ".join(f"{s.initials} {s.lastname}" for s in submission.submitters.all())
        writer.writerow([
            submission.subject,
            submission.instrument,
            submission.date.strftime('%Y-%m-%d'),
            submission.updated_at.strftime('%Y-%m-%d %H:%M'),
            submission.submitters.count(),
            indieners
        ])
    return response


def export_submissions_pdf(request):
    """
    Exporteer een PDF-bestand met een lijst van instrument submissions.
    """
    submissions_view = InstrumentSubmissionListView()
    submissions_view.request = request
    queryset = submissions_view.get_queryset()

    html_string = render_to_string("instruments/pdf_list/export_pdf.html", {
        "submissions": queryset,
        "filters": request.GET,
    })

    pdf_file = HTML(string=html_string).write_pdf()

    response = HttpResponse(pdf_file, content_type="application/pdf")
    response["Content-Disposition"] = "attachment; filename=instrumenten.pdf"
    return response


def export_submission_pdf(request, pk):
    """
    Exporteer één instrument submission als PDF-bestand.
    """
    submission = get_object_or_404(InstrumentSubmission, pk=pk)
    filename, content, mimetype = generate_export_file(submission, "pdf")
    return serve_export_file(filename, content, mimetype)


def export_submission_docx(request, pk):
    """
    Exporteer één instrument submission als DOCX-bestand.
    """
    submission = get_object_or_404(InstrumentSubmission, pk=pk)
    filename, content, mimetype = generate_export_file(submission, "docx")
    return serve_export_file(filename, content, mimetype)


def export_submission_latex(request, pk):
    """
    Exporteer één instrument submission als LaTeX-bestand.
    """
    submission = get_object_or_404(InstrumentSubmission, pk=pk)
    filename, content, mimetype = generate_export_file(submission, "latex")
    return serve_export_file(filename, content, mimetype)


def export_submission_latex_source(request, pk):
    """
    Exporteer de LaTeX-broncode van één instrument submission.
    """
    submission = get_object_or_404(InstrumentSubmission, pk=pk)
    filename, content, mimetype = generate_export_file(submission, "latex_source")
    return serve_export_file(filename, content, mimetype)


def export_submission_zip(request, pk):
    """
    Exporteer een instrument submission met bijbehorende bestanden als ZIP-archief.
    """
    submission = get_object_or_404(InstrumentSubmission, pk=pk)
    return export_submission_zip_response(submission, pk)


def email_export(request, pk):
    """
    Genereer een exportbestand en verstuur dit via e-mail naar de huidige gebruiker.
    """
    export_type = request.POST.get("format")
    user = request.user
    submission = get_object_or_404(InstrumentSubmission, pk=pk)

    try:
        filename, attachment_content, mimetype, body = generate_export_file_and_body(submission, export_type)
    except Exception as e:
        messages.error(request, f"Fout bij exporteren: {e}")
        return redirect("instrument_submission_detail", pk=pk)

    send_instrument_export_email(
        user=user,
        submission=submission,
        export_type=export_type,
        attachment_filename=filename,
        attachment_content=attachment_content,
        attachment_mimetype=mimetype,
        body=body
    )

    messages.success(request, f"De e-mail is succesvol verstuurd naar {user.email}.")
    return redirect("instrument_submission_detail", pk=pk)