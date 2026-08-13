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

        # 检查硬性门槛（考虑否定词）
        for db in self.profile.dealbreakers:
            # 提取关键词（去掉"不"/"没"等否定前缀）
            db_clean = db.lstrip("不没无未")
            # 检查是否命中dealbreaker（排除否定句）
            if db in bio or db in photo_description:
                # 检查否定词：如果前后5字符内有"不"/"没"，不算命中
                idx = bio.find(db) if db in bio else photo_description.find(db)
                if idx >= 0:
                    context = bio[max(0, idx-5):idx+len(db)+5] if db in bio else photo_description[max(0, idx-5):idx+len(db)+5]
                    if any(neg in context for neg in ["不", "没", "无", "未"]):
                        continue  # 否定句，跳过
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
