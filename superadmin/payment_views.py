from django.shortcuts import render, get_object_or_404
from payments.models import PaymentHistory
from django.core.paginator import Paginator
from .decorators import superadmin_required

@superadmin_required
def payment_list(request):
    payments = PaymentHistory.objects.all().order_by('-created_at')
    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/payments/payment_list.html', {'page_obj': page_obj})

@superadmin_required
def payment_detail(request, pk):
    payment = get_object_or_404(PaymentHistory, pk=pk)
    return render(request, 'superadmin/payments/payment_detail.html', {'payment': payment})