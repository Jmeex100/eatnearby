from .models import DeliveryInfo

def order_notifications(request):
    if not request.user.is_authenticated:
        return {
            'nav_in_progress_count': 0,
            'nav_declined_count': 0,
        }
    
    in_progress_count = DeliveryInfo.objects.filter(
        user=request.user,
        delivery_status='in_progress'
    ).count()
    declined_count = DeliveryInfo.objects.filter(
        user=request.user,
        delivery_status='cancelled'
    ).count()
    
    return {
        'nav_in_progress_count': in_progress_count,
        'nav_declined_count': declined_count,
        'nav_total_notifications': in_progress_count + declined_count,
    }
    # /home/surecode/Documents/GitHub/django/eatnearby/payments/context_processors.py