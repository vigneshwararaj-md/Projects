# tutor/admin.py

from django.contrib import admin
from .models import Document, Conversation

# Register your models here
@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'uploaded_at']
    list_filter = ['uploaded_at']
    search_fields = ['title']

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['user', 'document', 'question_preview', 'created_at']
    list_filter = ['created_at', 'document']
    search_fields = ['question', 'answer']
    
    def question_preview(self, obj):
        """Show first 50 characters of question"""
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'