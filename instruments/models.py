"""
Module: instruments/models.py
Beschrijving: Definieert de modellen voor instrument submissions, inclusief de indieners (Submitter)
en notities (Note). Nu wordt elke InstrumentSubmission gekoppeld aan een eigenaar (user).
"""

from django.db import models
from django.conf import settings

class InstrumentSubmission(models.Model):
    """
    Model voor een instrument submission.
    Naast informatie over het instrument, onderwerp, datums en indieners,
    wordt er nu ook een eigenaar (owner) bijgehouden om te bepalen
    welke gebruiker de submission aangemaakt heeft.
    """
    # Eigendom (owner) van de submission
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="instrument_submissions"
    )
    
    # Keuzelijst voor instrumenttypen
    INSTRUMENT_CHOICES = [
        ("Mondelinge vragen", "Mondelinge vragen"),
        ("Schriftelijke vragen", "Schriftelijke vragen"),
        ("Motie", "Motie"),
        ("Agendapunt", "Agendapunt"),
        ("Actualiteit", "Actualiteit"),
    ]
    
    instrument = models.CharField(
        max_length=50,
        choices=INSTRUMENT_CHOICES,
        default="Mondelinge vragen"
    )
    subject = models.CharField(max_length=200)
    date = models.DateField()
    considerations = models.TextField(blank=True)
    requests = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.instrument} - {self.subject} ({self.date})"


class Submitter(models.Model):
    """
    Model voor een indiener (submitter) die gekoppeld is aan een instrument submission.
    """
    submission = models.ForeignKey(
        InstrumentSubmission,
        on_delete=models.CASCADE,
        related_name="submitters"
    )
    initials = models.CharField(max_length=10)
    lastname = models.CharField(max_length=100)
    party = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.initials} {self.lastname} ({self.party})"


class Note(models.Model):
    """
    Model voor een notitie die gekoppeld is aan een instrument submission.
    """
    submission = models.ForeignKey(
        InstrumentSubmission,
        on_delete=models.CASCADE,
        related_name="notes"
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Notitie door {self.user} op {self.created_at.date()}"


class InstrumentVersion(models.Model):
    """
    Model voor het opslaan van een versie van een instrument submission op het moment van goedkeuringsaanvraag.
    Dit zorgt ervoor dat we altijd kunnen zien welke versie van het instrument is beoordeeld.
    """
    submission = models.ForeignKey(
        InstrumentSubmission,
        on_delete=models.CASCADE,
        related_name="versions"
    )
    instrument = models.CharField(max_length=50)
    subject = models.CharField(max_length=200)
    date = models.DateField()
    considerations = models.TextField(blank=True)
    requests = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # JSON field voor het opslaan van de indieners op het moment van versioning
    submitters_data = models.JSONField(default=list)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Versie van {self.instrument} - {self.subject} ({self.created_at})"

    @classmethod
    def create_from_submission(cls, submission):
        """
        Maak een nieuwe versie op basis van een InstrumentSubmission
        """
        submitters_data = [
            {
                'initials': s.initials,
                'lastname': s.lastname,
                'party': s.party
            }
            for s in submission.submitters.all()
        ]

        return cls.objects.create(
            submission=submission,
            instrument=submission.instrument,
            subject=submission.subject,
            date=submission.date,
            considerations=submission.considerations,
            requests=submission.requests,
            submitters_data=submitters_data
        )