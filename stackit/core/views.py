from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from .forms import CustomUserCreationForm, QuestionForm, AnswerForm
from .models import Question, Answer, Tag, AnswerVote, Notification, User
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Exists, OuterRef
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import re
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.db.models import Max
import os

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('core:login')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_banned:
                    messages.error(request, 'Your account is banned.')
                else:
                    login(request, user)
                    messages.success(request, f'Welcome back, {username}!')
                    return redirect('core:question_list')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('core:question_list')

def question_list(request):
    questions = Question.objects.all()
    sort = request.GET.get('sort', '')
    search_query = request.GET.get('q', '')

    if search_query:
        questions = questions.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )
    if sort == 'newest_answered':
        questions = questions.annotate(last_answer=Max('answers__created_at')).order_by('-last_answer')
    else:
        questions = questions.order_by('-created_at')

    if request.user.is_authenticated:
        questions = questions.exclude(author=request.user)
        questions = questions.annotate(
            user_has_answered=Exists(
                Answer.objects.filter(question=OuterRef('pk'), author=request.user)
            )
        )

    # Pagination
    paginator = Paginator(questions, 4)  # Show 10 questions per page
    page = request.GET.get('page')
    try:
        questions = paginator.page(page)
    except PageNotAnInteger:
        questions = paginator.page(1)
    except EmptyPage:
        questions = paginator.page(paginator.num_pages)

    notifications = Notification.objects.filter(user=request.user, read=False).count() if request.user.is_authenticated else 0
    return render(request, 'core/question_list.html', {
        'questions': questions,
        'unread_notifications': notifications,
        'sort': sort,
        'search_query': search_query,
    })

def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    answers = question.answers.all().annotate(
        upvotes=Coalesce(Count('answervote', filter=Q(answervote__vote_type=1)), 0),
        downvotes=Coalesce(Count('answervote', filter=Q(answervote__vote_type=-1)), 0),
        net_votes=Coalesce(Count('answervote', filter=Q(answervote__vote_type=1)), 0) - Coalesce(Count('answervote', filter=Q(answervote__vote_type=-1)), 0)
    )
    # Annotate each answer with the user's vote if authenticated
    if request.user.is_authenticated:
        for answer in answers:
            vote = answer.answervote_set.filter(user=request.user).first()
            answer.user_vote = vote.vote_type if vote else None
    answer_form = AnswerForm()
    notifications = Notification.objects.filter(user=request.user, read=False).count() if request.user.is_authenticated else 0
    return render(request, 'core/question_detail.html', {
        'question': question,
        'answers': answers,
        'answer_form': answer_form,
        'unread_notifications': notifications,
    })

@login_required
def my_questions(request):
    questions = request.user.questions.all().order_by('-created_at')
    notifications = Notification.objects.filter(user=request.user, read=False).count()
    return render(request, 'core/my_questions.html', {'questions': questions, 'unread_notifications': notifications})

@login_required
def post_answer(request, pk):
    question = get_object_or_404(Question, pk=pk)
    if request.method == 'POST':
        form = AnswerForm(request.POST)
        if form.is_valid():
            answer = form.save(commit=False)
            answer.author = request.user
            answer.question = question
            answer.save()
            if question.author != request.user:
                Notification.objects.create(
                    user=question.author,
                    message=f"{request.user.username} answered your question '{question.title}'."
                )
            content = form.cleaned_data['content']
            mentions = re.findall(r'@(\w+)', content)
            for username in mentions:
                try:
                    mentioned_user = User.objects.get(username=username)
                    if mentioned_user != request.user and mentioned_user != question.author:
                        Notification.objects.create(
                            user=mentioned_user,
                            message=f"{request.user.username} mentioned you in an answer to '{question.title}'."
                        )
                except User.DoesNotExist:
                    continue
            return redirect('core:question_detail', pk=pk)
    return redirect('core:question_detail', pk=pk)

@login_required
def vote_answer(request, answer_id, vote_type):
    answer = get_object_or_404(Answer, pk=answer_id)
    existing_vote = AnswerVote.objects.filter(user=request.user, answer=answer).first()
    if existing_vote:
        if existing_vote.vote_type != vote_type:
            existing_vote.vote_type = vote_type
            existing_vote.save()
    else:
        AnswerVote.objects.create(user=request.user, answer=answer, vote_type=vote_type)
    return redirect('core:question_detail', pk=answer.question.pk)

@login_required
def accept_answer(request, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    question = answer.question
    if request.user == question.author:
        question.accepted_answer = answer
        question.save()
        if answer.author != request.user:
            Notification.objects.create(
                user=answer.author,
                message=f"Your answer to '{question.title}' has been accepted."
            )
    return redirect('core:question_detail', pk=question.pk)

@login_required
def ask_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user
            question.save()
            tags_list = form.cleaned_data['tags']
            for tag_name in tags_list:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                question.tags.add(tag)
            return redirect('core:question_detail', pk=question.pk)
    else:
        form = QuestionForm()
    notifications = Notification.objects.filter(user=request.user, read=False).count()
    return render(request, 'core/ask_question.html', {'form': form, 'unread_notifications': notifications})

@login_required
def upload_image(request):
    if request.method == 'POST' and request.FILES.get('file'):
        file = request.FILES['file']
        file_name = default_storage.save(f'images/{file.name}', file)
        file_url = default_storage.url(file_name)
        return JsonResponse({'location': file_url})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def notifications(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'core/notifications.html', {
        'notifications': notifications,
        'unread_notifications': notifications.filter(read=False).count()
    })

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, pk=notification_id, user=request.user)
    if request.method == 'POST':
        notification.read = True
        notification.save()
    return redirect('core:notifications')
