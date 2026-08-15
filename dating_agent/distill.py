"""
蒸馏自己 - 从你的聊天记录提取你的性格档案

这是整个项目的核心"魔法"：
你不写prompt，你把自己的聊天记录丢进去，
AI帮你提取出你的说话方式、择偶偏好、硬性门槛，
生成一份专属的PersonalityProfile，作为Agent的长期记忆。

v0.3 升级（对齐项目书 2.1 节 + 蒸馏技能方法论）：
1. 五要素蒸馏：性格标签 / 择偶偏好 / 聊天风格指纹 / 价值观雷达 / 红线模式
2. 证据链：每条结论标注 verbatim（原文）/ artifact（物证）/ impression（推测）
3. 反馈闭环：蒸馏后先给用户看摘要确认，可纠正；追加新记录可增量更新
"""

from typing import Optional
from datetime import datetime
from .llm_client import LLMClient
from .profile import PersonalityProfile


class Distiller:
    """蒸馏器 - 从聊天记录提取性格档案"""

    def __init__(self, llm: LLMClient):
        self.llm = llm

    # ─── v0.3 新增：智能文本解析 ───
    @staticmethod
    def parse_chat_logs(text: str) -> list:
        """
        解析用户粘贴的聊天记录文本。

        支持的角色标记（自动识别"我"和"对方"）：
        - 我/me/i/你/自己 → role="me"
        - 对方/ta/他/她/them → role="them"
        也支持时间戳前缀（如 "2026-08-14 21:00 我: 你好"）。

        Args:
            text: 多行聊天记录文本

        Returns:
            [{"role": "me/them", "content": "..."}, ...]
        """
        me_markers = ("我", "me", "i", "自己", "你")
        them_markers = ("对方", "ta", "他", "她", "them", "别人")
        chat_logs = []

        for line in text.strip().splitlines():
            line = line.strip()
            if not line:
                continue
            # 剥掉时间戳前缀
            import re
            line = re.sub(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}\s+\d{1,2}:\d{2}(:\d{2})?\s*", "", line)
            line = re.sub(r"^\d{1,2}:\d{2}(:\d{2})?\s*", "", line)

            if ":" not in line:
                continue
            role_part, content = line.split(":", 1)
            role_part = role_part.strip().lower()
            content = content.strip()
            if not content:
                continue

            if any(role_part == m or role_part.startswith(m) for m in me_markers):
                role = "me"
            elif any(role_part == m or role_part.startswith(m) for m in them_markers):
                role = "them"
            else:
                continue
            chat_logs.append({"role": role, "content": content})

        return chat_logs

    @staticmethod
    def _build_conv_text(chat_logs: list, max_logs: int = 100) -> str:
        """把聊天记录拼成LLM输入文本"""
        if len(chat_logs) > max_logs:
            import warnings
            warnings.warn(
                f"聊天记录共{len(chat_logs)}条，仅取前{max_logs}条进行分析，"
                f"后{len(chat_logs) - max_logs}条被截断。",
                stacklevel=2,
            )
        return "\n".join(
            f"{'我' if log.get('role') == 'me' else '对方'}: {log['content']}"
            for log in chat_logs[:max_logs]
        )

    def distill(self, chat_logs: list, basic_info: dict) -> PersonalityProfile:
        """
        从聊天记录蒸馏出性格档案（v0.3：五要素 + 证据链）

        Args:
            chat_logs: 你的聊天记录列表
                [{"role": "me/them", "content": "..."}, ...]
            basic_info: 基本信息
                {"name": "...", "gender": "...", "age": 27}

        Returns:
            PersonalityProfile
        """
        conv_text = self._build_conv_text(chat_logs)

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
  "bonus_traits": ["加分项1", ...],
  "chat_style_fingerprint": {
    "message_length": "短句为主/中长句/长篇输出",
    "emoji_frequency": "几乎不用/偶尔/频繁",
    "question_habit": "爱提问/偏陈述/先听后说",
    "catchphrases": ["口头禅1", "口头禅2"],
    "tone_words": ["语气词1", "语气词2"],
    "topic_preferences": ["聊什么来劲1", "聊什么来劲2"],
    "reply_pace": "秒回/慢热/看心情"
  },
  "values_radar": {
    "money": {"score": 0-100, "description": "金钱观倾向"},
    "career": {"score": 0-100, "description": "事业心倾向"},
    "family": {"score": 0-100, "description": "家庭观倾向"},
    "social": {"score": 0-100, "description": "社交倾向"},
    "life_attitude": {"score": 0-100, "description": "生活态度"}
  },
  "redline_patterns": [
    {"pattern": "具体拒绝的行为/特征", "reason": "为什么拒绝", "source": "聊天记录"}
  ],
  "evidence": [
    {"claim": "结论", "evidence_text": "聊天记录原文摘录", "level": "verbatim|artifact|impression"}
  ]
}

