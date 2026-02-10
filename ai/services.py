import os
from openai import OpenAI
from django.conf import settings

class AIService:
    """AI服务封装"""
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.AI_API_KEY,
            base_url = settings.AI_BASE_URL,
        )
        self.model = settings.AI_MODEL


    def char_stream(self,message):
        """
        流式对话生成
        :param messages: 消息列表 [{"role": "user", "content": "你好"}]
        :yield: 逐字返回的文本片段
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=message,
                stream=True,    # 开启流式返回
            )

            for chunk in response:
                # chunk.choices[0].delta.content 是增量文本
                content = chunk.choices[0].delta.content
                if content:
                    # yield：Python生成器，每次产生一个文本片段
                    yield content
        except Exception as e:
            yield f"错误：{str(e)}"


    def generate_summary(self,content,max_length = 200):
        """
        生成文章摘要
        :param content: 文章内容
        :param max_length: 摘要最大长度
        :return: 摘要文本
        """
        prompt = f"""请为以下文章生成摘要，要求：
        1. 不超过{max_length}字
        2. 包含文章核心观点
        3. 语言简洁通顺
        
        文章内容：
        {content[:3000]}  # 只取前3000字，控制Token
    
        摘要："""

        try:
            response = self.client.chat.completions.create(
                model = self.model,
                messages = [{"role": "user", "content": prompt}],
                stream=False,
                max_tokens=300,
            )
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            return f"[生成摘要失败: {str(e)}]"