from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from auths.models import User

@login_required
def profile(request):
    """Display the user's profile information."""
    user = request.user
    # Get the human-readable gender display (e.g., "Mr.", "Mrs.", "Other")
    gender_display = user.get_gender_display() if user.gender else "Not specified"
    
    context = {
        'user': user,
        'full_name': f"{user.first_name} {user.last_name}",
        'user_type': user.get_user_type_display(),  # Human-readable user type
        'gender_prefix': gender_display,  # Pass the gender display value
    }
    return render(request, 'auths/profile.html', context)

@login_required
def settings(request):
    """Allow the user to update phone number, image, or change password."""
    user = request.user

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        if form_type == 'profile':
            # Profile update logic
            phone_number = request.POST.get('phone_number', '').strip()
            image = request.FILES.get('image')

            user.phone_number = phone_number if phone_number else None
            if image:
                user.image = image
            user.save()
            messages.success(request, "Profile updated successfully!")
            return redirect('profile')

        elif form_type == 'password':
            # Password change logic
            current_password = request.POST.get('current_password')
            new_password1 = request.POST.get('new_password1')
            new_password2 = request.POST.get('new_password2')

            # Validation
            if not user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif new_password1 != new_password2:
                messages.error(request, "New passwords do not match.")
            elif len(new_password1) < 8:
                messages.error(request, "New password must be at least 8 characters long.")
            else:
                user.set_password(new_password1)
                user.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, "Password changed successfully!")
                return redirect('profile')

    context = {
        'user': user,
    }
    return render(request, 'auths/settings.html', context)