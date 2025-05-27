from django import forms
from django.contrib.auth.forms import UserCreationForm
from auths.models import User
from payments.models import DeliveryInfo

class CustomUserCreationForm(forms.ModelForm):
    DELIVERY_POINTS = DeliveryInfo.DELIVERY_POINTS

    first_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 ease-in-out',
            'placeholder': 'Enter your first name',
        })
    )
    last_name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 ease-in-out',
            'placeholder': 'Enter your last name',
        })
    )
    email = forms.EmailField(
        max_length=100,
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 ease-in-out',
            'placeholder': 'Enter your email',
        }),
        required=True
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES,
        initial='customer',
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 ease-in-out',
        })
    )
    gender = forms.ChoiceField(
        choices=User.GENDER_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 ease-in-out',
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 ease-in-out',
            'placeholder': 'Enter your phone number',
        })
    )
    preferred_delivery_point = forms.ChoiceField(
        choices=DELIVERY_POINTS,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all duration-300 ease-in-out',
        })
    )
    is_superuser = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500',
        }),
        label="Superuser (Admin only)"
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'user_type', 'gender',
                  'phone_number', 'preferred_delivery_point', 'is_superuser')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            try:
                delivery_info = self.instance.deliveryinfo_set.first()
                if delivery_info:
                    self.initial['preferred_delivery_point'] = delivery_info.predefined_address
            except:
                pass

    def clean(self):
        cleaned_data = super().clean()
        user_type = cleaned_data.get('user_type')
        preferred_delivery_point = cleaned_data.get('preferred_delivery_point')

        if user_type == 'customer' and not preferred_delivery_point:
            self.add_error('preferred_delivery_point', 'Preferred delivery point is required for customers.')
        elif user_type != 'customer':
            cleaned_data['preferred_delivery_point'] = None

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=commit)
        return user  # Let the view handle DeliveryInfo creation