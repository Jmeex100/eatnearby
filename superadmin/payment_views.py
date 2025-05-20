from django.shortcuts import render, get_object_or_404, redirect
from payments.models import PaymentHistory
from cart.models import Cart, CartItem
from django.core.paginator import Paginator
from django.contrib import messages
from .decorators import superadmin_required
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

@superadmin_required
def payment_list(request):
    payments = PaymentHistory.objects.all().order_by('-created_at')
    query = request.GET.get('q')
    if query:
        payments = payments.filter(
            Q(transaction_id__icontains=query) |
            Q(user__username__icontains=query) |
            Q(user__email__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/payments/payment_list.html', {
        'page_obj': page_obj,
        'product_type': 'Food',  # For consistency with other templates
    })

@superadmin_required
def payment_detail(request, pk):
    payment = get_object_or_404(PaymentHistory, pk=pk)
    try:
        delivery_info = payment.delivery_info  # Correct ForeignKey access
    except:
        delivery_info = None
        logger.warning(f"No DeliveryInfo found for payment {pk}")
    cart_items = []
    try:
        cart = payment.cart
        cart_items = CartItem.objects.filter(cart=cart)
    except:
        logger.warning(f"No Cart found for payment {pk}")
    timeline_events = [
        {
            'event_type': 'created',
            'description': f"Payment {payment.transaction_id or 'N/A'} created",
            'timestamp': payment.created_at,
            'metadata': {
                'amount': payment.total,  # Fixed: Changed from payment.amount
                'method': getattr(delivery_info, 'payment_method', 'N/A'),
            }
        }
    ]
    if delivery_info and delivery_info.delivery_status != 'pending':
        timeline_events.append({
            'event_type': delivery_info.delivery_status,
            'description': f"Payment status updated to {delivery_info.get_delivery_status_display()}",
            'timestamp': delivery_info.updated_at or payment.updated_at,
            'metadata': {
                'amount': payment.total,  # Fixed: Changed from payment.amount
                'method': getattr(delivery_info, 'payment_method', 'N/A'),
            }
        })
    return render(request, 'superadmin/payments/payment_detail.html', {
        'payment': payment,
        'delivery_info': delivery_info,
        'cart_items': cart_items,
        'timeline_events': timeline_events,
        'product_type': 'Food',
    })

@superadmin_required
def approve_payment(request, pk):
    payment = get_object_or_404(PaymentHistory, pk=pk)
    if request.method == 'POST':
        try:
            if payment.delivery_info and payment.delivery_info.delivery_status == 'pending':
                payment.delivery_info.delivery_status = 'completed'
                payment.delivery_info.save()
                messages.success(request, f"Payment #{payment.transaction_id or 'N/A'} approved successfully.")
            else:
                messages.error(request, f"Payment #{payment.transaction_id or 'N/A'} cannot be approved (status: {payment.delivery_info.delivery_status if payment.delivery_info else 'N/A'}).")
        except Exception as e:
            logger.error(f"Error approving payment {pk}: {str(e)}")
            messages.error(request, "An error occurred while approving the payment.")
    return redirect('superadmin:payment_list')