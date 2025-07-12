from django.urls import path
from . import views
from django.urls import re_path

app_name = 'core'  # Define the namespace

urlpatterns = [
    path('', views.question_list, name='question_list'),
    path('question/<int:pk>/', views.question_detail, name='question_detail'),
    path('ask/', views.ask_question, name='ask_question'),
    path('question/<int:pk>/answer/', views.post_answer, name='post_answer'),
    re_path(r'^answer/(?P<answer_id>\d+)/vote/(?P<vote_type>-?\d+)/$', views.vote_answer, name='vote_answer'),
    path('answer/<int:answer_id>/accept/', views.accept_answer, name='accept_answer'),
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('notifications/', views.notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('upload_image/', views.upload_image, name='upload_image'),
    path('my-questions/', views.my_questions, name='my_questions'),
]