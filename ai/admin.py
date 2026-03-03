from django.contrib import admin
from .models import ChatSession, ChatMessage, AIUsageLog


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    """对话会话管理"""
    list_display = ['id', 'user', 'title', 'session_type', 'created_at', 'updated_at']
    list_filter = ['session_type', 'created_at']
    search_fields = ['title', 'user__username']
    date_hierarchy = 'created_at'
    ordering = ['-updated_at']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    """对话消息管理"""
    list_display = ['id', 'session', 'role', 'content', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content', 'session__title']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']


@admin.register(AIUsageLog)
class AIUsageLogAdmin(admin.ModelAdmin):
    """AI使用日志管理"""
    list_display = ['id', 'user', 'call_type', 'success', 'created_at']
    list_filter = ['call_type', 'success', 'created_at']
    search_fields = ['user__username', 'prompt_summary', 'error_message']
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
