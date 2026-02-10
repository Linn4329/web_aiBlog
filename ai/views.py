import json
from django.http import StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view,permission_classes
from rest_framework.permissions import IsAuthenticated
from .services import AIService
from .models import ChatSession, ChatMessage, AIUsageLog
from rest_framework.response import Response
from rest_framework import status


# @api_view(['POST']) - 只接受POST请求，GET会返回405
@api_view(['post'])

# @permission_classes([IsAuthenticated]) - 检查JWT Token，没登录返回401
@permission_classes([IsAuthenticated])


def generate_summary(request):
    """
    文章摘要接口 POST /api/ai/summarize/
    
    请求体：
    {
        "content": "文章正文...",  // 必填
        "max_length": 200          // 可选，默认200字
    }
    
    响应：
    {
        "summary": "生成的摘要..."
    }
    """

    content = request.data.get('content','').strip()
    max_length = request.data.get('max_length',200)

    if not content:
        return Response(
            {'error': '文章内容不能为空'},
            status = status.HTTP_400_BAD_REQUEST
        )
    # 调用AI生成摘要
    ai = AIService()
    summary = ai.generate_summary(content,max_length)

    # 记录调用日志
    AIUsageLog.objects.create(
        user=request.user,
        call_type='summarize',
        prompt_summary=content[:50] + "...",
        # ... 其他字段
    )

    return Response({"summary": summary})


@api_view(['post'])
@permission_classes([IsAuthenticated])

def chat_stream(request):
    """
    AI流式对话接口 POST /api/ai/chat/
    
    请求体：
    {
        "session_id": 1,        // 可选，不传则创建新会话
        "message": "你好"        // 用户消息
    }
    
    返回:SSE流 text/event-stream
    """

    user = request.user
    session_id = request.data.get('session_id')
    message = request.data.get('message','').strip()
    if not message:
        return StreamingHttpResponse(
            "data:[错误：消息不能为空]\n\n",
            content_type="text/event-stream",
        )
    
    # 获取或创建会话
    #     用户传入session_id? 
    #   ├── 是 → 查询该用户的会话
    #   │         ├── 存在 → 继续用
    #   │         └── 不存在 → 报错（防止用户访问别人的会话）
    #   └── 否 → 创建新会话，标题取消息前20字
    if session_id:
        # filter(user=user) 确保只能访问自己的会话
        session = ChatSession.objects.filter(id=session_id,user = user ).first()
        if not session:
            return StreamingHttpResponse(
            "data:[错误：会话不存在]\n\n",
            content_type="text/event-stream",
        )
    else:
        session = ChatSession.objects.create(
            user = user,
            title = message[:20]
        )

    # 保存用户消息
    ChatMessage.objects.create(
        content = message,
        role = 'user',
        session = session,
    )

    # 构建历史消息（取最近20条）
    history = ChatMessage.objects.filter(session=session).order_by('-id')[:20]
    messages = [{"role": msg.role, "content": msg.content} for msg in reversed(history)]


    # 创建AI服务
    ai = AIService()
    def event_stream():
        """SSE事件生成器"""
        full_response = []
        # 发送会话ID
        yield f"data:{json.dumps({'type':'session','session_id': session.id})}\n\n"

        # 流式返回AI回复

        #   循环从AI获取文本片段
        #   ├── 拼接到完整回复（用于后面保存数据库）
        #   └── 立即yield给前端（用户实时看到）
        for chunk in ai.chat_stream(messages):
            full_response.append(chunk)
            yield f"data: {json.dumps({'type': 'content', 'text': chunk})}\n\n"

        # 保存完整回复到数据库
        complete_text = ''.join(full_response)
        ChatMessage.objects.create(
            session=session,
            role='assistant',
            content=complete_text
        )

        # 发送结束标记
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # 禁用Nginx缓冲
    return response
