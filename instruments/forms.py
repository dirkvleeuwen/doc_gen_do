"""
Module: instruments/forms.py
Beschrijving: Bevat formulieren voor instrument submissions, indieners en notities.
"""

from django import forms
from django.forms import inlineformset_factory
from .models import InstrumentSubmission, Submitter, Note


class InstrumentSubmissionForm(forms.ModelForm):
    """
    Formulier voor het aanmaken/bijwerken van een instrument submission.
    Omvat velden als instrument, subject, datum, considerations en requests.
    """
    class Meta:
        model = InstrumentSubmission
        fields = ["instrument", "subject", "date", "considerations", "requests"]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }


# Inline formset om meerdere Submitters tegelijk toe te voegen
SubmitterFormSet = inlineformset_factory(
    parent_model=InstrumentSubmission,
    model=Submitter,
    fields=["initials", "lastname", "party"],
    extra=0,         # Toont 0 lege indieners per keer
    can_delete=True  # Hiermee kan een indiener worden verwijderd
)


class NoteForm(forms.ModelForm):
    """
    Formulier voor het toevoegen of aanpassen van een notitie.
    """
    class Meta:
        model = Note
        fields = ["text"]
        widgets = {
            "text": forms.Textarea(attrs={"rows": 3, "placeholder": "Voeg hier je notitie toe…"}),
        }