注意：
- 标签要具体，不要泛泛的'善良''温柔'
- chat_style要描述具体的说话习惯（句式/用词/节奏）
- chat_style_fingerprint必须从真实聊天记录提取，没有证据的项留空或写'未知'
- values_radar的score表示用户对该维度的看重程度（0-100），依据聊天内容推断
- redline_patterns是用户实际拒绝过/明确表达过反感的特征（历史行为），不是猜的
- evidence是证据链：verbatim=聊天记录原文直接支持；artifact=行为/物证推断；impression=推测
- 每条关键结论（尤其likes/dislikes/dealbreakers/redline_patterns）尽量给evidence
- dealbreakers要写死的一票否决项
- bonus_traits是加分项，不是必须的"""},
            {"role": "user", "content": f"我的基本信息: {basic_info}\n\n我的聊天记录:\n{conv_text}"},
        ]

        try:
            result = self.llm.chat_json(messages, temperature=0.5)
            now = datetime.now().isoformat(timespec="seconds")

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
                # v0.3 新字段
                chat_style_fingerprint=result.get("chat_style_fingerprint", {}) or {},
                values_radar=result.get("values_radar", {}) or {},
                redline_patterns=result.get("redline_patterns", []) or [],
                evidence=result.get("evidence", []) or [],
                distill_meta={
                    "version": "v0.3",
                    "source_count": len(chat_logs),
                    "created_at": now,
                    "updated_at": now,
                    "corrections_count": 0,
                    "corrections": [],
                },
            )
        except Exception as e:
            raise RuntimeError(f"蒸馏失败: {e}")

    # ─── v0.3 新增：增量更新（进化机制：追加新记录，档案越用越准） ───
    def update_profile(self, profile: PersonalityProfile,
                       new_chats: list) -> PersonalityProfile:
        """
        用新聊天记录增量更新档案（保留已有内容，合并新发现）。

        对应蒸馏技能里的"进化模式"——追加材料后合并更新，
        而不是推倒重来。
        """
        conv_text = self._build_conv_text(new_chats, max_logs=50)

        old_summary = {
            "personality_tags": profile.personality_tags,
            "likes": profile.likes,
            "dislikes": profile.dislikes,
            "chat_style": profile.chat_style,
            "chat_style_fingerprint": profile.chat_style_fingerprint,
            "values_radar": profile.values_radar,
            "redline_patterns": profile.redline_patterns,
        }

        messages = [
            {"role": "system", "content": f"""你是性格档案更新专家。
用户已有如下性格档案（JSON）：
{old_summary}

用户提供了新的聊天记录。请基于新记录更新档案：
1. 保留仍然成立的旧结论
2. 补充新发现的特点（新口头禅/新偏好/新价值观线索/新拒绝行为）
3. 修正与新记录矛盾的地方
4. 不要因为新记录而丢失原有准确信息

