"""
Approvals app voor het goedkeuren van inhoud.
"""
from django.conf import settings

def is_enabled():
    """
    Controleert of de approvals functionaliteit is ingeschakeld.
    
    Returns:
        bool: True als approvals is ingeschakeld, anders False.
    """
    return getattr(settings, 'ENABLE_APPROVALS', True)