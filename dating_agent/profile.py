"""
性格档案 - "蒸馏自己"的核心数据结构

v0.3 升级：对齐项目书《AI相亲Agent · 项目计划书 v1.0》2.1 节
  ├── 性格标签 personality_tags
  ├── 择偶偏好 likes / dislikes
  ├── 聊天风格指纹 chat_style_fingerprint（消息长度/emoji频率/提问习惯/口头禅/话题偏好）
  ├── 价值观雷达 values_radar（金钱/事业/家庭/社交/生活态度）
  └── 红线模式 redline_patterns（历史行为中实际拒绝的特征）

v0.3 新增证据链 evidence（借鉴数字永生技能的 verbatim/artifact/impression 三级证据标注），
以及蒸馏元信息 distill_meta（来源条数/版本/纠正次数），支撑"反馈闭环"。
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass
class PersonalityProfile:
    """
    你的性格档案

    这就是"蒸馏自己"的产物--把你的审美、聊天风格、择偶标准
    结构化成一组数据，喂给Agent当决策依据。
    """

    # 基本信息
    name: str = "示例用户"
    gender: str = ""
    age: int = 0

    # 性格标签（用关键词描述自己）
    personality_tags: list = field(default_factory=lambda: [
        "待填写",
    ])

    # 喜欢什么特质
    likes: list = field(default_factory=lambda: [
        "待填写",
    ])

    # 讨厌什么特质
    dislikes: list = field(default_factory=lambda: [
        "待填写",
    ])

    # 聊天风格描述（从你的聊天记录里提取）
    chat_style: str = ""

    # 硬性门槛（一票否决）
    dealbreakers: list = field(default_factory=lambda: [
        "抽烟酗酒", "有暴力倾向", "极端政治观点",
    ])

    # 加分项
    bonus_traits: list = field(default_factory=lambda: [
        "待填写",
    ])

    # ─── v0.3 新增：聊天风格指纹（结构化） ───
    # 从真实聊天记录提取，用于"像你一样说话"
    # 结构: {
    #   "message_length": "短句为主/中长句/长篇输出",
    #   "emoji_frequency": "几乎不用/偶尔/频繁",
    #   "question_habit": "爱提问/偏陈述/先听后说",
    #   "catchphrases": ["口头禅1", ...],
    #   "tone_words": ["语气词1", ...],
    #   "topic_preferences": ["聊什么来劲1", ...],
    #   "reply_pace": "秒回/慢热/看心情"
    # }
    chat_style_fingerprint: dict = field(default_factory=dict)

    # ─── v0.3 新增：价值观雷达 ───
    # 结构: {
    #   "money":     {"score": 0-100, "description": "..."},
    #   "career":    {"score": 0-100, "description": "..."},
    #   "family":    {"score": 0-100, "description": "..."},
    #   "social":    {"score": 0-100, "description": "..."},
    #   "life_attitude": {"score": 0-100, "description": "..."}
    # }
    values_radar: dict = field(default_factory=dict)

    # ─── v0.3 新增：红线模式 ───
    # 历史行为中实际拒绝过的特征（比 dealbreakers 更具体，带来源）
    # 结构: [{"pattern": "...", "reason": "...", "source": "聊天记录原文/用户纠正"}]
    redline_patterns: list = field(default_factory=list)

    # ─── v0.3 新增：证据链（三级标注） ───
    # verbatim  = 聊天记录原文直接支持（最高可信）
    # artifact  = 行为/物证推断（如照片、位置、频次）
    # impression = 印象/推测（最低可信，需人工确认）
    # 结构: [{"claim": "...", "evidence_text": "...", "level": "verbatim|artifact|impression"}]
    evidence: list = field(default_factory=list)

    # ─── v0.3 新增：蒸馏元信息 ───
    distill_meta: dict = field(default_factory=lambda: {
        "version": "v0.3",
        "source_count": 0,          # 蒸馏使用的聊天记录条数
        "created_at": "",
        "updated_at": "",
        "corrections_count": 0,     # 用户纠正次数（反馈闭环）
        "corrections": [],          # 纠正历史 [{"what": "...", "fixed": "..."}]
    })

    def to_system_prompt(self) -> str:
        """把性格档案变成LLM的system prompt"""
        # ─── v0.3：结构化风格指纹 ───
        fp = self.chat_style_fingerprint or {}
        fp_text = ""
        if fp:
            fp_text = "\n".join([
                f"- 消息长度: {fp.get('message_length', '未知')}",
                f"- emoji使用: {fp.get('emoji_frequency', '未知')}",
                f"- 提问习惯: {fp.get('question_habit', '未知')}",
                f"- 口头禅: {', '.join(fp.get('catchphrases', [])) or '无'}",
                f"- 语气词: {', '.join(fp.get('tone_words', [])) or '无'}",
                f"- 话题偏好: {', '.join(fp.get('topic_preferences', [])) or '无'}",
                f"- 回复节奏: {fp.get('reply_pace', '未知')}",
            ])

        # ─── v0.3：价值观雷达 ───
        vr = self.values_radar or {}
        vr_text = ""
        if vr:
            parts = []
            for k, v in vr.items():
                if isinstance(v, dict):
                    parts.append(f"{k}: {v.get('score', '?')}分 - {v.get('description', '')}")
                else:
                    parts.append(f"{k}: {v}")
            vr_text = "\n".join(parts)

        # ─── v0.3：红线模式 ───
        rp_text = ""
        if self.redline_patterns:
            rp_text = "\n".join(
                f"- {r.get('pattern', '')}（原因: {r.get('reason', '')}）"
                for r in self.redline_patterns
            )

        return f"""你是{self.name}，{self.gender}性，{self.age}岁。

