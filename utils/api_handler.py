import os
import requests
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from utils.prompt_templates import build_travel_prompt
from utils.response_parser import parse_travel_plan_response

load_dotenv()

class ZhipuAIClient:
    """智谱AI AFPI客户端"""
    
    def __init__(self):
        self.api_key = os.getenv("ZHIPU_API_KEY")
        self.base_url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        self.model = os.getenv("ZHIPU_MODEL", "glm-4")
        
    def generate_response(self, prompt: str, temperature: float = 0.7) -> str:
        """调用智谱AI生成回复"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            
            if "choices" in result:
                return result["choices"][0]["message"]["content"]
            else:
                error_msg = result.get("error", {}).get("message", "未知错误")
                return f"❌ API错误：{error_msg}"
                
        except requests.exceptions.Timeout:
            return "⏰ 请求超时，请稍后重试"
        except Exception as e:
            return f"🔌 请求失败：{str(e)}"
    
    def generate_travel_plan(self, user_input: Dict[str, Any]) -> Dict[str, Any]:
        """生成旅行计划（基于结构化 Prompt）"""
    
    # 1. 构建 Prompt（来自独立模块）
        prompt = build_travel_prompt(user_input)
    
    # 2. 调用大模型
        response = self.generate_response(prompt)
    
        try:
            parsed = parse_travel_plan_response(response)
            formatted_plan = parsed
        except Exception as e:
            formatted_plan = {
                "overview": "生成失败，请重试",
                "daily_plan": [],
                "budget_advice": "",
                "travel_story": ""
        }

        return {
            "prompt": prompt,
            "raw_response": response,
            "formatted_plan": formatted_plan
        }

    def _build_travel_prompt(self, user_input: Dict[str, Any]) -> str:
        """构建旅行规划提示词"""
        destination = user_input.get("destination", "")
        days = user_input.get("days", 3)
        budget = user_input.get("budget", "舒适型")
        people = user_input.get("people", 2)
        style = user_input.get("style", "休闲放松")
        
        return f"""你是一个专业的旅行规划师，请为以下需求创建{days}天的详细旅行计划：

【旅行需求】
目的地：{destination}
天数：{days}天
预算：{budget}
人数：{people}人
风格：{style}

【要求】
请按以下结构回复：
1. 行程概述（100字以内）
2. 每日详细安排（按天分上午、下午、晚上）
3. 住宿推荐（2-3个选择，包含特点和价格范围）
4. 预算分配表（住宿、餐饮、交通、门票、其他）
5. 旅行叙事（一段生动的旅行故事）
6. 实用建议（3-5条）

请确保内容具体、实用、符合预算。"""
    
    def _parse_response(self, response: str) -> str:
        """解析AI回复"""
        # 这里可以添加更复杂的解析逻辑
        # 目前先返回原始回复
        return response