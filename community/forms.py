from django import forms
from .models import Restaurant

class RestaurantForm(forms.ModelForm):
    class Meta:
        model = Restaurant
        fields = ['name', 'email', 'phone', 'address', 'city', 'country', 'description', 'website', 'is_verified']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }