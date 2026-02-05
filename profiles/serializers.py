from rest_framework import serializers
from .models import Profile

class ProfileSerializer(serializers.ModelSerializer):
    """个人资料序列化器 - 用于展示"""

    # 添加用户信息字段（只读）
    username = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = [
            'id','username','email','avatar','nickname',
            'bio','website','location','birth_date',
            'gender','created_at','updated_at'
        ]
        read_only_fields = ['id','created_at','updated_at']

    def get_username(self, obj):
        """获取用户名"""
        return obj.user.username
    
    def get_email(self, obj):
        """获取邮箱"""
        return obj.user.email


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """个人资料更新序列化器 - 用于修改"""

    # 昵称验证
    nickname = serializers.CharField(
        max_length=50, 
        allow_blank=True,
        required=False,
        error_messages={
            'max_length': '昵称长度不能超过50个字符',
        }
    )

    # 简介验证
    bio = serializers.CharField(
        max_length=500, 
        allow_blank=True,
        required=False,
        error_messages={
            'max_length': '个人简介长度不能超过500个字符',
        }
    )

    # 网址验证

    website = serializers.URLField(
        allow_blank=True,
        required=False,
        error_messages={
            'invalid': '请输入有效的网址',
        }
    )

    class Meta:
        model = Profile
        fields = [
            'avatar','nickname','bio','website',
            'location','birth_date','gender'
        ]
    

    def validate_nickname(self,value):
        """自定义昵称验证"""
        # value.strip()去除前后空格
        if value and len(value.strip()) == 0:
            raise serializers.ValidationError('昵称不能为空')
        return value.strip()
    
    def validate_bio(self, value):
        """自定义简介验证"""
        if value and len(value.strip()) == 0:
            raise serializers.ValidationError('简介不能为空')
        return value.strip()