from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Party
from django.utils.translation import gettext_lazy as _

@admin.register(Party)
class PartyAdmin(admin.ModelAdmin):
    list_display = ("name",)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ("email", "initials", "last_name", "is_active", "is_approved", "party")
    list_filter = ("is_active", "is_approved", "party")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Persoonlijk"), {"fields": ("initials", "first_name", "last_name", "party")}),
        (_("Status"), {"fields": ("is_active", "is_approved", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Belangrijk"), {"fields": ("last_login",)}),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "initials", "password1", "password2", "party", "is_staff", "is_active", "is_approved"),
        }),
    )
    search_fields = ("email", "initials", "last_name")
    ordering = ("email", "last_name",)
