from django.db import models
from django.contrib.auth import get_user_model
# Create your models here.

User = get_user_model()

class ChatSession(models.Model):
    """AI对话会话"""
    SESSION_TYPE = (
        ('consult', '咨询对话'),
        ('summary', '生成摘要'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name = 'chat_sessions')
    title = models.CharField(max_length=200, blank=True,help_text='会话标题')
    session_type = models.CharField(max_length=20,choices=SESSION_TYPE,default='consult')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'ai_chat_sessions'
        ordering = ('-updated_at',)

    def _str_(self):
        return f"{self.user.username}- {self.title or '未命名会话'}"
    

class ChatMessage(models.Model):
    """对话消息"""
    ROLE_CHOICES = [
        ('user', '用户'),
        ('assistant', 'AI助手'),
        ('system', '系统'),
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    prompt_tokens = models.IntegerField(default=0,help_text='输入token数')
    completion_tokens = models.IntegerField(default=0,help_text='输出token数')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_chat_messages'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."
    

class AIUsageLog(models.Model):
    """AI调用日志(审计用)"""
    CALL_TYPES = [
        ('chat', '对话'),
        ('summarize', '摘要生成'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE,related_name = 'ai_usage_logs')
    call_type = models.CharField(max_length=20, choices=CALL_TYPES)
    prompt_summary = models.CharField(max_length=200,help_text='Promt摘要')
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    total_tokens = models.IntegerField(default=0)
    response_time_ms = models.IntegerField(default=0, help_text='响应时间(ms)')
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'ai_usage_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.call_type} - {self.created_at}"