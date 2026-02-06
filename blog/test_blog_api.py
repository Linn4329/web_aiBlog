import json
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from .models import Tag, Post

User = get_user_model()


class TagAPITest(APITestCase):
    """标签 API 测试"""
    
    def setUp(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_get_tags_public(self):
        """测试：匿名用户可以获取标签列表"""
        # 创建标签
        tag = Tag.objects.create(name='Python', slug='python')
        
        # 未登录访问
        response = self.client.get('/api/blog/tags/')
        
        # 验证
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data['tags']), 1)
        self.assertEqual(response.data['message'], '获取标签列表成功')
    
    def test_create_tag_authenticated(self):
        """测试：登录用户可以创建标签"""
        # 模拟登录
        self.client.force_authenticate(user=self.user)
        
        data = {'name': 'Django'}
        response = self.client.post('/api/blog/tags/', data)
        
        # 验证
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['tag']['name'], 'Django')
        self.assertEqual(response.data['message'], '创建标签成功')
    
    def test_create_tag_unauthenticated(self):
        """测试：未登录用户不能创建标签"""
        data = {'name': 'Test'}
        response = self.client.post('/api/blog/tags/', data)
        
        # 验证：返回 401
        self.assertEqual(response.status_code, 401)
        self.assertIn('请先登录', response.data['message'])
    
    def test_create_duplicate_tag(self):
        """测试：创建重复标签返回 400"""
        # 创建标签
        Tag.objects.create(name='Python', slug='python')
        self.client.force_authenticate(user=self.user)
        
        data = {'name': 'Python'}
        response = self.client.post('/api/blog/tags/', data)
        
        # 验证：返回 400
        self.assertEqual(response.status_code, 400)
        self.assertIn('该标签已存在', response.data['error']['name'][0])


class PostAPITest(APITestCase):
    """文章 API 测试"""
    
    def setUp(self):
        """每个测试前执行"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        # 创建标签
        self.tag1 = Tag.objects.create(name='Python', slug='python')
        self.tag2 = Tag.objects.create(name='Django', slug='django')
        # 创建文章
        self.post = Post.objects.create(
            title='Django 入门',
            content='内容...',
            excerpt='Django 是 Python 的 Web 框架',
            author=self.user,
            status='published',
            view_count=10
        )
        self.post.tags.add(self.tag1, self.tag2)
    
    def test_get_posts_public(self):
        """测试：匿名用户可以获取已发布文章列表"""
        response = self.client.get('/api/blog/posts/')
        
        # 验证
        self.assertEqual(response.status_code, 200)
        self.assertGreater(len(response.data['posts']), 0)
        self.assertEqual(response.data['message'], '获取文章列表成功')
    
    def test_create_post_authenticated(self):
        """测试：登录用户可以创建文章"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': 'Python 进阶',
            'content': 'Python 高级内容...',
            'excerpt': 'Python 高级技巧',
            'status': 'draft'
        }
        response = self.client.post('/api/blog/posts/', data)
        
        # 验证
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['post']['title'], 'Python 进阶')
        self.assertEqual(response.data['post']['author'], self.user.username)
        self.assertEqual(response.data['post']['status'], 'draft')
    
    def test_create_post_unauthenticated(self):
        """测试：未登录用户不能创建文章"""
        data = {'title': 'Test'}
        response = self.client.post('/api/blog/posts/', data)
        
        # 验证：返回 401
        self.assertEqual(response.status_code, 401)
        self.assertIn('请先登录', response.data['message'])
    
    def test_create_post_missing_title(self):
        """测试：创建文章时标题为空返回 400"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'content': '内容...',
            'excerpt': '摘要...'
        }
        response = self.client.post('/api/blog/posts/', data)
        
        # 验证：返回 400
        self.assertEqual(response.status_code, 400)
        self.assertIn('标题不能为空', response.data['error']['title'][0])
    
    def test_create_post_short_excerpt(self):
        """测试：摘要少于 10 字符返回 400"""
        self.client.force_authenticate(user=self.user)
        
        data = {
            'title': '标题',
            'content': '内容...',
            'excerpt': '太短'
        }
        response = self.client.post('/api/blog/posts/', data)
        
        # 验证：返回 400
        self.assertEqual(response.status_code, 400)
        self.assertIn('摘要至少需要 10 个字符', response.data['error']['excerpt'][0])
    
    def test_get_post_detail_public(self):
        """测试：匿名用户可以获取文章详情"""
        response = self.client.get(f'/api/blog/posts/{self.post.id}/')
        
        # 验证
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['post']['id'], self.post.id)
        # 验证浏览量增加了
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, 11)  # 原来 10，访问后 +1
    
    def test_get_nonexistent_post(self):
        """测试：获取不存在的文章返回 404"""
        response = self.client.get('/api/blog/posts/99999/')
        
        # 验证：返回 404
        self.assertEqual(response.status_code, 404)
        self.assertIn('文章不存在', response.data['message'])
    
    def test_update_post_by_author(self):
        """测试：作者本人可以更新文章"""
        self.client.force_authenticate(user=self.user)
        
        data = {'title': '更新后的标题'}
        response = self.client.put(f'/api/blog/posts/{self.post.id}/', data)
        
        # 验证
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['post']['title'], '更新后的标题')
        # 验证数据库已更新
        self.post.refresh_from_db()
        self.assertEqual(self.post.title, '更新后的标题')
    
    def test_update_post_by_other(self):
        """测试：他人不能更新文章"""
        self.client.force_authenticate(user=self.other_user)
        
        data = {'title': '恶意修改'}
        response = self.client.put(f'/api/blog/posts/{self.post.id}/', data)
        
        # 验证：返回 403
        self.assertEqual(response.status_code, 403)
        self.assertIn('无权修改他人的文章', response.data['message'])
    
    def test_patch_post_by_author(self):
        """测试：作者本人可以部分更新文章"""
        self.client.force_authenticate(user=self.user)
        
        data = {'status': 'published'}
        response = self.client.patch(f'/api/blog/posts/{self.post.id}/', data)
        
        # 验证
        self.assertEqual(response.status_code, 200)
        self.post.refresh_from_db()
        self.assertEqual(self.post.status, 'published')
    
    def test_delete_post_by_author(self):
        """测试：作者本人可以删除文章"""
        self.client.force_authenticate(user=self.user)
        
        response = self.client.delete(f'/api/blog/posts/{self.post.id}/')
        
        # 验证
        self.assertEqual(response.status_code, 200)
        self.assertIn('删除文章成功', response.data['message'])
        # 验证文章已删除
        self.assertFalse(Post.objects.filter(id=self.post.id).exists())
    
    def test_delete_post_by_other(self):
        """测试：他人不能删除文章"""
        self.client.force_authenticate(user=self.other_user)
        
        response = self.client.delete(f'/api/blog/posts/{self.post.id}/')
        
        # 验证：返回 403
        self.assertEqual(response.status_code, 403)
        self.assertIn('无权修改他人的文章', response.data['message'])
