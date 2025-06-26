from django import forms
from .models import Restaurant ,Review ,Post ,RestaurantAnswer
from .models import Recipe, RecipeIngredient, RecipeInstruction, RecipeTag ,RestaurantQuestion
from django.forms import inlineformset_factory


class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'email', 'phone', 'address', 'city', 'country', 'description', 'website', 'is_verified']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
        

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'post_type', 'restaurant', 'image']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'title': forms.TextInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'post_type': forms.Select(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'id': 'id_post_type'}),
            'restaurant': forms.Select(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'image': forms.FileInput(attrs={'class': 'w-full p-2 border rounded', 'accept': 'image/*'}),
        }

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['rating', 'food_rating', 'service_rating', 'ambiance_rating']
        widgets = {
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'food_rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'service_rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'ambiance_rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
        }
        
        


class RecipeForm(forms.ModelForm):
    class Meta:
        model = Recipe
        fields = ['title', 'content', 'prep_time', 'cook_time', 'servings', 'difficulty', 'image', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'content': forms.Textarea(attrs={'rows': 4, 'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'prep_time': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'min': 0}),
            'cook_time': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'min': 0}),
            'servings': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'min': 1}),
            'difficulty': forms.Select(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
            'image': forms.FileInput(attrs={'class': 'w-full p-2 border rounded', 'accept': 'image/*'}),
            'tags': forms.SelectMultiple(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200'}),
        }

# Inline formset for RecipeIngredient
RecipeIngredientFormSet = inlineformset_factory(
    Recipe,
    RecipeIngredient,
    fields=('quantity', 'name', 'notes'),
    extra=1,
    can_delete=True,
    widgets={
        'quantity': forms.TextInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'placeholder': 'e.g., 2 cups'}),
        'name': forms.TextInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'placeholder': 'e.g., flour'}),
        'notes': forms.TextInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'placeholder': 'e.g., sifted'}),
    }
)

# Inline formset for RecipeInstruction
RecipeInstructionFormSet = inlineformset_factory(
    Recipe,
    RecipeInstruction,
    fields=('step_number', 'instruction'),
    extra=1,
    can_delete=True,
    widgets={
        'step_number': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'min': 1}),
        'instruction': forms.Textarea(attrs={'rows': 2, 'class': 'w-full p-2 border rounded bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-200', 'placeholder': 'e.g., Preheat oven to 350°F'}),
    }
)

from django import forms
from .models import Restaurant, RestaurantQuestion

class QuestionForm(forms.ModelForm):
    restaurant = forms.ModelChoiceField(
        queryset=Restaurant.objects.all(),
        label="Restaurant",
        widget=forms.Select(attrs={
            'class': 'w-full p-3 border rounded-lg text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-amber-500 focus:border-amber-500'
        })
    )

    class Meta:
        model = RestaurantQuestion
        fields = ['restaurant', 'question']
        widgets = {
            'question': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full p-3 border rounded-lg text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'Type your question here...'
            }),
        }
        
        
class AnswerForm(forms.ModelForm):
    class Meta:
        model = RestaurantAnswer
        fields = ['answer']
        widgets = {
            'answer': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full p-3 border rounded-lg text-gray-800 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 focus:ring-amber-500 focus:border-amber-500',
                'placeholder': 'Type your answer here...'
            }),
        }
