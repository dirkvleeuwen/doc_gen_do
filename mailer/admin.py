from django.contrib import admin
from .models import SentEmail

@admin.register(SentEmail)
class SentEmailAdmin(admin.ModelAdmin):
    list_display = ("subject", "to", "sent_at", "user")
    search_fields = ("subject", "to", "html_message")
    ordering = ("-sent_at",)