import json
import re
from typing import Any, Dict

def extract_json_block(text: str) -> str:
    """
    从大模型输出中提取 JSON 部分
    """
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("未找到 JSON 结构")
    return match.group(0)


def safe_json_loads(text: str) -> Dict[str, Any]:
    """
    尝试解析 JSON，必要时进行简单修复
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # 常见修复：中文标点
        repaired = (
            text.replace("，", ",")
                .replace("：", ":")
                .replace("“", "\"")
                .replace("”", "\"")
        )
        return json.loads(repaired)


def parse_travel_plan_response(raw_response: str) -> Dict[str, Any]:
    """
    主解析函数：从模型输出中得到结构化结果
    """
    json_text = extract_json_block(raw_response)
    data = safe_json_loads(json_text)

    # 字段兜底，防止缺失
    data.setdefault("overview", "")
    data.setdefault("daily_plan", [])
    data.setdefault("budget_advice", "")
    data.setdefault("travel_story", "")

    return data
