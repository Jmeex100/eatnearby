from django.shortcuts import render, get_object_or_404, redirect
from staffs.models import StaffServiceArea, StaffAssignment
from payments.models import DeliveryInfo
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .decorators import superadmin_required
from django.contrib import messages
from django import forms
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class StaffServiceAreaForm(forms.ModelForm):
    class Meta:
        model = StaffServiceArea
        fields = ['staff', 'point']
        widgets = {
            'staff': forms.Select(attrs={'class': 'p-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'}),
            'point': forms.Select(attrs={'class': 'p-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['staff'].queryset = self.fields['staff'].queryset.filter(user_type='staff')

class StaffAssignmentForm(forms.ModelForm):
    class Meta:
        model = StaffAssignment
        fields = ['staff', 'delivery']
        widgets = {
            'staff': forms.Select(attrs={'class': 'p-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'}),
            'delivery': forms.Select(attrs={'class': 'p-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600 dark:text-gray-100'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['staff'].queryset = self.fields['staff'].queryset.filter(user_type='staff')
        self.fields['delivery'].queryset = DeliveryInfo.objects.filter(delivery_status__in=['pending', 'in_progress'])

@superadmin_required
def staff_service_area_list(request):
    areas = StaffServiceArea.objects.select_related('staff').order_by('staff__username')
    query = request.GET.get('q')
    if query:
        areas = areas.filter(
            Q(staff__username__icontains=query) |
            Q(point__icontains=query)
        )
    staff_areas = {}
    for area in areas:
        staff_id = area.staff.id
        if staff_id not in staff_areas:
            staff_areas[staff_id] = {
                'staff': area.staff,
                'points': [],
                'pk': area.pk
            }
        staff_areas[staff_id]['points'].append(area.get_point_display())
    grouped_areas = list(staff_areas.values())
    paginator = Paginator(grouped_areas, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/staff/staff_service_area_list.html', {'page_obj': page_obj})

@superadmin_required
def staff_service_area_create(request):
    if request.method == 'POST':
        form = StaffServiceAreaForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Staff service area created successfully.')
                return redirect('superadmin:staff_service_area_list')
            except Exception as e:
                logger.error(f"Error creating staff service area: {str(e)}")
                messages.error(request, 'Failed to create staff service area. This staff may already be assigned to this delivery point.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffServiceAreaForm()
    return render(request, 'superadmin/staff/staff_service_area_create.html', {'form': form})

@superadmin_required
def staff_service_area_detail(request, pk):
    area = get_object_or_404(StaffServiceArea, pk=pk)
    return render(request, 'superadmin/staff/staff_service_area_detail.html', {'area': area})

@superadmin_required
def staff_assignment_list(request):
    # Get all assignments
    assignments = StaffAssignment.objects.select_related('staff', 'delivery').order_by('-assigned_at')
    query = request.GET.get('q')
    if query:
        assignments = assignments.filter(
            Q(staff__username__icontains=query) |
            Q(delivery__id__exact=query) |
            Q(delivery__address__icontains=query) |
            Q(delivery__predefined_address__icontains=query)
        )

    # Dashboard: Today's assignments (filtered by current date in CAT timezone)
    today = timezone.now().date()
    today_assignments = StaffAssignment.objects.filter(
        assigned_at__date=today
    ).select_related('delivery')
    if query:
        today_assignments = today_assignments.filter(
            Q(staff__username__icontains=query) |
            Q(delivery__id__exact=query) |
            Q(delivery__address__icontains=query) |
            Q(delivery__predefined_address__icontains=query)
        )

    # Compute status counts for dashboard
    status_counts = today_assignments.values('delivery__delivery_status').annotate(count=Count('id')).order_by()
    dashboard_stats = {
        'total': today_assignments.count(),
        'pending': 0,
        'in_progress': 0,
        'completed': 0,
        'cancelled': 0
    }
    for item in status_counts:
        status = item['delivery__delivery_status']
        if status in dashboard_stats:
            dashboard_stats[status] = item['count']

    # Pagination for main table
    paginator = Paginator(assignments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'dashboard_stats': dashboard_stats,
        'today': today.strftime('%B %d, %Y')
    }
    return render(request, 'superadmin/staff/staff_assignment_list.html', context)

@superadmin_required
def staff_assignment_create(request):
    if request.method == 'POST':
        form = StaffAssignmentForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, 'Staff assignment created successfully.')
                return redirect('superadmin:staff_assignment_list')
            except Exception as e:
                logger.error(f"Error creating staff assignment: {str(e)}")
                messages.error(request, 'Failed to create staff assignment. This staff may already be assigned to this delivery.')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = StaffAssignmentForm()
    return render(request, 'superadmin/staff/staff_assignment_create.html', {'form': form})

@superadmin_required
def staff_assignment_detail(request, pk):
    assignment = get_object_or_404(StaffAssignment, pk=pk)
    return render(request, 'superadmin/staff/staff_assignment_detail.html', {'assignment': assignment})