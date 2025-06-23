from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from ..models import Recipe, RecipeIngredient, RecipeInstruction, RecipeTag
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.text import slugify

# List all recipes or create a new recipe
@login_required
def recipe_list_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        prep_time = request.POST.get('prep_time')
        cook_time = request.POST.get('cook_time')
        servings = request.POST.get('servings')
        difficulty = request.POST.get('difficulty')
        image = request.FILES.get('image')
        tag_ids = request.POST.getlist('tags')
        ingredients = request.POST.getlist('ingredients')
        instructions = request.POST.getlist('instructions')

        # Create recipe
        recipe = Recipe(
            author=request.user,
            title=title,
            content=content,
            prep_time=prep_time,
            cook_time=cook_time,
            servings=servings,
            difficulty=difficulty,
            image=image,
            is_published=True
        )
        recipe.save()

        # Add tags
        if tag_ids:
            recipe.tags.set(tag_ids)

        # Add ingredients
        for ingredient in ingredients:
            if ingredient.strip():
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    name=ingredient.strip()
                )

        # Add instructions
        for index, instruction in enumerate(instructions, 1):
            if instruction.strip():
                RecipeInstruction.objects.create(
                    recipe=recipe,
                    step_number=index,
                    instruction=instruction.strip()
                )

        messages.success(request, 'Recipe created successfully!')
        return HttpResponseRedirect(reverse('community:recipe-detail', args=[recipe.pk]))

    recipes = Recipe.objects.filter(is_published=True).select_related('author').order_by('-created_at')
    tags = RecipeTag.objects.all()
    context = {
        'recipes': recipes,
        'tags': tags,
    }
    return render(request, 'recipes/recipe_list_create.html', context)

# Detail view for a specific recipe
def recipe_detail(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, is_published=True)
    ingredients = recipe.ingredients.all()
    instructions = recipe.instructions.all()
    tags = recipe.tags.all()
    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'instructions': instructions,
        'tags': tags,
    }
    return render(request, 'recipes/recipe_detail.html', context)

# Edit an existing recipe
@login_required
def recipe_edit(request, pk):
    recipe = get_object_or_404(Recipe, pk=pk, author=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        prep_time = request.POST.get('prep_time')
        cook_time = request.POST.get('cook_time')
        servings = request.POST.get('servings')
        difficulty = request.POST.get('difficulty')
        image = request.FILES.get('image')
        tag_ids = request.POST.getlist('tags')
        ingredients = request.POST.getlist('ingredients')
        instructions = request.POST.getlist('instructions')

        # Update recipe
        recipe.title = title
        recipe.content = content
        recipe.prep_time = prep_time
        recipe.cook_time = cook_time
        recipe.servings = servings
        recipe.difficulty = difficulty
        if image:
            recipe.image = image
        recipe.save()

        # Update tags
        recipe.tags.set(tag_ids)

        # Update ingredients (delete old, add new)
        recipe.ingredients.all().delete()
        for ingredient in ingredients:
            if ingredient.strip():
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    name=ingredient.strip()
                )

        # Update instructions (delete old, add new)
        recipe.instructions.all().delete()
        for index, instruction in enumerate(instructions, 1):
            if instruction.strip():
                RecipeInstruction.objects.create(
                    recipe=recipe,
                    step_number=index,
                    instruction=instruction.strip()
                )

        messages.success(request, 'Recipe updated successfully!')
        return HttpResponseRedirect(reverse('community:recipe-detail', args=[recipe.pk]))

    ingredients = recipe.ingredients.all()
    instructions = recipe.instructions.all()
    tags = RecipeTag.objects.all()
    context = {
        'recipe': recipe,
        'ingredients': ingredients,
        'instructions': instructions,
        'tags': tags,
    }
    return render(request, 'recipes/recipe_form.html', context)

# Delete a recipe
@login_required
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