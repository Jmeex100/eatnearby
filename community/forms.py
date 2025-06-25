from django import forms
from .models import Restaurant ,Review ,Post

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