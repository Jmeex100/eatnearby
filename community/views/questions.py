from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from ..models import RestaurantQuestion, RestaurantAnswer, Restaurant
from django.http import HttpResponseRedirect
from django.urls import reverse

# List questions for a restaurant or create a new question
@login_required
def question_list_create(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
    
    if request.method == 'POST':
        question_text = request.POST.get('question')

        # Create question
        question = RestaurantQuestion(
            user=request.user,
            restaurant=restaurant,
            question=question_text
        )
        question.save()

        messages.success(request, 'Question submitted successfully!')
        return HttpResponseRedirect(reverse('community:question-detail', args=[question.pk]))

    questions = RestaurantQuestion.objects.filter(restaurant=restaurant).select_related('user', 'answer__responder').order_by('-created_at')
    context = {
        'restaurant': restaurant,
        'questions': questions,
    }
    return render(request, 'questions/question_list_create.html', context)

# Detail view for a specific question
def question_detail(request, pk):
    question = get_object_or_404(RestaurantQuestion, pk=pk)
    answer = question.answer if hasattr(question, 'answer') else None
    context = {
        'question': question,
        'answer': answer,
    }
    return render(request, 'questions/question_detail.html', context)

# Edit an existing question
@login_required
def question_edit(request, pk):
    question = get_object_or_404(RestaurantQuestion, pk=pk, user=request.user)
    
    if question.is_answered:
        messages.error(request, 'Cannot edit a question that has been answered.')
        return HttpResponseRedirect(reverse('community:question-detail', args=[question.pk]))

    if request.method == 'POST':
        question_text = request.POST.get('question')

        # Update question
        question.question = question_text
        question.save()

        messages.success(request, 'Question updated successfully!')
        return HttpResponseRedirect(reverse('community:question-detail', args=[question.pk]))

    context = {
        'question': question,
    }
    return render(request, 'questions/question_form.html', context)

# Delete a question
@login_required
def question_delete(request, pk):
    question = get_object_or_404(RestaurantQuestion, pk=pk, user=request.user)
    
    if question.is_answered:
        messages.error(request, 'Cannot delete a question that has been answered.')
        return HttpResponseRedirect(reverse('community:question-detail', args=[question.pk]))

    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return HttpResponseRedirect(reverse('community:restaurant-detail', args=[question.restaurant.pk]))

    context = {
        'question': question,
    }
    return render(request, 'questions/question_confirm_delete.html', context)