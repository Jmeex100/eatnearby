from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100, 
        widget=forms.TextInput(attrs={
            'placeholder': 'Your Name', 
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Your Email', 
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Your Message', 
            'rows': 8,
            'class': 'w-full p-3 border border-gray-300 rounded-lg focus:outline-none focus:border-blue-500'
        })
    )

# /home/surecode/Documents/GitHub/django/coreEat/sim/forms.py