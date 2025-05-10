from django import template
from approvals.models import ApprovalRequest
import difflib

register = template.Library()

@register.simple_tag
def pending_approvals_count():
    """Return the number of pending approval requests"""
    return ApprovalRequest.objects.filter(status='PENDING').count()

@register.simple_tag
def user_has_pending_approvals(user):
    """Check if a specific user has pending approval requests"""
    if user.has_perm('approvals.can_review_submissions'):
        return ApprovalRequest.objects.filter(status='PENDING').exists()
    return False

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using bracket notation in templates"""
    return dictionary.get(str(key))

@register.filter
def generate_diff_lines(text1, text2):
    """
    Generate HTML diff between two texts with added/removed/unchanged lines.
    text1 should be the original (older) version
    text2 should be the new version
    """
    if not text1 or not text2:
        return []
    
    # Split both texts into lines
    lines1 = text1.splitlines()
    lines2 = text2.splitlines()
    
    # Use differ to get the differences
    differ = difflib.Differ()
    diff = list(differ.compare(lines1, lines2))
    
    # Process the diff output
    result = []
    for line in diff:
        if line.startswith('  '):  # Unchanged
            result.append(('unchanged', line[2:]))
        elif line.startswith('- '):  # Removed (in original but not in new)
            result.append(('removed', line[2:]))
        elif line.startswith('+ '):  # Added (in new but not in original)
            result.append(('added', line[2:]))
            
    return result