# /home/surecode/Documents/Django/GitHub/eatnearby/community/views/restaurants.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from ..models import Restaurant, Post, RestaurantQuestion
from ..forms import RestaurantForm  # You'll need to create this form

# Helper to check if user is staff
def is_staff(user):
    return user.is_authenticated and user.is_staff
def restaurant(request):
    restaurant = Restaurant.objects.get()
    return render(request, 'restaurant/restaurant.html', {'restaurants': []})

def restaurant_list(request):
    try:
        restaurant = Restaurant.objects.get()
        return redirect('community:restaurant-detail', pk=restaurant.pk)
    except Restaurant.DoesNotExist:
        messages.error(request, "No restaurant exists in the database. Please contact the administrator.")
        return render(request, 'restaurant/restaurant_list.html', {'restaurants': []})
    except Restaurant.MultipleObjectsReturned:
        messages.warning(request, "Multiple restaurants found. Showing the first one.")
        restaurant = Restaurant.objects.first()
        return redirect('community:restaurant-detail', pk=restaurant.pk)

def restaurant_detail(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    posts = Post.objects.filter(restaurant=restaurant, is_published=True).select_related('author', 'review').order_by('-created_at')
    questions = RestaurantQuestion.objects.filter(restaurant=restaurant).select_related('user', 'answer').order_by('-created_at')
    context = {
        'restaurant': restaurant,
        'posts': posts,
        'questions': questions,
    }
    return render(request, 'restaurant/restaurant_detail.html', context)

@user_passes_test(is_staff)
def restaurant_edit(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        form = RestaurantForm(request.POST, instance=restaurant)
        if form.is_valid():
            form.save()
            messages.success(request, "Restaurant updated successfully.")
            return redirect('community:restaurant-detail', pk=restaurant.pk)
    else:
        form = RestaurantForm(instance=restaurant)
    return render(request, 'restaurant/restaurant_form.html', {'form': form, 'restaurant': restaurant})

@user_passes_test(is_staff)
def restaurant_delete(request, pk):
    restaurant = get_object_or_404(Restaurant, pk=pk)
    if request.method == 'POST':
        restaurant.delete()
        messages.success(request, "Restaurant deleted successfully.")
        return redirect('community:restaurant-list')
    return render(request, 'restaurant/restaurant_confirm_delete.html', {'restaurant': restaurant})