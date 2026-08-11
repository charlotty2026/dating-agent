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
    聊天引擎

    两种模式：
    - 有LLM: 接真API，自然对话
    - 无LLM: 仿真模式，用于测试流程
    """

    def __init__(self, profile: PersonalityProfile, llm: Optional[LLMClient] = None,
                 meet_threshold: int = 70, drop_threshold: int = 30):
        """
        Args:
            meet_threshold: 分数>=此值建议约见面
            drop_threshold: 分数<此值建议放弃
        """
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
        生成回复

        Args:
            match_id: 匹配ID
            their_message: 对方发来的消息

        Returns:
            AI生成的回复
        """
        if match_id not in self.conversations:
            self.conversations[match_id] = []

        # 记录对方消息
        self.conversations[match_id].append({
            "role": "user",
            "content": their_message,
        })

        if self.llm:
            reply = self._reply_with_llm(match_id)
        else:
            reply = self._reply_simulated(their_message)

        # 记录AI回复
        self.conversations[match_id].append({
            "role": "assistant",
            "content": reply,
        })

        return reply

    def start_conversation(self, match_id: str) -> str:
        """AI主动发第一条消息"""
        if match_id not in self.conversations:
            self.conversations[match_id] = []

        if self.llm:
            messages = [
                {"role": "system", "content": self.profile.to_system_prompt()},
                {"role": "user", "content": "你刚匹配上一个人，发第一条消息打个招呼。只发一条，自然一点。"},
            ]
            reply = self.llm.chat(messages, temperature=0.9)
        else:
            import random
            templates = [
                "嗨，看到你的profile觉得挺有意思的，你平时喜欢做什么？",
                "你好呀！你简介里写的那个我也有兴趣，聊聊？",
                "哈哈你的照片挺有意思的，是在哪拍的呀？",
            ]
            reply = random.choice(templates)

        self.conversations[match_id].append({
            "role": "assistant",
            "content": reply,
        })
        return reply

    def _reply_with_llm(self, match_id: str) -> str:
        """用LLM生成回复"""
        messages = [
            {"role": "system", "content": self.profile.to_system_prompt()},
        ]

        # 带上对话历史（最近10轮防超长）
        history = self.conversations[match_id][-20:]
        messages.extend(history)

        return self.llm.chat(messages, temperature=0.85)

    def _reply_simulated(self, their_message: str) -> str:
        """仿真回复（无API时用）"""
        if len(their_message) < 5:
            return "嗯嗯"

        if "?" in their_message or "？" in their_message:
            return "哈哈这个问题问得好，我觉得……你呢？"

        return "哈哈，有意思，继续说？"

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

        if self.llm:
            return self._evaluate_with_llm(match_id)
        else:
            return self._evaluate_with_rules(conv)

    def _evaluate_with_llm(self, match_id: str) -> dict:
        """用LLM评估对话质量"""
        conv = self.conversations[match_id]

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
            return self._evaluate_with_rules(conv)

    def _evaluate_with_rules(self, conv: list) -> dict:
        """规则评估（无API时用）"""
        score = 50

        # 聊天轮数
        turns = len(conv) // 2
        score += min(turns * 3, 20)

        # 对方回复平均长度
        their_msgs = [m["content"] for m in conv if m["role"] == "user"]
        if their_msgs:
            avg_len = sum(len(m) for m in their_msgs) / len(their_msgs)
            if avg_len > 20:
                score += 15
            elif avg_len < 5:
                score -= 10

        # 对方是否主动提问
        questions = [m for m in their_msgs if "?" in m or "？" in m]
        if len(questions) >= 2:
            score += 10

        score = max(0, min(100, score))

        avg_len = sum(len(m) for m in their_msgs) // max(len(their_msgs), 1)
        return {
            "score": score,
            "should_meet": score >= self.meet_threshold,
            "should_drop": score < self.drop_threshold,
            "reason": f"规则评估: {len(conv)}条消息, 对方均长{avg_len}",
        }
