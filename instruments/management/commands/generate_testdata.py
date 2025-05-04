# instruments/management/commands/generate_testdata.py
from datetime import timedelta, date
import random
from typing import List
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import Party
from instruments.models import InstrumentSubmission, Submitter, Note

# Instrument‑waarden die het systeem herkent
ALLOWED_INSTRUMENTS = [
    "Mondelinge vragen",
    "Schriftelijke vragen",
    "Motie",
    "Agendapunt",
    "Actualiteit",
]

# ----  REALISTIC FIXTURES (25 stuks) ----------------------------------
REALISTIC_FIXTURES: List[dict] = [
    {
        "instrument": "MOTIE",
        "subject": "Versnelling uitvoering Klimaatakkoord 2030",
        "considerations": (
            "overwegende dat de huidige CO₂‑reductie te langzaam verloopt om "
            "de doelen van Parijs te halen;"
        ),
        "requests": (
            "verzoekt de regering vóór 1 oktober 2025 met een uitgewerkt plan "
            "te komen voor een nationaal isolatieprogramma;"
        ),
        "submitters": [("S.", "Hermans"), ("L.", "Klaver")],
    },
    {
        "instrument": "MOTIE",
        "subject": "Invoering rookvrije generatie per 2035",
        "considerations": (
            "constaterende dat tabaksgebruik jaarlijks duizenden doden veroorzaakt;"
        ),
        "requests": (
            "verzoekt de regering in kaart te brengen welke wet‑ en regelgeving "
            "nodig is om verkoop van tabak in 2035 volledig te beëindigen;"
        ),
        "submitters": [("M.", "Kuiken"), ("P.", "Ouwehand")],
    },
    {
        "instrument": "KAMERVRAGEN",
        "subject": "Dreigende tekorten in de jeugdzorg",
        "considerations": "",
        "requests": (
            "Kan de minister aangeven welke maatregelen worden genomen om de "
            "wachttijden in de jeugdzorg terug te dringen?"
        ),
        "submitters": [("R.", "Heijink")],
    },
    {
        "instrument": "AMENDEMENT",
        "subject": "Wijziging wetsvoorstel Digitaliseringsfonds",
        "considerations": (
            "overwegende dat MKB‑ondernemers onvoldoende steun ervaren bij "
            "digitaliseringstrajecten;"
        ),
        "requests": (
            "stelt voor om artikel 3, lid 2 te vervangen door: "
            "'Het fonds reserveert jaarlijks ten minste € 200 mln voor MKB-begeleiding.'"
        ),
        "submitters": [("I.", "Van der Graaf")],
    },
    {
        "instrument": "MOTIE",
        "subject": "Verbod op nertsenfokkerijen per 1 januari 2026",
        "considerations": (
            "constaterende dat eerdere uitbraken van zoönosen grote risico’s vormen;"
        ),
        "requests": (
            "verzoekt de regering wetgeving voor te bereiden die nertsenfokkerijen "
            "per 2026 verbiedt en een vangnet voor getroffen ondernemers uitwerkt;"
        ),
        "submitters": [("F.", "Wassenberg"), ("T.", "Teunissen")],
    },
    {
        "instrument": "MOTIE",
        "subject": "Onderzoek naar gratis OV voor minima",
        "considerations": (
            "overwegende dat mobiliteit een randvoorwaarde is voor participatie op de arbeidsmarkt;"
        ),
        "requests": (
            "verzoekt de regering pilots met gratis regionaal OV voor minima te starten "
            "en voor zomer 2026 de effecten te evalueren;"
        ),
        "submitters": [("B.", "Alkaya")],
    },
    {
        "instrument": "KAMERVRAGEN",
        "subject": "Effecten van PFAS‑vervuiling op drinkwaterbronnen",
        "considerations": "",
        "requests": (
            "Welke acties onderneemt de minister om verdere PFAS‑lozingen te voorkomen?"
        ),
        "submitters": [("L.", "Moors")],
    },
    {
        "instrument": "AMENDEMENT",
        "subject": "Extra middelen voor lerarensalarissen",
        "considerations": (
            "constaterende dat het lerarentekort verder oploopt;"
        ),
        "requests": (
            "voegt aan begrotingsartikel 15 een extra bedrag van € 300 mln toe voor salarisstijging."
        ),
        "submitters": [("D.", "Westerveld")],
    },
    {
        "instrument": "MOTIE",
        "subject": "Aanpak woonfraude in de private huursector",
        "considerations": "",
        "requests": (
            "verzoekt de regering met gemeenten samen te werken aan een landelijk "
            "meldpunt woonfraude en middelen vrij te maken voor handhaving;"
        ),
        "submitters": [("H.", "Bikker")],
    },
    {
        "instrument": "MOTIE",
        "subject": "Nationaal actieplan biodiversiteit",
        "considerations": (
            "overwegende dat de soortenrijkdom in Nederland blijft afnemen;"
        ),
        "requests": (
            "verzoekt de regering uiterlijk Q1 2026 een actieplan biodiversiteit op te stellen "
            "met meetbare doelen en jaarlijks te rapporteren;"
        ),
        "submitters": [("T.", "Grinwis")],
    },
] + [
    {
        "instrument": random.choice(["MOTIE", "AMENDEMENT", "KAMERVRAGEN"]),
        "subject": f"Realistisch onderwerp {i}",
        "considerations": "constaterende dat ...;" if i % 2 == 0 else "",
        "requests": "verzoekt de regering ...;" if i % 3 != 0 else "",
        "submitters": [("A.", f"Naam{i}")],
    }
    for i in range(15)
]

