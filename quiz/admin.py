from django.contrib import admin
from .models import Question


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "question_text", "answer", "difficulty")
    list_filter = ("difficulty", "answer")
    search_fields = ("question_text",)