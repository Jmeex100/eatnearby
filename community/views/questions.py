from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.urls import reverse
from ..models import Restaurant, RestaurantQuestion, RestaurantAnswer ,User
from ..forms import QuestionForm, AnswerForm

def question_list_create(request, restaurant_id=None):
    restaurant = None
    if restaurant_id:
        restaurant = get_object_or_404(Restaurant, pk=restaurant_id)
        questions = RestaurantQuestion.objects.filter(restaurant=restaurant).select_related('user', 'restaurant', 'answer__responder').order_by('-created_at')
    else:
        questions = RestaurantQuestion.objects.all().select_related('user', 'restaurant', 'answer__responder').order_by('-created_at')
    
    restaurants = Restaurant.objects.all()
    if not restaurants.exists() and not restaurant:
        messages.error(request, 'No restaurants available to ask a question.')
        return render(request, 'questions/question_list_create.html', {
            'restaurant': restaurant,
            'questions': questions,
            'restaurants': restaurants,
            'form': QuestionForm(),
        })

    form = QuestionForm(initial={'restaurant': restaurant} if restaurant else {})

    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to ask a question.')
            return redirect('login')
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.user = request.user
            if restaurant:
                question.restaurant = restaurant
            else:
                if form.cleaned_data['restaurant']:
                    question.restaurant = form.cleaned_data['restaurant']
                else:
                    form.add_error('restaurant', 'Please select a restaurant.')
                    messages.error(request, 'Please select a restaurant.')
                    context = {
                        'restaurant': restaurant,
                        'questions': questions,
                        'restaurants': restaurants,
                        'form': form,
                    }
                    return render(request, 'questions/question_list_create.html', context)
            question.save()
            messages.success(request, 'Question submitted successfully!')
            return HttpResponseRedirect(reverse('community:question-detail', args=[question.pk]))
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'restaurant': restaurant,
        'questions': questions,
        'restaurants': restaurants,
        'form': form,
    }
    return render(request, 'questions/question_list_create.html', context)

def question_detail(request, pk):
    question = get_object_or_404(RestaurantQuestion, pk=pk)
    answer = question.answer if hasattr(question, 'answer') else None
    form = None
    if request.user.is_authenticated and not question.is_answered and request.user.user_type in ['admin', 'staff']:
        if request.user.user_type == 'staff' and question.restaurant != request.user.restaurant:
            form = None  # Staff can only answer for their own restaurant
        else:
            form = AnswerForm()
    context = {
        'question': question,
        'answer': answer,
        'form': form,
    }
    return render(request, 'questions/question_detail.html', context)

@login_required
def question_edit(request, pk):
    question = get_object_or_404(RestaurantQuestion, pk=pk, user=request.user)
    
    if question.is_answered:
        messages.error(request, 'Cannot edit a question that has been answered.')
        return HttpResponseRedirect(reverse('community:question-detail', args=[question.pk]))

    form = QuestionForm(instance=question)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, 'Question updated successfully!')
            return HttpResponseRedirect(reverse('community:question-detail', args=[question.pk]))
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'question': question,
        'form': form,
    }
    return render(request, 'questions/question_form.html', context)

@login_required
def question_delete(request, pk):
    question = get_object_or_404(RestaurantQuestion, pk=pk, user=request.user)
    
    if question.is_answered:
        messages.error(request, 'Cannot delete a question that has been answered.')
        return HttpResponseRedirect(reverse('community:question-detail', args=[question.pk]))

    if request.method == 'POST':
        restaurant_id = question.restaurant.pk
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return HttpResponseRedirect(reverse('community:restaurant-detail', args=[restaurant_id]))

    context = {
        'question': question,
    }
    return render(request, 'questions/question_confirm_delete.html', context)

@login_required
def answer_create(request, question_id):
    question = get_object_or_404(RestaurantQuestion, pk=question_id)
    if request.user.user_type == 'staff' and question.restaurant != request.user.restaurant:
        raise PermissionDenied("You are not authorized to answer questions for this restaurant.")
    if request.user.user_type not in ['admin', 'staff']:
        raise PermissionDenied("Only staff or admins can answer questions.")
    if question.is_answered:
        messages.error(request, 'This question already has an answer.')
        return redirect('community:question-detail', pk=question_id)
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.question = question
            answer.responder = request.user
            answer.save()
            question.is_answered = True
            question.save()
            messages.success(request, 'Answer submitted successfully!')
            return redirect('community:question-detail', pk=question_id)
    else:
        form = AnswerForm()
    return render(request, 'questions/answer_form.html', {'form': form, 'question': question})

@login_required
def answer_edit(request, pk):
    answer = get_object_or_404(RestaurantAnswer, pk=pk)
    if request.user != answer.responder and request.user.user_type != 'admin':
        raise PermissionDenied("You are not authorized to edit this answer.")
    if request.method == 'POST':
        form = AnswerForm(request.POST, instance=answer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Answer updated successfully!')
            return redirect('community:question-detail', pk=answer.question.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = AnswerForm(instance=answer)
    return render(request, 'questions/answer_form.html', {'form': form, 'question': answer.question})

@login_required
def answer_delete(request, pk):
    answer = get_object_or_404(RestaurantAnswer, pk=pk)
    if request.user != answer.responder and request.user.user_type != 'admin':
        raise PermissionDenied("You are not authorized to delete this answer.")
    if request.method == 'POST':
        question_id = answer.question.pk
        answer.question.is_answered = False
        answer.question.save()
        answer.delete()
        messages.success(request, 'Answer deleted successfully!')
        return redirect('community:question-detail', pk=question_id)
    return render(request, 'questions/answer_confirm_delete.html', {'answer': answer})