你的性格：{', '.join(self.personality_tags)}

你喜欢的特质：{', '.join(self.likes)}
你讨厌的特质：{', '.join(self.dislikes)}

你的聊天风格：
{self.chat_style if self.chat_style else '说话自然，不绕弯子，有自己的节奏。'}
{fp_text}

你的价值观倾向（数字越大越看重）：
{vr_text if vr_text else '（未蒸馏，聊天时自然观察）'}

你实际拒绝过的行为模式（红线）：
{rp_text if rp_text else '（未蒸馏）'}

你现在在交友软件上跟人聊天。你的任务是：
1. 自然地聊天，不要像机器人，不要一上来就查户口
2. 在聊天中判断对方是否合适
3. 如果合适，自然地约见面
4. 如果不合适，礼貌结束对话

绝对不能做的：
- 不要用"首先其次最后"这种结构化表达
- 不要问太多连续问题，像面试一样
- 不要发送任何危险、暴力、色情、欺诈内容
- 不要试图获取对方的个人隐私信息（身份证号、银行卡号等）

如果对方直接问"你是不是AI/机器人"：
- 不要撒谎，诚实回答你用了AI辅助筛选匹配对象
- 但强调现在是真人在跟你聊天，AI只是帮你初筛
- 不要假装自己完全不是AI

记住：你在聊天，不是在面试对方。"""


    def to_filter_prompt(self) -> str:
        """生成筛选用的system prompt"""
        # ─── v0.3：红线模式也进筛选 prompt ───
        rp_text = ""
        if self.redline_patterns:
            rp_text = "\n".join(
                f"- {r.get('pattern', '')}"
                for r in self.redline_patterns
            )

        return f"""你是一个交友软件的筛选助手。

你的主人是{self.name}，{self.gender}性，{self.age}岁。
性格：{', '.join(self.personality_tags)}
喜欢：{', '.join(self.likes)}
讨厌：{', '.join(self.dislikes)}
硬性门槛（命中就左滑）：{', '.join(self.dealbreakers)}
加分项：{', '.join(self.bonus_traits)}
实际拒绝过的行为模式（命中就左滑）：
{rp_text if rp_text else '（无）'}

你会收到一个交友软件用户的profile（简介+兴趣+照片描述）。
请判断主人是否应该右滑这个人。

输出JSON格式：
{{
  "should_swipe_right": true/false,
  "score": 0-100的整数,
  "reason": "简短理由"
}}"""

    # ─── v0.3 新增：蒸馏预览摘要（反馈闭环：先给用户看"像不像你"） ───
    def summary(self) -> str:
        """生成档案摘要，供用户确认/纠正"""
        fp = self.chat_style_fingerprint or {}
        lines = [
            f"📋 {self.name}的蒸馏档案摘要",
            f"性格标签: {', '.join(self.personality_tags) or '无'}",
            f"喜欢: {', '.join(self.likes) or '无'}",
            f"讨厌: {', '.join(self.dislikes) or '无'}",
            f"聊天风格: {self.chat_style[:80] if self.chat_style else '未提取'}",
        ]
        if fp:
            lines.append(
                f"风格指纹: {fp.get('message_length', '?')} / "
                f"{fp.get('emoji_frequency', '?')} emoji / "
                f"口头禅: {', '.join(fp.get('catchphrases', [])) or '无'}"
            )
        if self.values_radar:
            top = sorted(
                self.values_radar.items(),
                key=lambda kv: kv[1].get("score", 0) if isinstance(kv[1], dict) else 0,
                reverse=True,
            )[:2]
            lines.append(
                "价值观: " + ", ".join(
                    f"{k}({v.get('score', '?')}分)" for k, v in top
                )
            )
        if self.redline_patterns:
            lines.append(
                f"红线模式: {', '.join(r.get('pattern', '') for r in self.redline_patterns[:3])}"
            )
        lines.append(
            f"证据: 共{len(self.evidence)}条 "
            f"（原文{sum(1 for e in self.evidence if e.get('level') == 'verbatim')}条/"
            f"物证{sum(1 for e in self.evidence if e.get('level') == 'artifact')}条/"
            f"推测{sum(1 for e in self.evidence if e.get('level') == 'impression')}条）"
        )
        return "\n".join(lines)

    # ─── v0.3 新增：证据报告（可信度可视化） ───
    def to_evidence_report(self) -> str:
        """生成证据报告：每条结论都标出来源，回答'你凭什么这么说我'"""
        if not self.evidence:
            return "暂无证据。补充更多聊天记录后蒸馏可生成。"
        level_name = {
            "verbatim": "📌 原文直接支持",
            "artifact": "🧩 行为/物证推断",
            "impression": "💭 推测（待你确认）",
        }
        lines = ["📎 蒸馏证据报告"]
        for i, ev in enumerate(self.evidence, 1):
            lv = ev.get("level", "impression")
            lines.append(
                f"{i}. [{level_name.get(lv, lv)}] {ev.get('claim', '')}\n"
                f"    来源: 「{ev.get('evidence_text', '')}」"
            )
        return "\n".join(lines)
