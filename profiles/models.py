from django.db import models
from django.contrib.auth.models import User
# Create your models here.

class Profile(models.Model):
    """用户个人资料模型"""
    # 一个用户对应一个个人资料
    user = models.OneToOneField(
        User,
        # 级联删除 即删除用户同时删除表
        on_delete=models.CASCADE,
        # 可以通过user.profile访问
        related_name='profile',
        verbose_name='用户'
    )

    avatar = models.ImageField(
        # 图片按日期分目录存储
        upload_to='avatars/%Y/%m/%d/', 
        # blank=True 表示表单中允许为空
        blank=True, 
        # null=True 表示数据库中允许为空
        null=True,
        verbose_name='头像'
    )
    nickname = models.CharField(
        max_length=50, 
        blank=True,
        verbose_name='昵称'
    )
    bio = models.TextField(
        max_length=500, 
        blank=True,
        verbose_name='个人简介'
    )
    website = models.URLField(
        blank=True,
        verbose_name='个人网站'
    )
    location = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='所在地'
    )
    birth_date = models.DateField(
        blank=True, 
        null=True,
        verbose_name='出生日期'
    )
    gender = models.CharField(
        max_length=10, 
        choices=[('male', '男'), ('female', '女'), ('other', '其他')],
        blank=True,
        verbose_name='性别'
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
    db_table = 'profiles_profile'
    verbose_name = '用户资料'
    verbose_name_plural = '用户资料'
def __str__(self):
        return f"{self.user.username} 的个人资料"