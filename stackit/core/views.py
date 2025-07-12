from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Question, Answer, Tag, AnswerVote, Notification
from .forms import QuestionForm, AnswerForm, CustomUserCreationForm
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from core import models

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
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
                    return redirect('question_list')
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
    return redirect('question_list')


def question_list(request):
    questions = Question.objects.all().order_by('-created_at')
    return render(request, 'core/question_list.html', {'questions': questions})

def question_detail(request, pk):
    question = get_object_or_404(Question, pk=pk)
    answers = question.answers.all().annotate(
        upvotes=models.Count('answervote', filter=models.Q(answervote__vote_type=1)),
        downvotes=models.Count('answervote', filter=models.Q(answervote__vote_type=-1))
    )
    answer_form = AnswerForm()
    return render(request, 'core/question_detail.html', {
        'question': question,
        'answers': answers,
        'answer_form': answer_form,
    })

@login_required
def ask_question(request):
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            question = form.save(commit=False)
            question.author = request.user
            question.save()
            # Handle tags
            tags_list = form.cleaned_data['tags']
            for tag_name in tags_list:
                tag, created = Tag.objects.get_or_create(name=tag_name)
                question.tags.add(tag)
            return redirect('question_detail', pk=question.pk)
    else:
        form = QuestionForm()
    return render(request, 'core/ask_question.html', {'form': form})

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
            # Notify question owner
            Notification.objects.create(
                user=question.author,
                message=f"{request.user.username} answered your question '{question.title}'."
            )
            return redirect('question_detail', pk=pk)
    return redirect('question_detail', pk=pk)

@login_required
def vote_answer(request, answer_id, vote_type):
    answer = get_object_or_404(Answer, pk=answer_id)
    vote, created = AnswerVote.objects.get_or_create(user=request.user, answer=answer)
    vote.vote_type = vote_type
    vote.save()
    return redirect('question_detail', pk=answer.question.pk)

@login_required
def accept_answer(request, answer_id):
    answer = get_object_or_404(Answer, pk=answer_id)
    question = answer.question
    if request.user == question.author:
        question.accepted_answer = answer
        question.save()
        # Notify answer author
        Notification.objects.create(
            user=answer.author,
            message=f"Your answer to '{question.title}' has been accepted."
        )
    return redirect('question_detail', pk=question.pk)
