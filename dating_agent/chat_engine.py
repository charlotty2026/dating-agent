"""
聊天引擎 - 接真LLM API，有对话记忆

核心能力：
1. 自然聊天（不是预设模板）
2. 对话中判断合不合适
3. 合适就约见面，不合适就礼貌结束
"""

from typing import Optional
from .llm_client import LLMClient
from .profile import PersonalityProfile


class ChatEngine:
    """
    聊天引擎 - Agent循环

    核心流程：
    感知（看到对方消息）→ 思考（结合记忆判断）→ 行动（生成回复）→ 记忆（存入历史）
    """

    def __init__(self, profile: PersonalityProfile, llm: Optional[LLMClient] = None,
                 meet_threshold: int = 70, drop_threshold: int = 30):
        self.profile = profile
        self.llm = llm
        self.meet_threshold = meet_threshold
        self.drop_threshold = drop_threshold
        self.conversations = {}  # match_id -> [{"role": "...", "content": "..."}]

    def get_history(self, match_id: str) -> list:
        """获取对话历史"""
        return self.conversations.get(match_id, [])

    def reply(self, match_id: str, their_message: str) -> str:
        """
        生成回复 - Agent循环的核心动作

        Args:
            match_id: 匹配ID
            their_message: 对方发来的消息

        Returns:
            AI生成的回复
        """
        # 初始化对话历史
        if match_id not in self.conversations:
            self.conversations[match_id] = []

        # 感知：记录对方消息
        self.conversations[match_id].append({
            "role": "user",
            "content": their_message,
        })

        # 限制对话历史长度（保留最近50条，防止内存泄漏）
        self.conversations[match_id] = self.conversations[match_id][-50:]

        # 必须有LLM才能聊天
        if not self.llm:
            raise ValueError(
                "聊天功能需要接LLM API！\n"
                "请设置环境变量：\n"
                "  export LLM_API_KEY='your-key'\n"
                "  export LLM_BASE_URL='https://api.deepseek.com/v1'\n"
                "  export LLM_MODEL='deepseek-chat'"
            )

        # 行动：生成回复
        reply = self._generate_reply(match_id)

        # 记忆：存入历史
        self.conversations[match_id].append({
            "role": "assistant",
            "content": reply,
        })

        return reply

    def start_conversation(self, match_id: str) -> str:
        """AI主动发第一条消息"""
        if match_id not in self.conversations:
            self.conversations[match_id] = []

        # 必须有LLM
        if not self.llm:
            raise ValueError("聊天功能需要接LLM API！")

        messages = [
            {"role": "system", "content": self.profile.to_system_prompt()},
            {"role": "user", "content": "你刚匹配上一个人，发第一条消息打个招呼。只发一条，自然一点。"},
        ]
        reply = self.llm.chat(messages, temperature=0.9)

        self.conversations[match_id].append({
            "role": "assistant",
            "content": reply,
        })
        return reply

    def _generate_reply(self, match_id: str) -> str:
        """
        生成回复 - 结合记忆+上下文

        记忆：对方的基本信息、之前的对话历史
        上下文：当前这条消息
        """
        messages = [
            {"role": "system", "content": self.profile.to_system_prompt()},
        ]

        # 带上对话历史（最近10轮防超长）
        history = self.conversations[match_id][-20:]
        messages.extend(history)

        return self.llm.chat(messages, temperature=0.85)

    def evaluate(self, match_id: str) -> dict:
        """
        评估一段聊天的质量

        Returns:
            {
                "score": 0-100,
                "should_meet": bool,
                "should_drop": bool,
                "reason": str,
            }
        """
        conv = self.conversations.get(match_id, [])

        if not conv:
            return {"score": 0, "should_meet": False, "should_drop": False,
                    "reason": "还没聊"}

        if not self.llm:
            raise ValueError("评估功能需要接LLM API！")

        # 构建对话文本
        conv_text = "\n".join(
            f"{'你' if m['role'] == 'assistant' else '对方'}: {m['content']}"
            for m in conv
        )

        messages = [
            {"role": "system", "content": f"""你是一个聊天质量评估器。
评估以下对话，判断两个人是否合适继续发展。

主人的偏好：
喜欢：{', '.join(self.profile.likes)}
讨厌：{', '.join(self.profile.dislikes)}

输出JSON：
{{
  "score": 0-100整数,
  "should_meet": true/false,
  "should_drop": true/false,
  "reason": "简短理由"
}}"""},
            {"role": "user", "content": f"对话记录:\n{conv_text}"},
        ]

        try:
            result = self.llm.chat_json(messages, temperature=0.2)
            return {
                "score": int(result.get("score", 50)),
                "should_meet": result.get("should_meet", False),
                "should_drop": result.get("should_drop", False),
                "reason": result.get("reason", ""),
            }
        except Exception:
            # 评估失败，默认不推荐也不放弃
            return {"score": 50, "should_meet": False, "should_drop": False,
                    "reason": "评估失败，需要人工判断"}
