from typing import Dict, List

from app.core.exceptions import CustomException
from app.log import logger
from app.models.admin import User
from app.models.food import Nutrition, NutritionRecommendation, RecognitionRecord
from app.services.ai.client import ai_client
from app.services.ai.prompts import (
    build_analysis_prompt,
    build_chat_system_prompt,
    build_history_recommendation_prompt,
)

try:
    from app.utils.crypto import decrypt_api_key
except ImportError:
    decrypt_api_key = lambda x: x  # stub — replaced by Task 6


class AiService:

    @staticmethod
    async def _get_user_ai_config(user_id: int) -> tuple:
        user = await User.get(id=user_id)
        api_key = getattr(user, "api_key", None)
        if not api_key:
            raise CustomException(message="请先在个人资料中配置 AI API Key", code=400)
        api_key = decrypt_api_key(api_key)
        base_url = getattr(user, "ai_base_url", None)
        model = getattr(user, "ai_model", None)
        return api_key, base_url, model

    @staticmethod
    async def _get_user_profile(user_id: int) -> Dict:
        user = await User.get(id=user_id)
        h = getattr(user, "height_cm", None)
        w = getattr(user, "weight_kg", None)
        g = getattr(user, "gender", None)
        a = getattr(user, "age", None)
        bmi = None
        status = "未知"
        if h and w:
            bmi = round(float(w) / ((h / 100) ** 2), 1)
            if bmi < 18.5:
                status = "偏瘦"
            elif 24 <= bmi < 28:
                status = "超重"
            elif bmi >= 28:
                status = "肥胖"
            else:
                status = "正常"
        return {
            "身高": f"{h}cm" if h else "未设置",
            "体重": f"{w}kg" if w else "未设置",
            "性别": {1: "男", 2: "女", 3: "其他"}.get(g, "未设置"),
            "年龄": f"{a}岁" if a else "未设置",
            "BMI": f"{bmi}（{status}）" if bmi else "未计算",
        }

    async def _build_record_context(self, record_id: int) -> tuple:
        record = await RecognitionRecord.get_or_none(id=record_id).prefetch_related(
            "analysis", "details", "details__food", "details__food__nutrition"
        )
        if not record:
            raise CustomException(message="识别记录不存在", code=404)
        items = []
        totals = {
            "热量_kcal": 0,
            "蛋白质_g": 0,
            "脂肪_g": 0,
            "碳水_g": 0,
            "纤维_g": 0,
            "钠_mg": 0,
        }
        if record.details:
            for d in record.details:
                item = {
                    "食物": (d.food.chinese_name or d.food.name) if d.food else "未知",
                    "置信度": f"{d.confidence * 100:.1f}%",
                }
                if d.food:
                    n = await Nutrition.get_or_none(food=d.food)
                    if n:
                        item["营养(每100g)"] = {
                            "热量": f"{n.energy}kcal",
                            "蛋白质": f"{n.protein}g",
                            "脂肪": f"{n.fat}g",
                            "碳水": f"{n.carbohydrate}g",
                        }
                        for k, v in [
                            ("热量_kcal", n.energy),
                            ("蛋白质_g", n.protein),
                            ("脂肪_g", n.fat),
                            ("碳水_g", n.carbohydrate),
                        ]:
                            totals[k] += float(v or 0)
                items.append(item)
        return items, totals

    async def analyze_record(self, record_id: int, user_id: int) -> Dict:
        api_key, base_url, model = await self._get_user_ai_config(user_id)
        items, totals = await self._build_record_context(record_id)
        profile = await self._get_user_profile(user_id)
        system = build_analysis_prompt(items, totals, profile)
        result = await ai_client.chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": "请分析这顿饭。"},
            ],
            api_key,
            base_url,
            model,
        )
        user = await User.get(id=user_id)
        record = await RecognitionRecord.get(id=record_id)
        await NutritionRecommendation.create(
            user=user,
            record=record,
            content=result["content"],
            reference=f"AI分析 record_id={record_id} model={model}",
        )
        return {"record_id": record_id, "content": result["content"]}

    async def generate_history_recommendation(self, user_id: int) -> Dict:
        api_key, base_url, model = await self._get_user_ai_config(user_id)
        records = (
            await RecognitionRecord.filter(user_id=user_id)
            .order_by("-created_at")
            .limit(10)
            .prefetch_related("analysis")
        )
        recent = []
        for r in records:
            recent.append(
                {
                    "时间": r.created_at.strftime("%Y-%m-%d %H:%M") if r.created_at else "",
                    "热量_kcal": r.analysis.total_energy if r.analysis else 0,
                    "蛋白质_g": r.analysis.total_protein if r.analysis else 0,
                    "状态": r.status,
                }
            )
        system = build_history_recommendation_prompt(
            recent, await self._get_user_profile(user_id)
        )
        result = await ai_client.chat(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": "请分析我的饮食情况，给出改善建议。"},
            ],
            api_key,
            base_url,
            model,
        )
        user = await User.get(id=user_id)
        await NutritionRecommendation.create(
            user=user,
            content=result["content"],
            reference=f"AI历史分析 records={len(recent)} model={model}",
        )
        return {"content": result["content"]}

    async def chat(self, user_id: int, messages: List[Dict], context: str = "") -> Dict:
        api_key, base_url, model = await self._get_user_ai_config(user_id)
        system = build_chat_system_prompt(context)
        result = await ai_client.chat(
            [{"role": "system", "content": system}] + messages,
            api_key,
            base_url,
            model,
        )
        user = await User.get(id=user_id)
        await NutritionRecommendation.create(
            user=user,
            content=result["content"],
            reference=f"AI对话 messages={len(messages)} model={model}",
        )
        return {"content": result["content"]}

    async def test_connection(self, user_id: int) -> Dict:
        api_key, base_url, model = await self._get_user_ai_config(user_id)
        return await ai_client.test_connection(api_key, base_url, model)


ai_service = AiService()