# ----  HULPFUNCTIE ---------------------------------------------------------
def generate_testdata(
    n_submissions: int = 100,
    realistic: bool = False,
    verbosity: int = 1,
):
    """
    Genereer testdata voor InstrumentSubmission en bijbehorende modellen.

    Parameters
    ----------
    n_submissions : int
        Aantal InstrumentSubmission‑records om aan te maken.
    realistic : bool
        Wanneer True worden eerst de items uit REALISTIC_FIXTURES gebruikt.
    verbosity : int
        0 = stil, 1 = korte output, 2 = alle aangemaakte regels.
    """
    random.seed(42)

    # 1. Partijen
    party_names = [
        "VVD",
        "D66",
        "GroenLinks-PvdA",
        "NSC",
        "PVV",
        "SP",
        "CDA",
        "Partij voor de Dieren",
    ]
    parties = {
        name: Party.objects.get_or_create(name=name)[0] for name in party_names
    }

    # 2. Gebruikers / eigenaren
    User = get_user_model()
    owners = []
    status_cycle = [
        {"is_active": False, "is_approved": False},
        {"is_active": True,  "is_approved": False},
        {"is_active": True,  "is_approved": True},
    ]
    for i in range(10):
        email = f"realuser{i}@example.com"
        status = status_cycle[i % len(status_cycle)]
        party = random.choice(list(parties.values()))
        first = f"Real{i}"
        last = "User"
        initials_val = f"{first[0]}{last[0]}"
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first,
                "last_name": last,
                "password": "test1234!",
                "is_active": status["is_active"],
                "is_approved": status["is_approved"],
                "initials": initials_val,
                "party": party,
            },
        )
        if not created:
            user.is_active = status["is_active"]
            user.is_approved = status["is_approved"]
            user.party = party
            user.initials = initials_val
            user.save(update_fields=["is_active", "is_approved", "party", "initials"])
        owners.append(user)

    instrument_types = ALLOWED_INSTRUMENTS

    # 3. Fixture selectie
    fixtures_cycle = REALISTIC_FIXTURES[: n_submissions] if realistic else []

    created = 0
    for idx in range(n_submissions):
        if idx < len(fixtures_cycle):
            f = fixtures_cycle[idx]
            instrument = f["instrument"]
            instrument = {
                "MOTIE": "Motie",
                "KAMERVRAGEN": "Schriftelijke vragen",
                "AMENDEMENT": "Agendapunt",
            }.get(instrument, instrument)
            if instrument not in ALLOWED_INSTRUMENTS:
                instrument = "Agendapunt"
            subject = f["subject"]
            considerations = f["considerations"]
            requests = f["requests"]
            submitter_list = f["submitters"]
        else:
            instrument = instrument_types[idx % len(instrument_types)]
            subject = f"Testonderwerp {idx + 1}"
            considerations = (
                f"Overwegingen bij {subject}" if random.random() < 0.7 else ""
            )
            requests = (
                f"Verzoekt de regering {subject.lower()}"
                if random.random() < 0.7
                else ""
            )
            submitter_list = [
                (chr(65 + j), f"Achternaam_{idx}_{j}")
                for j in range(random.randint(1, 3))
            ]

        owner = random.choice(owners)
        subm_date = timezone.now().date() - timedelta(days=random.randint(1, 365))

        submission = InstrumentSubmission.objects.create(
            owner=owner,
            instrument=instrument,
            subject=subject,
            date=subm_date,
            considerations=considerations,
            requests=requests,
        )

        # Submitters
        for initials, lastname in submitter_list:
            party = random.choice(list(parties.values()))
            Submitter.objects.create(
                submission=submission,
                initials=initials,
                lastname=lastname,
                party=party.name,
            )

        # Notes
        for k in range(random.randint(0, 2)):
            Note.objects.create(
                submission=submission,
                user=owner,
                text=f"Opmerking {k + 1} bij {subject}",
            )

        created += 1
        if verbosity > 1:
            print(f"⤷  {submission}")

    if verbosity:
        mode = "realistisch" if realistic else "generiek"
        print(f"✅  {created} InstrumentSubmissions ({mode}) aangemaakt.")


# ----  MANAGEMENT‑COMMAND --------------------------------------------------
class Command(BaseCommand):
    help = "Genereer testdata: ≥100 InstrumentSubmissions + submitters + notes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=100,
            help="Aantal InstrumentSubmissions dat je wilt aanmaken (default 100).",
        )
        parser.add_argument(
            "--realistic",
            action="store_true",
            help="Gebruik realistische voorbeelden uit de fixtures.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        realistic = options["realistic"]
        verbosity = options.get("verbosity", 1)
        generate_testdata(count, realistic, verbosity)