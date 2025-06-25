from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from .views.restaurants import restaurant,chatbot, restaurant_list, restaurant_detail, restaurant_edit, restaurant_delete

from .views.posts import post_list_create, post_detail, post_edit, post_delete, rating_create, rating_edit, post_like, comment_like, comment_create
# from .views.ratings import rating_create, rating_edit
# from .views.comments import comment_list_create, comment_edit, comment_delete, comment_reply

from .views.challenges import challenge_list, challenge_detail, challenge_create, challenge_edit, challenge_delete, challenge_entry, challenge_entry_delete, challenge_mark_completed
from .views.recipes import recipe_list_create, recipe_detail, recipe_edit, recipe_delete
from .views.questions import question_list_create, question_detail, question_edit, question_delete
# from .views.answers import answer_create, answer_edit, answer_delete

app_name = 'community'


  
urlpatterns = [
    # Restaurant URLs
    path('', restaurant, name='restaurant'),
    path('chatbot/', chatbot, name='chatbot'),
    path('restaurants/', restaurant_list, name='restaurant-list'),
    path('restaurants/<int:pk>/', restaurant_detail, name='restaurant-detail'),
    path('restaurants/<int:pk>/edit/', restaurant_edit, name='restaurant-edit'),
    path('restaurants/<int:pk>/delete/', restaurant_delete, name='restaurant-delete'),

   
 # Post URLs
    path('posts/', post_list_create, name='post-list-create'),
    path('posts/<int:pk>/', post_detail, name='post-detail'),
    path('posts/<int:pk>/edit/', post_edit, name='post-edit'),
    path('posts/<int:pk>/delete/', post_delete, name='post-delete'),

    # Rating URLs (tied to posts)
    path('posts/<int:post_id>/rate/', rating_create, name='rating-create'),
    path('posts/<int:post_id>/rate/edit/', rating_edit, name='rating-edit'),

    # Comment URLs
    path('posts/<int:pk>/comment/', comment_create, name='comment-create'),
    path('posts/<int:pk>/like/', post_like, name='post-like'),
    path('comments/<int:pk>/like/', comment_like, name='comment-like'),

   # Challenge URLs
    path('challenges/', challenge_list, name='challenge-list'),
    path('challenges/<int:pk>/', challenge_detail, name='challenge-detail'),
    path('challenges/create/', challenge_create, name='challenge-create'),
    path('challenges/<int:pk>/edit/', challenge_edit, name='challenge-edit'),
    path('challenges/<int:pk>/delete/', challenge_delete, name='challenge-delete'),
    # Challenge Entry URLs
    path('challenges/<int:challenge_id>/enter/', challenge_entry, name='challenge-entry'),
    path('challenges/<int:pk>/entries/<int:participation_id>/delete/', challenge_entry_delete, name='challenge-entry-delete'),
    path('challenges/<int:challenge_id>/entries/<int:participation_id>/mark-completed/', challenge_mark_completed, name='challenge-mark-completed'),
    # Recipe URLs
    path('recipes/', recipe_list_create, name='recipe-list-create'),
    path('recipes/<int:pk>/', recipe_detail, name='recipe-detail'),
    path('recipes/<int:pk>/edit/', recipe_edit, name='recipe-edit'),
    path('recipes/<int:pk>/delete/', recipe_delete, name='recipe-delete'),

# Question (Ask the Chef) URLs
path('restaurants/<int:restaurant_id>/ask/', question_list_create, name='question-list-create'),
    path('questions/<int:pk>/', question_detail, name='question-detail'),
    path('questions/<int:pk>/edit/', question_edit, name='question-edit'),
    path('questions/<int:pk>/delete/', question_delete, name='question-delete'),
    
    # # Answer URLs
    # path('questions/<int:question_id>/answer/', answer_create, name='answer-create'),
    # path('answers/<int:pk>/edit/', answer_edit, name='answer-edit'),
    # path('answers/<int:pk>/delete/', answer_delete, name='answer-delete'),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)