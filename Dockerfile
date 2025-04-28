# Gebruik officieel Python-beeld
FROM python:3.11-slim

# Werkdirectory
WORKDIR /app

# Installeer dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer applicatiecode
COPY . .

# Expose en start
EXPOSE 8000
CMD ["gunicorn", "--workers", "3", "instrument_generator.wsgi:application", "--bind", "0.0.0.0:8000"]