"""
Module: instruments/views.py
Beschrijving: Bevat de views voor het beheren van instrument submissions en gerelateerde notities.
Nu wordt gecontroleerd of gebruikers alleen hun eigen submissions zien en kunnen bewerken.
Export- en e-mailfuncties zijn verplaatst naar export_and_email_views.py.
"""

import csv
from django.core.mail import EmailMessage
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.views.generic import CreateView, UpdateView, DetailView, DeleteView, ListView
from django.views.generic.edit import SingleObjectMixin
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, Http404
from django.contrib import messages

from instruments.models import InstrumentSubmission, Note
from instruments.forms import InstrumentSubmissionForm, SubmitterFormSet, NoteForm
from instruments.exports.compose_text import process_gui_data

# Definieer de e-mail export opties die je wilt aanbieden
EMAIL_OPTIONS = [
    {'fmt': 'pdf', 'icon': 'bi-file-earmark-pdf text-danger', 'label': '.pdf (van html)'},
    {'fmt': 'txt', 'icon': 'bi-filetype-txt text-secondary', 'label': 'platte tekst'},
    {'fmt': 'docx', 'icon': 'bi-file-earmark-word text-primary', 'label': '.docx'},
    {'fmt': 'latex', 'icon': 'bi-filetype-pdf text-dark', 'label': '.pdf (van LaTeX)'},
    {'fmt': 'latex_source', 'icon': 'bi-file-code text-dark', 'label': '. tex'},
    # Voeg eventueel andere formaten toe die je export_and_email_views ondersteunt
]
# Voeg dit toe bovenaan views.py, bij EMAIL_OPTIONS
DOWNLOAD_OPTIONS = [
    {'url_name': 'submission_preview_pdf', 'icon': 'bi-file-earmark-pdf text-danger', 'label': '.pdf (van html)'},
    {'url_name': 'instrument_submission_export_docx', 'icon': 'bi-file-earmark-word text-primary', 'label': '.docx'},
    {'url_name': 'instrument_submission_export_latex', 'icon': 'bi-filetype-pdf text-dark', 'label': '.pdf (van LaTeX)'},
    {'url_name': 'instrument_submission_export_latex_source', 'icon': 'bi-file-code text-dark', 'label': '.tex'},
    {'url_name': 'instrument_submission_export_zip', 'icon': 'bi-file-zip text-secondary', 'label': '.zip (alle bestanden)'},
    # Voeg hier andere downloadopties toe als je die hebt
]

class InstrumentSubmissionCreateView(CreateView):
    """
    View voor het aanmaken van een nieuwe instrument submission.
    Biedt een inline formset om meerdere indieners toe te voegen.
    De eigenaar (owner) wordt ingesteld op de ingelogde gebruiker.
    """
    model = InstrumentSubmission
    form_class = InstrumentSubmissionForm
    template_name = "instruments/submission_form.html"

    def get_context_data(self, **kwargs):
        # Voeg de submitter formset toe aan de context
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['submitter_formset'] = SubmitterFormSet(self.request.POST, instance=self.object)
        else:
            context['submitter_formset'] = SubmitterFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        # Stel de eigenaar van de submission in op de huidige gebruiker
        form.instance.owner = self.request.user
        context = self.get_context_data()
        submitter_formset = context['submitter_formset']
        if submitter_formset.is_valid() and form.is_valid():
            self.object = form.save()
            submitter_formset.instance = self.object
            submitter_formset.save()
            messages.success(self.request, "Instrument succesvol aangemaakt.")
            action = self.request.POST.get("submit_action", "save_return")
            if action == "save_stay":
                return redirect("instrument_submission_edit", pk=self.object.pk)
            return redirect("instrument_submission_detail", pk=self.object.pk)
        return self.form_invalid(form)


