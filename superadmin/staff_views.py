from django.shortcuts import render, get_object_or_404
from staffs.models import StaffServiceArea, StaffAssignment
from django.core.paginator import Paginator
from .decorators import superadmin_required

@superadmin_required
def staff_service_area_list(request):
    areas = StaffServiceArea.objects.all().order_by('name')
    paginator = Paginator(areas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/staff/staff_service_area_list.html', {'page_obj': page_obj})

@superadmin_required
def staff_service_area_detail(request, pk):
    area = get_object_or_404(StaffServiceArea, pk=pk)
    return render(request, 'superadmin/staff/staff_service_area_detail.html', {'area': area})

@superadmin_required
def staff_assignment_list(request):
    assignments = StaffAssignment.objects.all().order_by('-created_at')
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/staff/staff_assignment_list.html', {'page_obj': page_obj})

@superadmin_required
def staff_assignment_detail(request, pk):
    assignment = get_object_or_404(StaffAssignment, pk=pk)
    return render(request, 'superadmin/staff/staff_assignment_detail.html', {'assignment': assignment})