from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Tag(models.Model):
    """标签模型"""
    name = models.CharField(
        max_length=50, 
        unique=True,
        verbose_name='标签名称'
    )

    # Django 特殊字段类型，只允许字母、数字、下划线、连字符
    slug = models.SlugField(
        max_length=50,
        unique=True,
        verbose_name='URL标识符'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    class Meta:
        db_table = 'blog_tag'
        verbose_name = '标签'
        verbose_name_plural = '标签'
        ordering = ['-created_at']

    # 返回标签名
    def __str__(self):
        return self.name
    
class Post(models.Model):
    """文章模型"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('archived', '已归档'),
    ]

    title = models.CharField(
        max_length=200,
        verbose_name='标题'
    )

    # ForeignKey（外键）：多对一关系，多篇文章属于一个用户
    author = models.ForeignKey(
        User,
        # 级联删除
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='作者'
    )
    content = models.TextField(
        verbose_name='正文内容'
    )
    excerpt = models.CharField(
        max_length=500,
        verbose_name='摘要'
    )
    cover_image = models.ImageField(
        upload_to='covers/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name='封面图'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name='状态'
    )
    view_count = models.IntegerField(
        default=0,
        verbose_name='浏览量'
    )
    
    # 多对多，一个文章有多个标签，多个标签也可以对应一个文章
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        verbose_name='标签'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='创建时间'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='更新时间'
    )

    class Meta:
        db_table = 'blog_post'
        verbose_name = '文章'
        verbose_name_plural = '文章'

        # ordering=['-created_at']：文章列表默认按创建时间倒序，最新的在前
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    
