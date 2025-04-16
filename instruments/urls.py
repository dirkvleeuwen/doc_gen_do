"""
Module: instruments/urls.py
Beschrijving: URL-configuratie voor de instruments app.
Routes voor export en e-mail functionaliteit worden nu afgehandeld door export_and_email_views.
"""

from django.urls import path
from . import views
from . import export_and_email_views

urlpatterns = [
    path("submissions/", views.InstrumentSubmissionListView.as_view(), name="instrument_submission_list"),
    path("submissions/new/", views.InstrumentSubmissionCreateView.as_view(), name="instrument_submission_create"),
    path("submissions/<int:pk>/", views.InstrumentSubmissionDetailView.as_view(), name="instrument_submission_detail"),
    path("submissions/edit/<int:pk>/", views.InstrumentSubmissionUpdateView.as_view(), name="instrument_submission_edit"),
    path("submissions/delete/<int:pk>/", views.InstrumentSubmissionDeleteView.as_view(), name="instrument_submission_delete"),
    path("submissions/export/", export_and_email_views.export_submissions_csv, name="instrument_submission_export"),
    path("submissions/export-pdf/", export_and_email_views.export_submissions_pdf, name="instrument_submission_export_pdf"),
    path("submissions/<int:pk>/download-preview/", export_and_email_views.export_submission_pdf, name="submission_preview_pdf"),
    path("notes/<int:pk>/edit/", views.NoteUpdateView.as_view(), name="note_edit"),
    path("notes/<int:pk>/delete/", views.NoteDeleteView.as_view(), name="note_delete"),
    path("submissions/<int:pk>/export-docx/", export_and_email_views.export_submission_docx, name="instrument_submission_export_docx"),
    path("submissions/<int:pk>/export-latex/", export_and_email_views.export_submission_latex, name="instrument_submission_export_latex"),
    path("submissions/<int:pk>/export-latex-source/", export_and_email_views.export_submission_latex_source, name="instrument_submission_export_latex_source"),
    path("submissions/<int:pk>/export-zip/", export_and_email_views.export_submission_zip, name="instrument_submission_export_zip"),
    path("submissions/<int:pk>/email-export/", export_and_email_views.email_export, name="instrument_email_export"),
]