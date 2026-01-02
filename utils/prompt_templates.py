def build_travel_prompt(user_input: dict) -> str:
    """
    构建旅行规划 Prompt（注入真实POI数据）
    """
    # 从user_input中提取真实数据
    destination = user_input.get('destination', '')
    real_attractions = user_input.get('real_attractions', [])
    real_restaurants = user_input.get('real_restaurants', [])
    
    real_data_context = ""
    if real_attractions:
        real_data_context += f"\n【系统提示：以下是{destination}的真实热门景点，请优先在行程中考虑】\n" + "\n".join([f"- {attr}" for attr in real_attractions])
    if real_restaurants:
        real_data_context += f"\n【系统提示：以下是{destination}的真实热门餐饮，请优先在行程中考虑】\n" + "\n".join([f"- {rest}" for rest in real_restaurants])
    
    return f"""
你是一名【资深旅行规划师】和【旅行故事作家】。

请根据以下用户需求，并结合提供的【真实地点信息】，生成一个【结构化、合理、具有叙事感】的旅行计划。
{real_data_context}

【用户需求】
- 目的地：{user_input.get('destination')} (坐标：{user_input.get('city_location', '未知')})
- 旅行天数：{user_input.get('days')} 天
- 出行人数：{user_input.get('people')} 人
- 预算等级：{user_input.get('budget')}
- 旅行风格：{user_input.get('style')}
- 住宿偏好：{user_input.get('hotel_preference', '无特殊要求')}

【规划原则】
1. 行程节奏合理，避免过度疲劳。
2. 活动安排请务必参考上方提供的【真实景点和餐厅】，使推荐具体可信。
3. 考虑地点间的距离（基于给定坐标），确保动线顺畅。
4. 符合用户预算与风格偏好。

【输出格式要求】
请【严格只输出 JSON】，不要包含任何解释性文字。
JSON 格式如下：
{{
  "overview": "整体旅行概述（100字左右）",
  "daily_plan": [
    {{
      "day": 1,
      "morning": "上午活动安排（请提及具体景点名）",
      "afternoon": "下午活动安排（请提及具体景点或餐厅名）",
      "evening": "晚上活动安排（请提及具体餐厅名）",
      "tips": "当天旅行小贴士"
    }}
  ],
  "budget_advice": "预算分配建议（结合用户预算等级）",
  "travel_story": "一段生动的旅行叙事，融入推荐的具体地点"
}}
"""