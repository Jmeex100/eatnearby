from django.shortcuts import render, get_object_or_404
from payments.models import DeliveryInfo
from django.core.paginator import Paginator
from .decorators import superadmin_required

@superadmin_required
def delivery_list(request):
    deliveries = DeliveryInfo.objects.all().order_by('-created_at')
    paginator = Paginator(deliveries, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/deliveries/delivery_list.html', {'page_obj': page_obj})

@superadmin_required
def delivery_detail(request, pk):
    delivery = get_object_or_404(DeliveryInfo, pk=pk)
    return render(request, 'superadmin/deliveries/delivery_detail.html', {'delivery': delivery})

@superadmin_required
def all_deliveries(request):
    deliveries = DeliveryInfo.objects.all().order_by('-created_at')
    paginator = Paginator(deliveries, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/deliveries/delivery_list.html', {'page_obj': page_obj})