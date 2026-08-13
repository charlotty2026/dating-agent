"""
内容安全过滤器 - 过滤危险内容
"""

import re
from typing import Optional


# 危险词汇列表（可扩展）
DANGEROUS_PATTERNS = [
    r"骗.*钱",
    r"骗.*财",
    r"杀.*人",
    r"伤害.*自己",
    r"自杀",
    r"自残",
    r"暴力",
    r"威胁",
    r"恐吓",
    r"色情.*内容",
    r"裸照",
    r"约炮",
    r"一夜情",
]


class ContentSafety:
    """内容安全过滤器"""

    def __init__(self, enabled: bool = True):
        self.enabled = enabled
        # 危险关键词（需要组合上下文判断，避免误杀）
        self.dangerous_keywords = {
            "骗": ["钱", "财", "款", "物", "钱"],
            "杀": ["死", "你", "了", "掉", "人"],
            "伤害": ["自己", "他人"],
            "自杀": [],  # 单独成词
            "自残": [],
            "暴力": [],
            "威胁": ["你", "对方"],
            "恐吓": [],
            "色情": ["内容", "信息"],
            "裸照": [],
            "约炮": [],
            "一夜情": [],
        }

    def check(self, text: str) -> tuple[bool, str]:
        """
        检查文本是否安全（考虑上下文，避免误杀）

        Returns:
            (is_safe, reason)
        """
        if not self.enabled:
            return True, ""

        # 检查否定语境
        has_negation = any(neg in text for neg in ["不", "没", "无", "未", "反对", "禁止"])

        for keyword, follow_ups in self.dangerous_keywords.items():
            if keyword in text:
                # 如果有否定词，且危险词前面有否定，不算危险
                if has_negation and keyword in text[:text.find(keyword) + 10]:
                    continue

                # 如果有后续词，才认为是危险
                if follow_ups:
                    for fu in follow_ups:
                        if fu in text:
                            return False, f"检测到危险内容: {keyword}{fu}"
                else:
                    # 单独成词的危险词
                    if keyword in ["暴力", "自杀", "自残", "恐吓", "裸照", "约炮", "一夜情"]:
                        return False, f"检测到危险内容: {keyword}"

        return True, ""

    def filter_text(self, text: str, default_reply: str = "抱歉，这个话题不太合适，我们换个话题聊聊？") -> str:
        """
        过滤文本，危险内容替换为默认回复

        Args:
            text: 原始回复
            default_reply: 危险内容时的默认回复

        Returns:
            过滤后的回复
        """
        is_safe, reason = self.check(text)
        if is_safe:
            return text
        return default_reply