class InstrumentSubmissionUpdateView(UpdateView):
    """
    View voor het bijwerken van een bestaande instrument submission.
    Alleen de eigenaar mag zijn eigen submission bewerken.
    """
    model = InstrumentSubmission
    form_class = InstrumentSubmissionForm
    template_name = "instruments/submission_form.html"

    def get_queryset(self):
        # Zorg dat de gebruiker enkel zijn eigen submissions kan bewerken
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        # Voeg de submitter formset toe aan de context
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['submitter_formset'] = SubmitterFormSet(self.request.POST, instance=self.object)
        else:
            context['submitter_formset'] = SubmitterFormSet(instance=self.object)
        # Add notes and note form for the submission_form template
        context['notes'] = Note.objects.filter(submission=self.object).order_by('-created_at')
        context['note_form'] = NoteForm()
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        submitter_formset = context['submitter_formset']
        if submitter_formset.is_valid() and form.is_valid():
            self.object = form.save()
            submitter_formset.instance = self.object
            submitter_formset.save()
            messages.success(self.request, "Instrument succesvol bijgewerkt.")
            action = self.request.POST.get("submit_action", "save_return")
            if action == "save_stay":
                return redirect("instrument_submission_edit", pk=self.object.pk)
            return redirect("instrument_submission_detail", pk=self.object.pk)
        return self.form_invalid(form)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        # Detecteer AJAX-aanvraag voor notitie
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' and 'text' in request.POST:
            note_form = NoteForm(request.POST)
            if note_form.is_valid():
                note = note_form.save(commit=False)
                note.submission = self.object
                note.user = request.user
                note.save()
                # Render alleen de bijgewerkte lijst-notities
                notes = Note.objects.filter(submission=self.object).order_by('-created_at')
                html = render_to_string('instruments/partials/notes_list.html', {
                    'notes': notes,
                    'user': request.user
                }, request=request)
                return JsonResponse({'notes_html': html})
            return JsonResponse({'errors': note_form.errors}, status=400)
        # Valideer geen AJAX? Laat de standaard UpdateView doorlopen
        return super().post(request, *args, **kwargs)

class InstrumentSubmissionDeleteView(DeleteView):
    """
    View voor het verwijderen van een instrument submission.
    Alleen de eigenaar mag zijn eigen submission verwijderen.
    """
    model = InstrumentSubmission
    template_name = "instruments/submission_confirm_delete.html"
    success_url = reverse_lazy("instrument_submission_list")

    def get_queryset(self):
        # Zorg dat de gebruiker enkel zijn eigen submissions kan verwijderen
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


class InstrumentSubmissionListView(ListView):
    """
    View voor het tonen van een lijst met instrument submissions met filter- en sorteermogelijkheden.
    Alleen de submissions van de ingelogde gebruiker worden getoond.
    """
    model = InstrumentSubmission
    template_name = "instruments/submission_list.html"
    context_object_name = "submissions"
    paginate_by = 10

    def get_queryset(self):
        # Begin met alleen de submissions van de ingelogde gebruiker
        queryset = super().get_queryset().filter(owner=self.request.user).prefetch_related("submitters")
        q = self.request.GET.get("q", "").strip()
        if q:
            queryset = queryset.filter(
                Q(subject__icontains=q) |
                Q(submitters__lastname__icontains=q) |
                Q(submitters__initials__icontains=q) |
                Q(instrument__icontains=q)
            ).distinct()

        instrument_filter = self.request.GET.get("instrument", "")
        if instrument_filter:
            queryset = queryset.filter(instrument__iexact=instrument_filter)

        date_from = self.request.GET.get("date_from", "")
        date_to = self.request.GET.get("date_to", "")
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)

        sort = self.request.GET.get("sort")
        if sort:
            # Implementeer hier je sorteerlogica (bv. met een helper functie of direct)
            # Zorg ervoor dat de sorteervelden veilig zijn
            allowed_sort_fields = ['subject', 'instrument', 'date', 'updated_at']
            sort_field = sort.replace('_desc', '')
            direction = '-' if sort.endswith('_desc') else ''

            if sort_field in allowed_sort_fields:
                 queryset = queryset.order_by(f"{direction}{sort_field}")
            # else: negeer ongeldige sorteerparameter of gebruik default

        # Default sortering als er geen geldige sort is opgegeven
        elif not queryset.query.order_by:
             queryset = queryset.order_by('-updated_at') # Bijvoorbeeld default op laatst bewerkt

        return queryset

    def get_context_data(self, **kwargs):
        # Voeg extra contextinformatie toe
        context = super().get_context_data(**kwargs)
        context["request"] = self.request # Nodig voor url_replace tag

        # Haal unieke instrumentsoorten voor de filter dropdown
        context["instrument_choices"] = (
            InstrumentSubmission.objects.filter(owner=self.request.user)
            .order_by("instrument")
            .values_list("instrument", flat=True)
            .distinct()
        )

        context['email_export_options'] = EMAIL_OPTIONS
        context['download_export_options'] = DOWNLOAD_OPTIONS

        # context['submissions'] is een Paginator Page of lijst van submissions
        for submission in context['submissions']:
            table_data = [
                [s.initials, s.lastname, s.party]
                for s in submission.submitters.all()
            ]
            preview_data = process_gui_data(
                table_data=table_data,
                instrument=submission.instrument,
                subject=submission.subject,
                date_str=str(submission.date),
                considerations=submission.considerations,
                requests=submission.requests,
            )
            # render_to_string haalt hetzelfde template als in detailview
            submission.preview = render_to_string(
                "instruments/previews/template.txt",
                preview_data
            )

        return context


