from django.urls import path
from . import views

urlpatterns = [
    path('', views.question_list, name='question_list'),
    path('question/<int:pk>/', views.question_detail, name='question_detail'),
    path('ask/', views.ask_question, name='ask_question'),
    path('question/<int:pk>/answer/', views.post_answer, name='post_answer'),
    path('answer/<int:answer_id>/vote/<int:vote_type>/', views.vote_answer, name='vote_answer'),
    path('answer/<int:answer_id>/accept/', views.accept_answer, name='accept_answer'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]