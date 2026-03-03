from rest_framework import serializers
from .models import ChatSession, ChatMessage, AIUsageLog


class ChatMessageSerializer(serializers.ModelSerializer):
    """对话消息序列化器"""

    class Meta:
        model = ChatMessage
        fields = ['id', 'session', 'role', 'content', 'prompt_tokens', 
                  'completion_tokens', 'created_at']
        read_only_fields = ['id', 'created_at']


class ChatSessionSerializer(serializers.ModelSerializer):
    """对话会话序列化器"""
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = ChatSession
        fields = ['id', 'user', 'title', 'session_type', 'created_at', 
                  'updated_at', 'messages']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ChatSessionListSerializer(serializers.ModelSerializer):
    """会话列表序列化器（不包含消息详情）"""
    last_message = serializers.SerializerMethodField()
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = ['id', 'title', 'session_type', 'created_at', 
                  'updated_at', 'last_message', 'message_count']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_last_message(self, obj):
        """获取最后一条消息"""
        last_msg = obj.messages.order_by('-created_at').first()
        if last_msg:
            return {
                'content': last_msg.content[:100],
                'role': last_msg.role,
                'created_at': last_msg.created_at
            }
        return None

    def get_message_count(self, obj):
        """获取消息数量"""
        return obj.messages.count()


class AIUsageLogSerializer(serializers.ModelSerializer):
    """AI使用日志序列化器"""

    class Meta:
        model = AIUsageLog
        fields = ['id', 'user', 'call_type', 'prompt_summary', 
                  'prompt_tokens', 'completion_tokens', 'total_tokens',
                  'response_time_ms', 'success', 'error_message', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']
