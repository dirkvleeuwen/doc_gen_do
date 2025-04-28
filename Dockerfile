# Gebruik officieel Python-beeld
FROM python:3.11-slim

# Werkdirectory
WORKDIR /app

# System dependencies for WeasyPrint PDF rendering
RUN apt-get update && apt-get install -y \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libglib2.0-0 \
    libgdk-pixbuf2.0-0 \
    libffi7 \
    shared-mime-info \
  && rm -rf /var/lib/apt/lists/*

# Installeer dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer applicatiecode
COPY . .

# Expose en start
EXPOSE 8000
CMD ["gunicorn", "--workers", "3", "instrument_generator.wsgi:application", "--bind", "0.0.0.0:8000"]