from django.shortcuts import render, get_object_or_404, redirect
from cart.models import Cart, CartItem
from django.core.paginator import Paginator
from django.contrib import messages
from django.views.decorators.http import require_POST
from .decorators import superadmin_required
import logging

logger = logging.getLogger(__name__)

def get_unread_notification_count(user):
    # Placeholder: Replace with your actual notification logic
    return 0

@superadmin_required
def cart_list(request):
    carts = Cart.objects.all().order_by('-created_at')
    paginator = Paginator(carts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'unread_notifications_count': get_unread_notification_count(request.user),
        'product_type': 'Food',  # For consistency with product templates
    }
    return render(request, 'superadmin/carts/cart_list.html', context)

@superadmin_required
def cart_detail(request, pk):
    cart = get_object_or_404(Cart, pk=pk)
    context = {
        'cart': cart,
        'unread_notifications_count': get_unread_notification_count(request.user),
        'product_type': 'Food',  # For consistency with product templates
    }
    return render(request, 'superadmin/carts/cart_detail.html', context)

@superadmin_required
@require_POST
def cart_delete(request, pk):
    cart = get_object_or_404(Cart, pk=pk)
    try:
        cart_id = cart.pk
        cart.delete()
        messages.success(request, f"Cart #{cart_id} deleted successfully.")
    except Exception as e:
        logger.error(f"Error deleting cart {pk}: {str(e)}")
        messages.error(request, "An error occurred while deleting the cart.")
    return redirect('superadmin:cart_list')