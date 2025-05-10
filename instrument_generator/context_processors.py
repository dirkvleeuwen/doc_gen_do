# context_processors.py
from django.conf import settings

def sqlite_mode(request):
    using_sqlite = (
        settings.DEBUG
        and settings.DATABASES["default"]["ENGINE"].endswith("sqlite3")
    )
    return {"sqlite_mode": using_sqlite}

def approvals_enabled(request):
    """Maakt de approvals status beschikbaar in templates."""
    return {"approvals_enabled": settings.ENABLE_APPROVALS}