class InstrumentSubmissionDetailView(View):
    """
    Composiet view die zowel de weergave van een submission als het posten van notities behandelt.
    Ook hier zorgen we ervoor dat alleen de eigenaar de details kan zien.
    """
    def get(self, request, *args, **kwargs):
        # Gebruik de aangepaste queryset in de detail view
        view = SubmissionDisplayView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = SubmissionNotePostView.as_view()
        return view(request, *args, **kwargs)


class SubmissionDisplayView(DetailView):
    """
    View om de details van een instrument submission te tonen, inclusief een gegenereerde preview.
    Alleen toegankelijk voor de eigenaar.
    """
    model = InstrumentSubmission
    template_name = "instruments/submission_detail.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        submission = self.object
        # Bouw data op uit de submitters om een preview te genereren
        table_data = [[s.initials, s.lastname, s.party] for s in submission.submitters.all()]
        preview_data = process_gui_data(
            table_data=table_data,
            instrument=submission.instrument,
            subject=submission.subject,
            date_str=str(submission.date),
            considerations=submission.considerations,
            requests=submission.requests
        )
        context["preview"] = render_to_string("instruments/previews/template.txt", preview_data)
        context["preview_data"] = preview_data
        context["note_form"] = NoteForm()
        context["notes"] = submission.notes.order_by("-created_at")
        context['download_export_options'] = DOWNLOAD_OPTIONS
        context['email_export_options'] = EMAIL_OPTIONS
        return context


class SubmissionNotePostView(SingleObjectMixin, View):
    """
    View om een nieuwe notitie toe te voegen aan een instrument submission.
    """
    model = InstrumentSubmission

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = NoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.submission = self.object
            note.user = request.user
            note.save()
        return redirect("instrument_submission_detail", pk=self.object.pk)
    

class NoteUpdateView(UpdateView):
    """
    View voor het aanpassen van een notitie die gekoppeld is aan een instrument submission.
    Alleen de eigenaar van de notitie mag deze bewerken.
    """
    model = Note
    form_class = NoteForm
    template_name = "instruments/note_form.html"

    def get_success_url(self):
        return reverse_lazy("instrument_submission_detail", kwargs={"pk": self.object.submission.pk})

    def dispatch(self, request, *args, **kwargs):
        note = self.get_object()
        if note.user != request.user:
            return HttpResponseForbidden("Je mag alleen je eigen notities bewerken.")
        return super().dispatch(request, *args, **kwargs)


class NoteDeleteView(DeleteView):
    """
    View voor het verwijderen van een notitie.
    Alleen de eigenaar mag zijn notitie verwijderen.
    """
    model = Note
    template_name = "instruments/note_confirm_delete.html"

    def get_success_url(self):
        return reverse_lazy("instrument_submission_detail", kwargs={"pk": self.object.submission.pk})

    def dispatch(self, request, *args, **kwargs):
        note = self.get_object()
        if note.user != request.user:
            return HttpResponseForbidden("Je mag alleen je eigen notities verwijderen.")
        return super().dispatch(request, *args, **kwargs)
