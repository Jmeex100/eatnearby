from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.text import slugify
from ..models import Recipe, RecipeIngredient, RecipeInstruction, RecipeTag, Comment, CommentLike
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.db import transaction
from ..models import Recipe, RecipeIngredient, RecipeInstruction, RecipeTag, Comment, CommentLike
from ..forms import RecipeForm, RecipeIngredientFormSet, RecipeInstructionFormSet

# Custom decorator to check if user is admin or staff
def admin_or_staff_required(view_func):
    @login_required
    def wrapper(request, *args, **kwargs):
        if request.user.user_type not in ['admin', 'staff']:
            messages.error(request, 'Only admins and staff can perform this action.')
            raise PermissionDenied("You do not have permission to perform this action.")
        return view_func(request, *args, **kwargs)
    return wrapper

# List all recipes or create a new recipe (viewable by all, creation restricted to admin/staff)
def recipe_list_create(request):
    if request.method == 'POST':
        if not request.user.is_authenticated or request.user.user_type not in ['admin', 'staff']:
            messages.error(request, 'Only admins and staff can create recipes.')
            return HttpResponseRedirect(reverse('community:recipe-list-create'))

        form = RecipeForm(request.POST, request.FILES)
        ingredient_formset = RecipeIngredientFormSet(request.POST, instance=Recipe(), prefix='ingredients')
        instruction_formset = RecipeInstructionFormSet(request.POST, instance=Recipe(), prefix='instructions')

        if form.is_valid() and ingredient_formset.is_valid() and instruction_formset.is_valid():
            with transaction.atomic():
                recipe = form.save(commit=False)
                recipe.author = request.user
                recipe.is_published = True
                recipe.save()
                form.save_m2m()

                ingredient_formset.instance = recipe
                ingredient_formset.save()

                instruction_formset.instance = recipe
                instruction_formset.save()

                messages.success(request, 'Recipe created successfully!')
                return HttpResponseRedirect(reverse('community:recipe-detail', args=[recipe.pk]))

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = RecipeForm()
        ingredient_formset = RecipeIngredientFormSet(instance=Recipe(), prefix='ingredients')
        instruction_formset = RecipeInstructionFormSet(instance=Recipe(), prefix='instructions')

    recipes = Recipe.objects.filter(is_published=True).select_related('author').prefetch_related('tags').order_by('-created_at')
    tags = RecipeTag.objects.all()
    context = {
        'form': form,
        'ingredient_formset': ingredient_formset,
        'instruction_formset': instruction_formset,
        'recipes': recipes,
        'tags': tags,
    }
    return render(request, 'recipes/recipe_list_create.html', context)
# Detail view for a specific recipe (allow comments for all authenticated users)

def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, is_published=True)
    ingredients = recipe.ingredients.all()
    instructions = recipe.instructions.all()
    tags = recipe.tags.all()
    # Fetch top-level comments (parent__isnull=True) for the recipe
    comments = recipe.comments.filter(parent__isnull=True).select_related('author').prefetch_related('replies__author')
    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'instructions': instructions,
        'tags': tags,
        'comments': comments,
    }
    return render(request, 'recipes/recipe_detail.html', context)
# Edit an existing recipe (admin/staff only)
@admin_or_staff_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)
    
    if request.method == 'POST':
        form = RecipeForm(request.POST, request.FILES, instance=recipe)
        ingredient_formset = RecipeIngredientFormSet(request.POST, instance=recipe)
        instruction_formset = RecipeInstructionFormSet(request.POST, instance=recipe)

        if form.is_valid() and ingredient_formset.is_valid() and instruction_formset.is_valid():
            with transaction.atomic():
                # Save recipe
                recipe = form.save()
                # Save ingredients
                ingredient_formset.save()
                # Save instructions
                instruction_formset.save()

                messages.success(request, 'Recipe updated successfully!')
                return HttpResponseRedirect(reverse('community:recipe-detail', args=[recipe.pk]))

        else:
            messages.error(request, 'Please correct the errors below.')

    else:
        form = RecipeForm(instance=recipe)
        ingredient_formset = RecipeIngredientFormSet(instance=recipe)
        instruction_formset = RecipeInstructionFormSet(instance=recipe)

    context = {
        'form': form,
        'ingredient_formset': ingredient_formset,
        'instruction_formset': instruction_formset,
        'recipe': recipe,
        'tags': RecipeTag.objects.all(),
    }
    return render(request, 'recipes/recipe_form.html', context)

# Delete a recipe (admin/staff only)
@admin_or_staff_required
def recipe_delete(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)
    
    if request.method == 'POST':
        recipe.delete()
        messages.success(request, 'Recipe deleted successfully!')
        return HttpResponseRedirect(reverse('community:recipe-list-create'))

    context = {
        'recipe': recipe,
    }
    return render(request, 'recipes/recipe_confirm_delete.html', context)

# Create a comment on a recipe (all authenticated users)
@login_required
def recipe_comment_create(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, is_published=True)
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')  # For replies
        if content:
            comment = Comment.objects.create(
                author=request.user,
                content=content,
                parent=get_object_or_404(Comment, pk=parent_id) if parent_id else None
            )
            recipe.recipe_comments.add(comment)  # Link comment to recipe via ManyToManyField
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Comment cannot be empty.')
        return HttpResponseRedirect(reverse('community:recipe-detail', args=[recipe.pk]))
    return HttpResponseRedirect(reverse('community:recipe-detail', args=[recipe.pk]))

# Like a comment on a recipe (all authenticated users)
@login_required
def recipe_comment_like(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    if request.method == 'POST':
        comment_like, created = CommentLike.objects.get_or_create(user=request.user, comment=comment)
        if not created:
            comment_like.delete()  # Unlike if already liked
            messages.success(request, 'Comment unliked.')
        else:
            messages.success(request, 'Comment liked.')
        # Redirect to recipe detail page, using recipe.pk from comment's related recipe
        recipe = comment.recipe_comments.first()  # Get the recipe associated with the comment
        if recipe:
            return HttpResponseRedirect(reverse('community:recipe-detail', args=[recipe.pk]))
        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))