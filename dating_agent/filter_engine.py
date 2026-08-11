"""
筛选引擎 - 用LLM做语义判断，不是关键词匹配
"""

from typing import Optional
from .llm_client import LLMClient
from .profile import PersonalityProfile


class FilterEngine:
    """
    初筛引擎 - 判断要不要右滑

    v0.1: 关键词匹配（仿真模式，不花钱）
    v0.2: LLM语义判断（需要API key）
    """

    def __init__(self, profile: PersonalityProfile, llm: Optional[LLMClient] = None):
        self.profile = profile
        self.llm = llm

    def evaluate(self, bio: str, interests: list,
                 photo_description: str = "") -> dict:
        """
        评估一个profile要不要右滑

        Returns:
            {
                "should_swipe_right": bool,
                "score": int,  # 0-100
                "reason": str,
            }
        """
        if self.llm:
            return self._evaluate_with_llm(bio, interests, photo_description)
        else:
            return self._evaluate_with_rules(bio, interests, photo_description)

    def _evaluate_with_rules(self, bio: str, interests: list,
                              photo_description: str) -> dict:
        """规则匹配模式（不花API钱）"""
        score = 50
        reasons = []

        # 检查硬性门槛
        bio_lower = bio.lower()
        for db in self.profile.dealbreakers:
            if db in bio or db in photo_description:
                return {
                    "should_swipe_right": False,
                    "score": 0,
                    "reason": f"命中硬性门槛: {db}",
                }

        # 加分项
        for like in self.profile.likes:
            if like in bio:
                score += 10
                reasons.append(f"有'{like}'特质")

        for interest in interests:
            if interest in self.profile.bonus_traits:
                score += 8
                reasons.append(f"加分兴趣: {interest}")

        # 减分项
        for dislike in self.profile.dislikes:
            if dislike in bio:
                score -= 15
                reasons.append(f"有'{dislike}'特质")

        # 照片检查
        for word in ["酒", "烟", "夜店"]:
            if word in photo_description:
                score -= 10
                reasons.append(f"照片有{word}")

        for word in ["动物", "猫", "狗", "书"]:
            if word in photo_description:
                score += 5
                reasons.append(f"照片有{word}")

        score = max(0, min(100, score))
        return {
            "should_swipe_right": score >= 60,
            "score": score,
            "reason": "; ".join(reasons) if reasons else "无明显特征",
        }

    def _evaluate_with_llm(self, bio: str, interests: list,
                            photo_description: str) -> dict:
        """LLM语义判断模式"""
        user_profile_text = f"""
简介: {bio}
兴趣: {', '.join(interests) if interests else '未填写'}
照片描述: {photo_description if photo_description else '无照片'}
"""
        messages = [
            {"role": "system", "content": self.profile.to_filter_prompt()},
            {"role": "user", "content": user_profile_text},
        ]

        try:
            result = self.llm.chat_json(messages, temperature=0.3)
            return {
                "should_swipe_right": result.get("should_swipe_right", False),
                "score": int(result.get("score", 50)),
                "reason": result.get("reason", "LLM未给出理由"),
            }
        except Exception as e:
            # LLM挂了就退回规则模式
            return self._evaluate_with_rules(bio, interests, photo_description)
