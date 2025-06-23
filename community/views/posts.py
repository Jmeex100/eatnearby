from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from ..models import Post, Restaurant, Review
from django.http import HttpResponseRedirect
from django.urls import reverse

# List all posts or create a new post
@login_required
def post_list_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')
        restaurant_id = request.POST.get('restaurant_id')
        image = request.FILES.get('image')
        rating = request.POST.get('rating')  # For REVIEW post type

        # Create post
        post = Post(
            author=request.user,
            title=title,
            content=content,
            post_type=post_type,
            restaurant=get_object_or_404(Restaurant, pk=restaurant_id) if restaurant_id else None,
            image=image,
            is_published=True
        )
        post.save()

        # If post is a review, create associated Review object
        if post_type == 'REVIEW' and rating:
            Review.objects.create(
                post=post,
                rating=rating,
                food_rating=request.POST.get('food_rating'),
                service_rating=request.POST.get('service_rating'),
                ambiance_rating=request.POST.get('ambiance_rating')
            )

        messages.success(request, 'Post created successfully!')
        return HttpResponseRedirect(reverse('community:post-detail', args=[post.pk]))

    posts = Post.objects.filter(is_published=True).select_related('author', 'restaurant').order_by('-created_at')
    restaurants = Restaurant.objects.all()
    context = {
        'posts': posts,
        'restaurants': restaurants,
    }
    return render(request, 'posts/post_list_create.html', context)

# Detail view for a specific post
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, is_published=True)
    comments = post.comments.filter(parent__isnull=True).select_related('author')
    review = post.review if hasattr(post, 'review') else None
    context = {
        'post': post,
        'comments': comments,
        'review': review,
    }
    return render(request, 'posts/post_detail.html', context)

# Edit an existing post
@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        post_type = request.POST.get('post_type')
        restaurant_id = request.POST.get('restaurant_id')
        image = request.FILES.get('image')
        rating = request.POST.get('rating')  # For REVIEW post type

        # Update post
        post.title = title
        post.content = content
        post.post_type = post_type
        post.restaurant = get_object_or_404(Restaurant, pk=restaurant_id) if restaurant_id else None
        if image:
            post.image = image
        post.save()

        # Update or create Review if post_type is REVIEW
        if post_type == 'REVIEW' and rating:
            review, created = Review.objects.get_or_create(post=post)
            review.rating = rating
            review.food_rating = request.POST.get('food_rating')
            review.service_rating = request.POST.get('service_rating')
            review.ambiance_rating = request.POST.get('ambiance_rating')
            review.save()

        messages.success(request, 'Post updated successfully!')
        return HttpResponseRedirect(reverse('community:post-detail', args=[post.pk]))

    restaurants = Restaurant.objects.all()
    review = post.review if hasattr(post, 'review') else None
    context = {
        'post': post,
        'restaurants': restaurants,
        'review': review,
    }
    return render(request, 'posts/post_form.html', context)

# Delete a post
@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, 'Post deleted successfully!')
        return HttpResponseRedirect(reverse('community:post-list-create'))

    context = {
        'post': post,
    }
    return render(request, 'posts/post_confirm_delete.html', context)

# Create or update a rating for a post (REVIEW type)
@login_required
def rating_create(request, post_id):
    post = get_object_or_404(Post, pk=post_id, post_type='REVIEW')
    
    # Check if user is the post author (to prevent others from rating)
    if post.author != request.user:
        raise PermissionDenied("You can only rate your own review posts.")

    if request.method == 'POST':
        rating = request.POST.get('rating')
        food_rating = request.POST.get('food_rating')
        service_rating = request.POST.get('service_rating')
        ambiance_rating = request.POST.get('ambiance_rating')

        # Create or update Review
        review, created = Review.objects.get_or_create(post=post)
        review.rating = rating
        review.food_rating = food_rating or None
        review.service_rating = service_rating or None
        review.ambiance_rating = ambiance_rating or None
        review.save()

        messages.success(request, 'Rating submitted successfully!')
        return HttpResponseRedirect(reverse('community:post-detail', args=[post.pk]))

    review = post.review if hasattr(post, 'review') else None
    context = {
        'post': post,
        'review': review,
    }
    return render(request, 'posts/rating_form.html', context)

# Edit an existing rating for a post
@login_required
def rating_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id, post_type='REVIEW')
    review = get_object_or_404(Review, post=post)
    
    # Check if user is the post author
    if post.author != request.user:
        raise PermissionDenied("You can only edit ratings for your own review posts.")

    if request.method == 'POST':
        rating = request.POST.get('rating')
        food_rating = request.POST.get('food_rating')
        service_rating = request.POST.get('service_rating')
        ambiance_rating = request.POST.get('ambiance_rating')

        # Update Review
        review.rating = rating
        review.food_rating = food_rating or None
        review.service_rating = service_rating or None
        review.ambiance_rating = ambiance_rating or None
        review.save()

        messages.success(request, 'Rating updated successfully!')
        return HttpResponseRedirect(reverse('community:post-detail', args=[post.pk]))

    context = {
        'post': post,
        'review': review,
    }
    return render(request, 'posts/rating_form.html', context)