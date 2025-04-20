# create_dot_env.py (Aangepaste versie met batching)
import boto3
import os

params_to_fetch = [
    '/instrument_generator/prod/SECRET_KEY',
    '/instrument_generator/prod/DB_PASSWORD',
    '/instrument_generator/prod/DB_NAME',
    '/instrument_generator/prod/DB_USER',
    '/instrument_generator/prod/DB_HOST',
    '/instrument_generator/prod/DB_PORT',
    '/instrument_generator/prod/EMAIL_HOST_USER',
    '/instrument_generator/prod/EMAIL_HOST_PASSWORD',
    '/instrument_generator/prod/ALLOWED_HOSTS',
    '/instrument_generator/prod/DEBUG',
    '/instrument_generator/prod/AWS_STORAGE_BUCKET_NAME', # Voeg toe indien nodig
    '/instrument_generator/prod/AWS_REGION', # Voeg toe indien nodig
    '/instrument_generator/prod/AWS_S3_REGION_NAME',
    # Voeg andere parameters toe...
]

# Gebruik de regio van de EC2 instance metadata of een default
session = boto3.Session()
# Pas regio aan indien nodig, of stel AWS_REGION env var in
ssm = session.client('ssm', region_name=os.getenv('AWS_REGION', 'eu-central-1'))

print("Fetching parameters from AWS Parameter Store...")

parameters = {} # Initialiseer een lege dictionary om resultaten te verzamelen
batch_size = 10 # Maximaal 10 parameters per API call

try:
    # Loop door de lijst in batches van 'batch_size'
    for i in range(0, len(params_to_fetch), batch_size):
        batch_names = params_to_fetch[i:i + batch_size] # Pak de huidige batch namen
        print(f"Fetching batch: {batch_names}") # Optioneel: laat zien welke batch wordt gehaald

        # Roep GetParameters aan voor de huidige batch
        response = ssm.get_parameters(Names=batch_names, WithDecryption=True)

        # Voeg de opgehaalde parameters toe aan de hoofddictionary
        # Controleer of er wel parameters zijn teruggekomen
        if 'Parameters' in response:
             parameters.update({p['Name']: p['Value'] for p in response['Parameters']})

        # Controleer of er ongeldige parameters waren in deze batch
        if 'InvalidParameters' in response and response['InvalidParameters']:
             print(f"Warning: Could not find the following parameters in this batch: {response['InvalidParameters']}")


    # --- Schrijf naar .env file (deze logica blijft hetzelfde) ---
    print("Writing parameters to .env file...")
    with open('.env', 'w') as f:
        if not parameters:
             print("Warning: No parameters were fetched successfully.")
        for name, value in parameters.items():
            # Converteer /path/to/PARAM_NAME naar PARAM_NAME
            env_var_name = name.split('/')[-1]
            # Zorg voor correcte quoting, vooral voor multiline of speciale tekens
            # Simpele quoting voor nu:
            f.write(f"{env_var_name}='{value}'\n")

    print("Successfully created .env file.")

except Exception as e:
    print(f"Error fetching parameters or writing .env file: {e}")
