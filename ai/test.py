import json
from unittest.mock import patch
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import ChatSession, ChatMessage, AIUsageLog

User = get_user_model()


class AIAPITests(TestCase):
    """AI模块接口测试"""
    
    def setUp(self):
        """测试前置：创建用户和客户端"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = APIClient()
        
        # 获取JWT Token
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {str(refresh.access_token)}'
        )
    
    # ========== 测试会话创建 ==========
    
    def test_create_new_session(self):
        """测试：不传session_id时创建新会话"""
        response = self.client.post(
            '/api/ai/chat/',
            {'message': '你好'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ChatSession.objects.count(), 1)
        
        session = ChatSession.objects.first()
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.title, '你好')
    
    def test_use_existing_session(self):
        """测试：传session_id时使用已有会话"""
        # 先创建一个会话
        session = ChatSession.objects.create(
            user=self.user,
            title='测试会话'
        )
        
        response = self.client.post(
            '/api/ai/chat/',
            {'session_id': session.id, 'message': '继续问'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        # 会话数不变
        self.assertEqual(ChatSession.objects.count(), 1)
        # 用户消息已保存
        self.assertEqual(ChatMessage.objects.filter(role='user').count(), 1)
    
    def test_cannot_access_others_session(self):
        """测试：不能访问其他用户的会话"""
        other_user = User.objects.create_user(
            username='other',
            password='pass123'
        )
        other_session = ChatSession.objects.create(
            user=other_user,
            title='别人的会话'
        )
        
        response = self.client.post(
            '/api/ai/chat/',
            {'session_id': other_session.id, 'message': '你好'},
            format='json'
        )
        
        # 返回200但内容是错误信息（SSE格式）
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
    
    # ========== 测试参数校验 ==========
    
    def test_empty_message_error(self):
        """测试：空消息返回错误"""
        response = self.client.post(
            '/api/ai/chat/',
            {'message': ''},
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/event-stream')
    
    # ========== 测试摘要接口 ==========
    
    @patch('ai.views.AIService.generate_summary')
    def test_generate_summary_success(self, mock_generate_summary):
        """测试：摘要生成成功"""
        # Mock AI返回
        mock_generate_summary.return_value = '这是摘要'
        
        response = self.client.post(
            '/api/ai/summarize/',
            {'content': '这是一篇很长的文章...', 'max_length': 50},
            format='json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['summary'], '这是摘要')
        
        # 验证日志记录
        log = AIUsageLog.objects.first()
        self.assertEqual(log.call_type, 'summarize')
        self.assertTrue(log.success)
    
    def test_summary_empty_content_error(self):
        """测试：空文章内容返回400"""
        response = self.client.post(
            '/api/ai/summarize/',
            {'content': ''},
            format='json'
        )
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('error', response.data)
    
    # ========== 测试权限 ==========
    
    def test_chat_requires_auth(self):
        """测试：未登录不能访问对话接口"""
        # 清除认证
        self.client.credentials()
        
        response = self.client.post(
            '/api/ai/chat/',
            {'message': '你好'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 401)
    
    def test_summary_requires_auth(self):
        """测试：未登录不能访问摘要接口"""
        self.client.credentials()
        
        response = self.client.post(
            '/api/ai/summarize/',
            {'content': '文章内容'},
            format='json'
        )
        
        self.assertEqual(response.status_code, 401)
