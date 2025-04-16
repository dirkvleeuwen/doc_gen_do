from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class Party(models.Model):
    name = models.CharField(max_length=100)
    
    class Meta:
        verbose_name_plural = "Parties"

    def __str__(self):
        return self.name

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Gebruikers moeten een e-mailadres opgeven")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_approved", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser moet is_staff=True zijn.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser moet is_superuser=True zijn.")
        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser moet is_active=True zijn.")
        if extra_fields.get("is_approved") is not True:
            raise ValueError("Superuser moet is_approved=True zijn.")

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    initials = models.CharField(_("initialen"), max_length=30)
    first_name = models.CharField(_("voornaam"), max_length=30, blank=True)
    last_name = models.CharField(_("achternaam"), max_length=150, blank=True)
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True)

    is_active = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["initials", "last_name", "party"]

    objects = CustomUserManager()

    class Meta:
        verbose_name = "User"

    def __str__(self):
        return f"{self.initials} {self.last_name}, {self.party} ({self.email})"
