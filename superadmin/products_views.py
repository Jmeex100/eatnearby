from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from auths.models import Food, Category
from django.core.paginator import Paginator
from django.forms import ModelForm
from .decorators import superadmin_required

class ProductForm(ModelForm):
    class Meta:
        model = Food
        fields = ['product_id', 'name', 'category', 'price', 'quantity', 'description', 'image_url']  # Added quantity and product_id

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional: Customize field attributes (e.g., placeholders, classes)
        self.fields['product_id'].widget.attrs.update({'class': 'w-full border-gray-300 rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 transition-colors'})
        self.fields['name'].widget.attrs.update({'class': 'w-full border-gray-300 rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 transition-colors'})
        self.fields['category'].widget.attrs.update({'class': 'w-full border-gray-300 rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 transition-colors'})
        self.fields['price'].widget.attrs.update({'class': 'w-full border-gray-300 rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 transition-colors'})
        self.fields['quantity'].widget.attrs.update({'class': 'w-full border-gray-300 rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 transition-colors'})
        self.fields['description'].widget.attrs.update({'class': 'w-full border-gray-300 rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 transition-colors'})
        self.fields['image_url'].widget.attrs.update({'class': 'w-full border-gray-300 rounded-lg p-2 dark:bg-gray-700 dark:border-gray-600 dark:text-gray-200 transition-colors'})

@superadmin_required
def product_list(request):
    products = Food.objects.all().order_by('-created_at')
    paginator = Paginator(products, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'superadmin/products/product_list.html', {'page_obj': page_obj})

@superadmin_required
def product_detail(request, pk):
    product = get_object_or_404(Food, pk=pk)
    return render(request, 'superadmin/products/product_detail.html', {'product': product})

@superadmin_required
def product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product created successfully.")
            return redirect('superadmin:product_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm()
    return render(request, 'superadmin/products/product_form.html', {'form': form, 'action': 'Create'})

@superadmin_required
def product_update(request, pk):
    product = get_object_or_404(Food, pk=pk)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully.")
            return redirect('superadmin:product_list')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProductForm(instance=product)
    return render(request, 'superadmin/products/product_form.html', {'form': form, 'action': 'Update'})

@superadmin_required
def product_delete(request, pk):
    product = get_object_or_404(Food, pk=pk)
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully.")
        return redirect('superadmin:product_list')
    return render(request, 'superadmin/products/product_delete.html', {'product': product})