只输出完整的更新后档案JSON，结构为：
{{
  "personality_tags": [...],
  "likes": [...],
  "dislikes": [...],
  "chat_style": "...",
  "dealbreakers": [...],
  "bonus_traits": [...],
  "chat_style_fingerprint": {{...}},
  "values_radar": {{...}},
  "redline_patterns": [...],
  "evidence": [...]
}}"""},
            {"role": "user", "content": f"新聊天记录:\n{conv_text}"},
        ]

        result = self.llm.chat_json(messages, temperature=0.4)

        profile.personality_tags = result.get("personality_tags", profile.personality_tags)
        profile.likes = result.get("likes", profile.likes)
        profile.dislikes = result.get("dislikes", profile.dislikes)
        profile.chat_style = result.get("chat_style", profile.chat_style)
        profile.dealbreakers = result.get("dealbreakers", profile.dealbreakers)
        profile.bonus_traits = result.get("bonus_traits", profile.bonus_traits)
        profile.chat_style_fingerprint = result.get("chat_style_fingerprint", profile.chat_style_fingerprint) or profile.chat_style_fingerprint
        profile.values_radar = result.get("values_radar", profile.values_radar) or profile.values_radar
        profile.redline_patterns = result.get("redline_patterns", profile.redline_patterns) or profile.redline_patterns
        if result.get("evidence"):
            profile.evidence = profile.evidence + result["evidence"]

        profile.distill_meta["updated_at"] = datetime.now().isoformat(timespec="seconds")
        profile.distill_meta["source_count"] = profile.distill_meta.get("source_count", 0) + len(new_chats)
        return profile

    # ─── v0.3 新增：用户纠正（反馈闭环：'这不对，我不是这样的'） ───
    def apply_corrections(self, profile: PersonalityProfile,
                          corrections: list) -> PersonalityProfile:
        """
        应用用户纠正，修正档案。

        Args:
            corrections: [{"what": "你觉得哪里不对", "fixed": "正确应该是什么"}]
        """
        if not corrections:
            return profile

        messages = [
            {"role": "system", "content": f"""你是性格档案修正专家。
用户对已有档案提出纠正。请只修改被纠正的部分，保持其他内容不变。

已有档案：
{{
  "personality_tags": {profile.personality_tags},
  "likes": {profile.likes},
  "dislikes": {profile.dislikes},
  "chat_style": "{profile.chat_style}",
  "chat_style_fingerprint": {profile.chat_style_fingerprint},
  "values_radar": {profile.values_radar},
  "redline_patterns": {profile.redline_patterns}
}}

只输出更新后的完整JSON，结构与上面一致。"""},
            {"role": "user", "content": f"我的纠正: {corrections}"},
        ]

        result = self.llm.chat_json(messages, temperature=0.3)

        profile.personality_tags = result.get("personality_tags", profile.personality_tags)
        profile.likes = result.get("likes", profile.likes)
        profile.dislikes = result.get("dislikes", profile.dislikes)
        profile.chat_style = result.get("chat_style", profile.chat_style)
        profile.chat_style_fingerprint = result.get("chat_style_fingerprint", profile.chat_style_fingerprint) or profile.chat_style_fingerprint
        profile.values_radar = result.get("values_radar", profile.values_radar) or profile.values_radar
        profile.redline_patterns = result.get("redline_patterns", profile.redline_patterns) or profile.redline_patterns

        profile.distill_meta["corrections_count"] = profile.distill_meta.get("corrections_count", 0) + len(corrections)
        profile.distill_meta.setdefault("corrections", []).extend(corrections)
        profile.distill_meta["updated_at"] = datetime.now().isoformat(timespec="seconds")
        return profile

    def refine_style(self, profile: PersonalityProfile,
                     new_chats: list) -> PersonalityProfile:
        """
        用新聊天记录迭代优化风格描述

        用得越久，AI越像你。（v0.3 推荐改用 update_profile，本方法保留兼容）
        """
        conv_text = self._build_conv_text(new_chats, max_logs=50)

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
