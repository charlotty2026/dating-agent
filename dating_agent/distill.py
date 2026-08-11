"""
蒸馏自己 - 从你的聊天记录提取你的说话风格

这是整个项目最核心的"魔法"：
你不写prompt，你把自己的聊天记录丢进去，
AI帮你提取出你的说话方式，生成专属system prompt。
"""

from typing import Optional
from .llm_client import LLMClient
from .profile import PersonalityProfile


class Distiller:
    """蒸馏器 - 从聊天记录提取性格档案"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    def distill(self, chat_logs: list, basic_info: dict) -> PersonalityProfile:
        """
        从聊天记录蒸馏出性格档案

        Args:
            chat_logs: 你的聊天记录列表
                [{"role": "me/them", "content": "..."}, ...]
            basic_info: 基本信息
                {"name": "...", "gender": "...", "age": 27}

        Returns:
            PersonalityProfile
        """
        # 构建对话文本
        max_logs = 100
        if len(chat_logs) > max_logs:
            import warnings
            warnings.warn(
                f"聊天记录共{len(chat_logs)}条，仅取前{max_logs}条进行分析，"
                f"后{len(chat_logs) - max_logs}条被截断。",
                stacklevel=2,
            )
        conv_text = "\n".join(
            f"{'我' if log.get('role') == 'me' else '对方'}: {log['content']}"
            for log in chat_logs[:max_logs]  # 最多取100条防超长
        )

        messages = [
            {"role": "system", "content": """你是一个性格分析专家。
用户会给你一段聊天记录，你需要从中提取用户的性格特征。

输出JSON格式：
{
  "personality_tags": ["标签1", "标签2", ...],
  "likes": ["喜欢的特质1", ...],
  "dislikes": ["讨厌的特质1", ...],
  "chat_style": "聊天风格描述（用第二人称'你'描述）",
  "dealbreakers": ["硬性门槛1", ...],
  "bonus_traits": ["加分项1", ...]
}

注意：
- 标签要具体，不要泛泛的"善良""温柔"
- chat_style要描述具体的说话习惯（句式/用词/节奏）
- 从聊天内容推断对方的偏好，不只是字面意思"""},
            {"role": "user", "content": f"我的基本信息: {basic_info}\n\n我的聊天记录:\n{conv_text}"},
        ]

        try:
            result = self.llm.chat_json(messages, temperature=0.5)

            return PersonalityProfile(
                name=basic_info.get("name", "用户"),
                gender=basic_info.get("gender", ""),
                age=basic_info.get("age", 0),
                personality_tags=result.get("personality_tags", []),
                likes=result.get("likes", []),
                dislikes=result.get("dislikes", []),
                chat_style=result.get("chat_style", ""),
                dealbreakers=result.get("dealbreakers", []),
                bonus_traits=result.get("bonus_traits", []),
            )
        except Exception as e:
            raise RuntimeError(f"蒸馏失败: {e}")

    def refine_style(self, profile: PersonalityProfile,
                     new_chats: list) -> PersonalityProfile:
        """
        用新聊天记录迭代优化风格描述

        用得越久，AI越像你。
        """
        conv_text = "\n".join(
            f"{'我' if log.get('role') == 'me' else '对方'}: {log['content']}"
            for log in new_chats[:50]
        )

        messages = [
            {"role": "system", "content": f"""这是用户现有的聊天风格描述：
{profile.chat_style}

用户提供了新的聊天记录。请基于新记录，优化这个风格描述，
让它更准确。保留原有的准确部分，补充新发现的特点。

只输出优化后的风格描述文本，不要输出其他内容。"""},
            {"role": "user", "content": f"新聊天记录:\n{conv_text}"},
        ]

        refined = self.llm.chat(messages, temperature=0.4)
        profile.chat_style = refined.strip()
        return profile
