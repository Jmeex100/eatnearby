from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from ..models import Post, Restaurant, Review, Comment, PostLike, CommentLike

# List all posts or create a new post
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from ..models import Post, Restaurant, Review
from ..forms import PostForm, ReviewForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from ..models import Post, Restaurant, Review
from ..forms import PostForm, ReviewForm
import logging

# Configure logging
logger = logging.getLogger(__name__)

def post_list_create(request):
    if request.method == 'POST':
        post_form = PostForm(request.POST, request.FILES)
        review_form = ReviewForm(request.POST) if request.POST.get('post_type') == 'REVIEW' else None
        
        forms_valid = post_form.is_valid() and (review_form is None or review_form.is_valid())
        
        if forms_valid:
            post = post_form.save(commit=False)
            post.author = request.user
            
            # Additional validation for review posts
            if post.post_type == 'REVIEW' and not post.restaurant:
                messages.error(request, 'A restaurant is required for review posts.')
                logger.error('Review post creation failed: No restaurant selected.')
                return render(request, 'posts/post_list_create.html', {
                    'post_form': post_form,
                    'review_form': review_form or ReviewForm(),
                    'posts': Post.objects.filter(is_published=True).select_related('author', 'restaurant').order_by('-created_at'),
                    'restaurants': Restaurant.objects.all().order_by('name'),
                    'post_types': Post.POST_TYPES,
                })
            
            post.save()
            
            if post.post_type == 'REVIEW' and review_form:
                review = review_form.save(commit=False)
                review.post = post
                review.save()
                logger.info(f"Review post created: ID={post.id}, Restaurant={post.restaurant.name}")
            
            messages.success(request, 'Post created successfully!')
            logger.info(f"Post created: ID={post.id}, Type={post.post_type}")
            return redirect('community:post-list-create')
        
        # Form validation failed
        logger.error(f"Form errors - Post: {post_form.errors}, Review: {review_form.errors if review_form else 'N/A'}")
        messages.error(request, 'Please correct the errors below.')
    
    else:
        post_form = PostForm()
        review_form = ReviewForm()

    posts = Post.objects.filter(is_published=True).select_related('author', 'restaurant').order_by('-created_at')
    restaurants = Restaurant.objects.all().order_by('name')
    
    return render(request, 'posts/post_list_create.html', {
        'post_form': post_form,
        'review_form': review_form,
        'posts': posts,
        'restaurants': restaurants,
        'post_types': Post.POST_TYPES,
    })

# Detail view for a specific post
def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, is_published=True)
    comments = post.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author')
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

        # Validate input
        if not title or not content or not post_type:
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'posts/post_form.html', {
                'post': post,
                'restaurants': Restaurant.objects.all(),
                'review': post.review if hasattr(post, 'review') else None,
            })

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
            try:
                review, created = Review.objects.get_or_create(post=post)
                review.rating = int(rating)
                review.food_rating = int(request.POST.get('food_rating')) if request.POST.get('food_rating') else None
                review.service_rating = int(request.POST.get('service_rating')) if request.POST.get('service_rating') else None
                review.ambiance_rating = int(request.POST.get('ambiance_rating')) if request.POST.get('ambiance_rating') else None
                review.save()
            except ValueError:
                messages.error(request, 'Invalid rating values.')
                return render(request, 'posts/post_form.html', {
                    'post': post,
                    'restaurants': Restaurant.objects.all(),
                    'review': post.review if hasattr(post, 'review') else None,
                })

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
    
    if post.author != request.user:
        raise PermissionDenied("You can only rate your own review posts.")

    if request.method == 'POST':
        rating = request.POST.get('rating')
        food_rating = request.POST.get('food_rating')
        service_rating = request.POST.get('service_rating')
        ambiance_rating = request.POST.get('ambiance_rating')

        try:
            review, created = Review.objects.get_or_create(post=post)
            review.rating = int(rating)
            review.food_rating = int(food_rating) if food_rating else None
            review.service_rating = int(service_rating) if service_rating else None
            review.ambiance_rating = int(ambiance_rating) if ambiance_rating else None
            review.save()
            messages.success(request, 'Rating submitted successfully!')
        except ValueError:
            messages.error(request, 'Invalid rating values.')
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
    
    if post.author != request.user:
        raise PermissionDenied("You can only edit ratings for your own review posts.")

    if request.method == 'POST':
        rating = request.POST.get('rating')
        food_rating = request.POST.get('food_rating')
        service_rating = request.POST.get('service_rating')
        ambiance_rating = request.POST.get('ambiance_rating')

        try:
            review.rating = int(rating)
            review.food_rating = int(food_rating) if food_rating else None
            review.service_rating = int(service_rating) if service_rating else None
            review.ambiance_rating = int(ambiance_rating) if ambiance_rating else None
            review.save()
            messages.success(request, 'Rating updated successfully!')
        except ValueError:
            messages.error(request, 'Invalid rating values.')
        return HttpResponseRedirect(reverse('community:post-detail', args=[post.pk]))

    context = {
        'post': post,
        'review': review,
    }
    return render(request, 'posts/rating_form.html', context)

# Like a post
@login_required
def post_like(request, pk):
    post = get_object_or_404(Post, pk=pk, is_published=True)
    if request.method == 'POST':
        post_like, created = PostLike.objects.get_or_create(user=request.user, post=post)
        if not created:
            post_like.delete()  # Unlike if already liked
            messages.success(request, 'Post unliked.')
        else:
            messages.success(request, 'Post liked.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('community:post-detail', args=[post.pk])))
    return HttpResponseRedirect(reverse('community:post-detail', args=[post.pk]))

# Like a comment
# Like a comment
@login_required
def comment_like(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    emoji = "👍"  # Default emoji for liked comment
    if request.method == 'POST':
        comment_like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            comment_like.delete()  # Unlike if already liked
            emoji = "👎"  # Change emoji to thumbs down if unliked
            messages.success(request, 'Comment unliked.')
        else:
            messages.success(request, 'Comment liked.')
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('community:post-detail', args=[comment.post.pk])))
    return HttpResponseRedirect(reverse('community:post-detail', args=[comment.post.pk]))
# Create a comment
@login_required
def comment_create(request, pk):
    post = get_object_or_404(Post, pk=pk, is_published=True)
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')  # For replies
        if content:
            comment = Comment.objects.create(
                author=request.user,
                post=post,
                content=content,
                parent=get_object_or_404(Comment, pk=parent_id) if parent_id else None
            )
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Comment cannot be empty.')
        return HttpResponseRedirect(reverse('community:post-detail', args=[post.pk]))
    return HttpResponseRedirect(reverse('community:post-detail', args=[post.pk]))