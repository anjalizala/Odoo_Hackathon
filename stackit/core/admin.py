from django.contrib import admin
from .models import User, Question, Answer, Tag, AnswerVote, Notification

admin.site.register(User)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Tag)
admin.site.register(AnswerVote)
admin.site.register(Notification)
