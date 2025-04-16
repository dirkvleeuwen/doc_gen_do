"""
Module: instruments/admin.py
Beschrijving: Definieert de admin interface voor InstrumentSubmission, Submitter en Note.
"""

from django.contrib import admin
from django.forms.models import BaseInlineFormSet
from .models import InstrumentSubmission, Submitter, Note


class SubmitterInline(admin.TabularInline):
    """
    Inline admin view voor Submitter gekoppeld aan een instrument submission.
    """
    model = Submitter
    extra = 0


class NoteInlineFormSet(BaseInlineFormSet):
    """
    Formset voor de Note inline admin, zet de user automatisch op de huidige request.user.
    """
    def save_new(self, form, commit=True):
        obj = super().save_new(form, commit=False)
        obj.user = self.request.user  # Stel de gebruiker in op de huidige ingelogde user
        if commit:
            obj.save()
        return obj


class NoteInline(admin.TabularInline):
    """
    Inline admin view voor Note, enkel lezen van bepaalde velden.
    """
    model = Note
    extra = 0
    readonly_fields = ("user", "created_at")
    can_delete = False
    formset = NoteInlineFormSet

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.request = request
        return formset


@admin.register(InstrumentSubmission)
class InstrumentSubmissionAdmin(admin.ModelAdmin):
    """
    Admin interface voor InstrumentSubmission.
    """
    list_display = ("subject", "instrument", "date", "updated_at")
    search_fields = ("subject",)
    list_filter = ("instrument", "date")
    ordering = ("-updated_at",)
    inlines = [SubmitterInline, NoteInline]
    readonly_fields = ("timestamp", "updated_at")


@admin.register(Note)
class NoteAdmin(admin.ModelAdmin):
    """
    Admin interface voor Note.
    """
    list_display = ("submission", "user", "created_at")
    search_fields = ("text",)
    ordering = ("-created_at",)
    readonly_fields = ("created_at",)


@admin.register(Submitter)
class SubmitterAdmin(admin.ModelAdmin):
    """
    Admin interface voor Submitter.
    """
    list_display = ("initials", "lastname", "party", "submission")
    search_fields = ("initials", "lastname", "party")
    list_filter = ("party",)