from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Create your models here.
class User(AbstractUser):
    is_banned = models.BooleanField(default=False)

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Question(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='questions')
    tags = models.ManyToManyField(Tag, related_name='questions')
    created_at = models.DateTimeField(default=timezone.now)
    accepted_answer = models.OneToOneField('Answer', null=True, blank=True, on_delete=models.SET_NULL, related_name='+')

    def __str__(self):
        return self.title

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='answers')
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    votes = models.ManyToManyField(User, through='AnswerVote', related_name='answer_votes')

    def __str__(self):
        return f'Answer to {self.question.title}'

class AnswerVote(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE)
    vote_type = models.SmallIntegerField()  # +1 for upvote, -1 for downvote

    class Meta:
        unique_together = ('user', 'answer')

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    read = models.BooleanField(default=False)