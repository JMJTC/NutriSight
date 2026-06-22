import json
from typing import Dict, List


def build_analysis_prompt(food_items: List[Dict], nutrition_totals: Dict, user_profile: Dict) -> str:
    return f"""你是一名注册营养师。根据以下信息分析这顿饭的营养结构，给出个性化饮食建议。

## 识别到的食物
{json.dumps(food_items, ensure_ascii=False, indent=2)}

## 营养素汇总（每100g估算）
{json.dumps(nutrition_totals, ensure_ascii=False)}

## 用户身体数据
{json.dumps(user_profile, ensure_ascii=False)}

请回复：1.**总体评价** 2.**亮点** 3.**需改善** 4.**具体建议**
用中文，300字以内，基于真实数据。"""


def build_history_recommendation_prompt(recent_records: List[Dict], user_profile: Dict) -> str:
    return f"""你是一名健康管理顾问。根据以下近期饮食记录，分析趋势并给出建议。

## 近期饮食记录
{json.dumps(recent_records, ensure_ascii=False, indent=2)}

## 用户身体数据
{json.dumps(user_profile, ensure_ascii=False)}

请回复：1.**饮食趋势** 2.**营养均衡度** 3.**长期建议**（3-4条）
用中文，400字以内，鼓励语气。"""


def build_chat_system_prompt(context_info: str = "") -> str:
    base = """你是一名专业的营养顾问，拥有丰富的营养学、食品安全和饮食搭配知识。
可以解答：食物营养、饮食搭配（增肌/减脂）、特殊饮食需求（糖尿病/高血压等）、食品安全与烹饪、运动营养。
要求：中文回复，知识准确语气亲切，涉及医疗问题提醒咨询医生，300字以内。"""
    if context_info:
        return base + f"\n\n## 当前上下文\n{context_info}\n\n在回复时参考以上上下文。"
    return base
