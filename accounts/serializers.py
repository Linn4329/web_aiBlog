# \blog\serializers.py

# 导入DRF的序列化器模块
from rest_framework import serializers

# 导入django用户模型获取函数
from django.contrib.auth import get_user_model

User = get_user_model()

# 创建用户注册序列化器
class UserRegisterSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(required = True, write_only=True)
    #嵌套的配置类，定义序列化器的元数据。
    class Meta:
        # 指定关联的 Django 模型。
        model = User
        # password：密码（模型字段）  password_confirm：确认密码（自定义字段，不在模型中）
        # 只包含必要字段
        fields = ['id','username','email','password','password_confirm']

        # 为已有字段添加额外配置
        extra_kwargs = {
            'password':{
                'write_only':True,  # 只允许写入(不返回给前端)
                'min_length':6, 
                'error_messages':{
                'min_length':'密码长度不能小于6位',
                }
            },
            'email':{
                'required':True,
                'error_messages':{
                'required':'邮箱不能为空！',
                'invalid':'邮箱格式错误！',
                }
            }
        }

    # 字段级验证只能访问一个字段 如validate_username 只能访问 username
    # 当所有的字段级验证完成后才执行全局验证
    # 这个方法可以访问所有字段，比较多个字段的值

    # self 指序列化器对象实例本身， attrs 是经过字段级验证后的数据字典即符合要求的数据字典
    def validate(self, attrs):
        # 全局验证两次输入的密码
        if attrs['password'] != attrs['password_confirm']: 
            raise serializers.ValidationError({
                'password':'两次输入的密码不一致！'
            })
        attrs.pop('password_confirm')
        # attrs会传递给 create方法
        return attrs
    
    def create(self,validated_data):
        # User.objects用户模型的管理器,提供 create()、get()、filter() 等方法
        # Django 内置方法，专门用于创建用户。
        # create()不加密密码 而 create_user()自动加密密码
        # **validated_data  ** 是解包操作符（两个星号） 将字典展开成关键字参数，自动匹配参数名

        user = User.objects.create_user(**validated_data)

        return user
    
# 用户信息序列化器
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id','username','email','first_name','last_name','data_joined']
        # 只读部分不会被修改
        read_only_fields = ['id','data_joined']