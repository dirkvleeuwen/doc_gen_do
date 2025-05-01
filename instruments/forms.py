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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Bepaal instrument-type via instance of initial data
        instrument = None
        if hasattr(self.instance, 'instrument') and self.instance.instrument:
            instrument = self.instance.instrument
        elif 'instrument' in self.initial:
            instrument = self.initial['instrument']

        # Condioneel labels instellen per instrument
        if instrument == 'Mondelinge vragen':
            self.fields['instrument'].label = 'Instrument'
            self.fields['date'].label = 'Datum vergadering'
            self.fields['subject'].label = 'Onderwerp'
            self.fields['considerations'].label = 'Toelichting'
            self.fields['requests'].label = 'Vragen'
        elif instrument == 'Schriftelijke vragen':
            self.fields['instrument'].label = 'Instrument'
            self.fields['date'].label = 'Datum indiening'
            self.fields['subject'].label = 'Onderwerp'
            self.fields['considerations'].label = 'Toelichting'
            self.fields['requests'].label = 'Vragen'
        elif instrument == 'Agendapunt' or instrument == 'Actualiteit':
            self.fields['instrument'].label = 'Instrument'
            self.fields['date'].label = 'Datum'
            self.fields['subject'].label = 'Onderwerp'
            self.fields['considerations'].label = 'Toelichting'
            from django import forms  # ensure import is present at top if not already
            self.fields['requests'].widget = forms.HiddenInput()
            self.fields['requests'].label = ''
        elif instrument == 'Motie':
            self.fields['instrument'].label = 'Instrument'
            self.fields['date'].label = 'Datum vergadering'
            self.fields['subject'].label = 'Onderwerp'
            self.fields['considerations'].label = 'Overwegingen'
            self.fields['requests'].label = 'Verzoeken'
        else:
            # Standaard labels
            self.fields['instrument'].label = 'Instrument'
            self.fields['date'].label = 'Datum'
            self.fields['subject'].label = 'Onderwerp'
            self.fields['considerations'].label = 'Toelichting/overwegingen'
            self.fields['requests'].label = 'Vragen/verzoeken'

    class Media:
        js = ('instruments/js/instrument_form.js',)


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