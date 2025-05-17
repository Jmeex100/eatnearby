from django.shortcuts import render
from .decorators import superadmin_required

@superadmin_required
def revenue_dashboard(request):
    return render(request, 'superadmin/revenue/revenue_dashboard.html')

@superadmin_required
def revenue_detail(request, method):
    return render(request, 'superadmin/revenue/revenue_detail.html')