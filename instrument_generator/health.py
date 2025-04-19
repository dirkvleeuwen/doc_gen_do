# instrument_generator/health.py

from django.http import HttpResponse

def health(request):
    return HttpResponse("OK")
