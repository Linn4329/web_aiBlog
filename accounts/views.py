from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.shortcuts import render
from .serializers import UserRegisterSerializer, UserSerializer
# Create your views here.

User = get_user_model()

class RegisterView(APIView):
    """
    用户注册 API
    - 接收用户名、邮箱、密码、确认密码
    - 验证数据并创建用户
    - 返回用户信息（不含密码）
    """
    permission_classes = []
    def post(self, request):
        """
        处理注册请求
        """
        # 1. 使用序列化器验证数据
        serializer = UserRegisterSerializer(data=request.data)

        # 2. 验证失败，返回错误
        if not serializer.is_valid():
            return Response(
                # serializer.errors：验证失败的错误字典
                {'error':'注册失败','details':serializer.errors},
                status = status.HTTP_400_BAD_REQUEST    
            )
        
        # 3. 验证成功，保存用户
        user = serializer.save()

        # 4. 返回用户信息
        response_data = {
            'message':'注册成功',
            'user':UserSerializer(user).data
        }

        return Response(response_data, status = status.HTTP_201_CREATED)
    
class LoginView(APIView):
    """
    用户登录 API
    - 接收用户名/邮箱、密码
    - 验证凭据
    - 返回 access_token 和 refresh_token
    """

    permission_classes = []
    def post(self,request):
        """
        处理登录请求
        """

        # 获取用户名和密码
        username = request.data.get('username')
        password = request.data.get('password')

        # 验证字段
        if not username or not password:
            return Response(
                {'message':'用户名或密码不能为空'},
                status = status.HTTP_400_BAD_REQUEST
            )
        
        # 按用户名或邮箱查找用户
        try:
            user = User.objects.get(username = username)
        except User.DoesNotExist:
            try: user = User.objects.get(email = username)
            except User.DoesNotExist: return Response(
                {'message':'用户不存在'},
                status = status.HTTP_401_UNAUTHORIZED
            )

        #验证密码
        # .check_password() 函数用于验证明文密码是否匹配数据库中的加密密码。
        if not user.check_password(password):
            return Response(
                {'message':'密码错误'},
                status = status.HTTP_401_UNAUTHORIZED
            )
        
         # 生成 JWT token（access_token + refresh_token）
        refresh = RefreshToken.for_user(user)
        
        response_data = {
            'message':'登录成功',
            'user': UserSerializer(user).data,
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh)
        }

        return Response(response_data, status=status.HTTP_200_OK)
    

class  ProfileView(APIView):
    """
    获取用户信息 API
    - 需要认证（携带 JWT token）
    - 返回当前登录用户的详细信息
    """
    
    # 权限：只有认证用户才能访问
    # 检查密钥是否匹配
    permission_classes = [IsAuthenticated]
    def get(self,request):
        """
        获取当前用户信息
        """
        # request.user 已由 JWT 认证自动设置
        user = request.user

        response_data = {
            'message': '获取用户信息成功',
            'user': UserSerializer(user).data
        }

        return Response(response_data,status = status.HTTP_200_OK)
