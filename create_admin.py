# create_admin.py
import os
import sys
import django
from pathlib import Path
from dotenv import load_dotenv

# --- CONFIGURATIE (Pas deze waarden aan!) ---
ADMIN_EMAIL = 'admin@doc-gen.eu'
ADMIN_PASSWORD = 'ZjonG4J2!' # Kies een sterk, uniek wachtwoord!
ADMIN_INITIALEN = 'D.J.'
ADMIN_ACHTERNAAM = 'van Leeuwen'
ADMIN_PARTY_ID = 1  # Het ID van de Party die je wilt koppelen (bv. 'Admin Party')
# --- EINDE CONFIGURATIE ---

def setup_django():
    """Zet de Django omgeving op zodat we modellen kunnen gebruiken."""
    # Voeg de project root directory toe aan het Python pad
    # BASE_DIR is de map waar manage.py staat (/home/ubuntu/instrument_generator)
    BASE_DIR = Path(__file__).resolve().parent
    sys.path.append(str(BASE_DIR))

    # Laad .env bestand *voordat* settings worden geladen
    dotenv_path = BASE_DIR / '.env'
    if dotenv_path.exists():
        print(f"Loading environment variables from: {dotenv_path}")
        load_dotenv(dotenv_path=dotenv_path)
    else:
        print(f"Warning: .env file not found at {dotenv_path}. Environment variables might be missing.")
        # Probeer zonder .env verder te gaan (systemd Environment= moet dan werken)
        # Als dat niet werkt, stop hier:
        # raise FileNotFoundError(f".env file not found at {dotenv_path}")


    # Stel de settings module in
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'instrument_generator.settings')

    # Setup Django
    try:
        django.setup()
        print("Django setup successful.")
    except Exception as e:
        print(f"Error during django.setup(): {e}")
        sys.exit(1)


def create_admin_user():
    """Maakt de admin gebruiker aan op een manier die werkt met custom fields."""
    # Importeer modellen *na* django.setup()
    try:
        from accounts.models import CustomUser, Party
        print("Models imported successfully.")
    except Exception as e:
         print(f"Error importing models: {e}")
         sys.exit(1)


    # Controleer of gebruiker al bestaat
    if CustomUser.objects.filter(email=ADMIN_EMAIL).exists():
        print(f"User with email {ADMIN_EMAIL} already exists.")
        return

    # Haal het Party object op
    try:
        party_object = Party.objects.get(pk=ADMIN_PARTY_ID)
        print(f"Found party: {party_object.name} (ID: {party_object.pk})")
    except Party.DoesNotExist:
        print(f"ERROR: Party with ID {ADMIN_PARTY_ID} not found in the database.")
        print("Please create the party first or correct ADMIN_PARTY_ID.")
        return
    except Exception as e:
        print(f"Error fetching party: {e}")
        return

    # Maak de gebruiker aan en stel velden daarna in
    try:
        print(f"Attempting to create superuser: {ADMIN_EMAIL}")
        # Maak eerst user aan met alleen email (of andere velden die __init__ accepteert)
        user = CustomUser(
            email=ADMIN_EMAIL,
            party=party_object # ForeignKey kan vaak wel direct mee
        )
        # Stel de wachtwoorden en booleans in
        user.set_password(ADMIN_PASSWORD)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.is_approved = True # Waarschijnlijk wil je dit ook voor de admin?

        # Stel de custom velden in
        user.initials = ADMIN_INITIALEN
        user.last_name = ADMIN_ACHTERNAAM

        # Valideer (optioneel maar goed) en sla op
        user.full_clean() # Controleert model constraints
        user.save()
        print(f"Superuser {ADMIN_EMAIL} created successfully!")
    except Exception as e:
        print(f"ERROR creating superuser: {e}")


if __name__ == "__main__":
    print("Setting up Django environment...")
    setup_django()
    create_admin_user()
