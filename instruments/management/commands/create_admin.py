"""
Management command to create the initial superuser with custom fields (initials,
party and approval flag). You can supply values via command‑line options or
environment variables.

Environment variables that will be used if no options are passed:
    ADMIN_EMAIL
    ADMIN_PASSWORD
    ADMIN_INITIALEN
    ADMIN_ACHTERNAAM
    ADMIN_PARTY

Gebruik dit commando om een superuser aan te maken met de volgende command line:
python manage.py create_admin \
    --email admin@doc-gen.eu \
    --password 'sterkwachtwoord' \
    --initials 'D.J.' \
    --last-name 'van Leeuwen' \
    --party 'Admin Party'
"""

import os
from django.core.management.base import BaseCommand
from dotenv import load_dotenv
from accounts.models import CustomUser, Party


class Command(BaseCommand):
    help = "Creates an initial superuser with initials, party and approval flag."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            default=os.environ.get("ADMIN_EMAIL", "admin@example.com"),
            help="E‑mail for the new superuser (or set ADMIN_EMAIL env var).",
        )
        parser.add_argument(
            "--password",
            default=os.environ.get("ADMIN_PASSWORD", "admin"),
            help="Password for the superuser (or set ADMIN_PASSWORD env var).",
        )
        parser.add_argument(
            "--initials",
            default=os.environ.get("ADMIN_INITIALEN", "A.B."),
            help="Initials (or set ADMIN_INITIALEN env var).",
        )
        parser.add_argument(
            "--last-name",
            dest="last_name",
            default=os.environ.get("ADMIN_ACHTERNAAM", "Admin"),
            help="Last name (or set ADMIN_ACHTERNAAM env var).",
        )
        parser.add_argument(
            "--party",
            default=os.environ.get("ADMIN_PARTY", "Admin Party"),
            help="Party name for the user (or set ADMIN_PARTY env var).",
        )

    def handle(self, *args, **options):
        # Pick up .env variables for local runs
        load_dotenv()

        email = options["email"]
        password = options["password"]
        initials = options["initials"]
        last_name = options["last_name"]
        party_name = options["party"]

        if CustomUser.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f"User with email '{email}' already exists.")
            )
            return

        party_obj, _ = Party.objects.get_or_create(name=party_name)

        user = CustomUser(
            email=email,
            initials=initials,
            last_name=last_name,
            is_staff=True,
            is_superuser=True,
            is_active=True,
            is_approved=True,
            party=party_obj,
        )
        user.set_password(password)
        user.full_clean()
        user.save()

        self.stdout.write(
            self.style.SUCCESS(f"Superuser '{email}' created successfully!")
        )
