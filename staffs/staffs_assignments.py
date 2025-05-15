# staffs/staffs_assignments.py

from django.db.models import Min
from django.contrib.auth import get_user_model
from .models import StaffServiceArea

User = get_user_model()

def pick_staff_for_point(point_key):
    """
    Returns the staff who covers `point_key` whose last assignment is oldest.
    """
    # Get staff who serve this point
    staff_qs = User.objects.filter(
        user_type='staff',
        service_areas__point=point_key
    ).distinct()

    if not staff_qs.exists():
        return None

    # Annotate each with their earliest (oldest) assignment timestamp
    staff_qs = staff_qs.annotate(
        last_assigned=Min('delivery_assignments__assigned_at')
    ).order_by('last_assigned')  # nulls first = those never assigned

    return staff_qs.first()
