# instrument_generator/health.py

from django.http import HttpResponse
from django.contrib.auth.decorators import login_not_required

@login_not_required
def health(request):
    return HttpResponse("OK")
