from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils.text import slugify
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.forms import ModelForm
from ..models import Challenge, ChallengeParticipation, User, Post
from datetime import date
from ..models import Challenge, ChallengeParticipation
import logging

# Configure logging
logger = logging.getLogger(__name__)
# Challenge Form for cleaner validation
class ChallengeForm(ModelForm):
    class Meta:
        model = Challenge
        fields = ['title', 'description', 'start_date', 'end_date', 'banner_image', 'is_active']
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and end_date < start_date:
            raise ValidationError("End date cannot be before start date.")
        
        if start_date and start_date < date.today():
            raise ValidationError("Start date cannot be in the past.")
        
        return cleaned_data

# List all active challenges
def challenge_list(request):
    challenges = Challenge.objects.filter(is_active=True).order_by('-created_at')
    return render(request, 'challenges/challenge_list.html', {'challenges': challenges})

# Detail view for a specific challenge
def challenge_detail(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    participations = ChallengeParticipation.objects.filter(challenge=challenge).select_related('user', 'post')
    return render(request, 'challenges/challenge_detail.html', {
        'challenge': challenge,
        'participations': participations,
    })

# Create a new challenge
@login_required
def challenge_create(request):
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to create a challenge.")

    if request.method == 'POST':
        form = ChallengeForm(request.POST, request.FILES)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.slug = slugify(form.cleaned_data['title'])
            challenge.created_by = request.user  # Track who created the challenge
            challenge.save()
            messages.success(request, 'Challenge created successfully!')
            return HttpResponseRedirect(reverse('community:challenge-detail', args=[challenge.pk]))
    else:
        form = ChallengeForm(initial={'is_active': True})

    return render(request, 'challenges/challenge_form.html', {'form': form})

# Edit an existing challenge
@login_required
def challenge_edit(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to edit this challenge.")

    if request.method == 'POST':
        form = ChallengeForm(request.POST, request.FILES, instance=challenge)
        if form.is_valid():
            challenge = form.save(commit=False)
            challenge.slug = slugify(form.cleaned_data['title'])
            challenge.updated_by = request.user  # Track who updated the challenge
            challenge.save()
            messages.success(request, 'Challenge updated successfully!')
            return HttpResponseRedirect(reverse('community:challenge-detail', args=[challenge.pk]))
    else:
        form = ChallengeForm(instance=challenge)

    return render(request, 'challenges/challenge_form.html', {'form': form, 'challenge': challenge})

# Delete a challenge
@login_required
def challenge_delete(request, pk):
    challenge = get_object_or_404(Challenge, pk=pk)
    if not request.user.is_staff:
        raise PermissionDenied("You do not have permission to delete this challenge.")

    if request.method == 'POST':
        challenge.delete()
        messages.success(request, 'Challenge deleted successfully!')
        return HttpResponseRedirect(reverse('community:challenge-list'))

    return render(request, 'challenges/challenge_confirm_delete.html', {'challenge': challenge})

# Submit a challenge entry
logger = logging.getLogger(__name__)

@login_required
def challenge_entry(request, challenge_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    if not challenge.is_active:
        messages.error(request, 'This challenge is no longer active.')
        logger.error(f"Challenge {challenge.id} is inactive, user {request.user.username} attempted to join.")
        return redirect('community:challenge-detail', pk=challenge.pk)

    if ChallengeParticipation.objects.filter(challenge=challenge, user=request.user).exists():
        messages.error(request, 'You have already joined this challenge.')
        logger.error(f"User {request.user.username} attempted to join challenge {challenge.id} multiple times.")
        return redirect('community:challenge-detail', pk=challenge.pk)

    if request.method == 'POST':
        participation = ChallengeParticipation(
            challenge=challenge,
            user=request.user,
            post=None,  # Explicitly set to None
            completed=False
        )
        participation.save()
        messages.success(request, 'You have successfully joined the challenge!')
        logger.info(f"User {request.user.username} joined challenge {challenge.id}.")
        return redirect('community:challenge-detail', pk=challenge.pk)

    return render(request, 'challenges/challenge_entry_form.html', {
        'challenge': challenge,
    })
@login_required
def challenge_mark_completed(request, challenge_id, participation_id):
    challenge = get_object_or_404(Challenge, pk=challenge_id)
    participation = get_object_or_404(ChallengeParticipation, pk=participation_id, challenge=challenge)
    if not request.user.is_staff:
        raise PermissionDenied("Only staff can mark participations as completed.")
    if request.method == 'POST':
        participation.completed = True
        participation.save()
        messages.success(request, 'Participation marked as completed.')
        return HttpResponseRedirect(reverse('community:challenge-detail', args=[challenge.pk]))
    return render(request, 'challenges/challenge_mark_completed.html', {
        'challenge': challenge,
        'participation': participation,
    })


# Delete a challenge entry
@login_required
def challenge_entry_delete(request, pk, participation_id):
    challenge = get_object_or_404(Challenge, pk=pk)
    participation = get_object_or_404(ChallengeParticipation, pk=participation_id, challenge=challenge)
    
    if participation.user != request.user and not request.user.is_staff:
        raise PermissionDenied("You do not have permission to delete this entry.")

    if request.method == 'POST':
        participation.delete()
        messages.success(request, 'Your entry has been deleted successfully!')
        return HttpResponseRedirect(reverse('community:challenge-detail', args=[challenge.pk]))

    return render(request, 'challenges/challenge_entry_confirm_delete.html', {
        'challenge': challenge,
        'participation': participation,
    })