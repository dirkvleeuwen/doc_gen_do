"""
Module: instruments/apps.py
Beschrijving: Configuratie van de instruments app.
"""

from django.apps import AppConfig


class InstrumentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'instruments'