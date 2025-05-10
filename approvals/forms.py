from django import forms
from .models import ApprovalRequest, ApprovalLog, ApprovalGroup
from django.utils.translation import gettext_lazy as _

class ApprovalRequestForm(forms.ModelForm):
    """Form for creating/updating approval requests"""
    
    class Meta:
        model = ApprovalRequest
        fields = ['required_groups', 'request_comment']
        widgets = {
            'required_groups': forms.CheckboxSelectMultiple(),
            'request_comment': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': 'Optionele toelichting bij dit goedkeuringsverzoek'
            })
        }
        labels = {
            'required_groups': _('Goedkeuringsgroepen'),
            'request_comment': _('Toelichting')
        }
        help_texts = {
            'required_groups': _('Selecteer welke groepen dit verzoek moeten goedkeuren'),
            'request_comment': _('Voeg eventueel een toelichting toe bij je goedkeuringsverzoek')
        }
    
    def clean_required_groups(self):
        required_groups = self.cleaned_data.get('required_groups')
        if not required_groups or required_groups.count() == 0:
            raise forms.ValidationError(_('Selecteer ten minste één goedkeuringsgroep.'))
        return required_groups

class ApprovalReviewForm(forms.ModelForm):
    """Form for reviewing approval requests"""
    
    class Meta:
        model = ApprovalRequest
        fields = ['status', 'review_comment']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'review_comment': forms.Textarea(attrs={
                'rows': 3, 
                'class': 'form-control',
                'placeholder': 'Opmerkingen bij je beoordeling'
            })
        }
        labels = {
            'status': _('Status'),
            'review_comment': _('Opmerkingen')
        }
        help_texts = {
            'review_comment': _('Voeg een toelichting toe bij je beoordeling (verplicht bij afwijzing)')
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        review_comment = cleaned_data.get('review_comment')
        
        if status == 'rejected' and not review_comment:
            raise forms.ValidationError(_('Een toelichting is verplicht bij het afwijzen van een verzoek.'))
        
        return cleaned_data

class ReviewForm(forms.Form):
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 4,
            'class': 'form-control',
            'placeholder': 'Opmerkingen bij je beoordeling'
        }),
        required=False,
        label=_('Opmerkingen'),
        help_text=_('Optionele opmerkingen bij de beoordeling (verplicht bij afwijzing)')
    )