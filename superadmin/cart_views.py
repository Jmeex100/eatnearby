from django.shortcuts import render, get_object_or_404
from cart.models import Cart
from django.core.paginator import Paginator
from .decorators import superadmin_required

@superadmin_required
def cart_list(request):
    carts = Cart.objects.all().order_by('-created_at')
    paginator = Paginator(carts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/carts/cart_list.html', {'page_obj': page_obj})

@superadmin_required
def cart_detail(request, pk):
    cart = get_object_or_404(Cart, pk=pk)
    return render(request, 'superadmin/carts/cart_detail.html', {'cart': cart})