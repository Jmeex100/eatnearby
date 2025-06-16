from django.contrib import admin
from .models import (
    Restaurant, UserProfile, Post, PostLike, Review, Comment, CommentLike,
    Challenge, ChallengeParticipation, Recipe, RecipeIngredient, RecipeInstruction,
    RecipeTag, RestaurantQuestion, RestaurantAnswer
)

# Register Restaurant
@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'is_verified', 'created_at')
    list_filter = ('is_verified', 'city')
    search_fields = ('name', 'address', 'city', 'email')
    list_editable = ('is_verified',)
    ordering = ('name',)

# Register UserProfile
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'dietary_preferences', 'created_at')
    search_fields = ('user__username', 'bio', 'dietary_preferences')
    filter_horizontal = ('favorite_restaurants',)

# Register Post
@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'post_type', 'restaurant', 'is_published', 'created_at')
    list_filter = ('post_type', 'is_published', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    list_editable = ('is_published',)
    ordering = ('-created_at',)

# Register PostLike
@admin.register(PostLike)
class PostLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at')
    search_fields = ('user__username', 'post__title')
    list_filter = ('created_at',)

# Register Review
@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('post', 'rating', 'food_rating', 'service_rating', 'ambiance_rating', 'created_at')
    search_fields = ('post__title', 'post__restaurant__name')
    list_filter = ('rating', 'created_at')

# Register Comment
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'post', 'parent', 'created_at')
    search_fields = ('content', 'author__username', 'post__title')
    list_filter = ('created_at',)

# Register CommentLike
@admin.register(CommentLike)
class CommentLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'comment', 'created_at')
    search_fields = ('user__username', 'comment__content')
    list_filter = ('created_at',)

# Register Challenge
@admin.register(Challenge)
class ChallengeAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_date', 'end_date', 'is_active', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('is_active', 'start_date', 'end_date')
    list_editable = ('is_active',)
    prepopulated_fields = {'slug': ('title',)}

# Register ChallengeParticipation
@admin.register(ChallengeParticipation)
class ChallengeParticipationAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'post', 'completed', 'created_at')
    search_fields = ('user__username', 'challenge__title', 'post__title')
    list_filter = ('completed', 'created_at')

# Register Recipe
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'difficulty', 'prep_time', 'cook_time', 'is_published')
    search_fields = ('title', 'content', 'author__username')
    list_filter = ('difficulty', 'is_published', 'created_at')
    filter_horizontal = ('tags',)

# Register RecipeIngredient
@admin.register(RecipeIngredient)
class RecipeIngredientAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'name', 'quantity', 'notes')
    search_fields = ('name', 'recipe__title', 'notes')
    list_filter = ('recipe',)

# Register RecipeInstruction
@admin.register(RecipeInstruction)
class RecipeInstructionAdmin(admin.ModelAdmin):
    list_display = ('recipe', 'step_number', 'instruction', 'created_at')
    search_fields = ('instruction', 'recipe__title')
    list_filter = ('recipe',)
    ordering = ('recipe', 'step_number')

# Register RecipeTag
@admin.register(RecipeTag)
class RecipeTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}

# Register RestaurantQuestion
@admin.register(RestaurantQuestion)
class RestaurantQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'restaurant', 'is_answered', 'created_at')
    search_fields = ('question', 'user__username', 'restaurant__name')
    list_filter = ('is_answered', 'created_at')

# Register RestaurantAnswer
@admin.register(RestaurantAnswer)
class RestaurantAnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'responder', 'created_at')
    search_fields = ('answer', 'question__question', 'responder__username')
    list_filter = ('created_at',)