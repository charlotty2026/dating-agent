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
        self.compiled_patterns = [
            re.compile(p, re.IGNORECASE) for p in DANGEROUS_PATTERNS
        ]

    def check(self, text: str) -> tuple[bool, str]:
        """
        检查文本是否安全

        Returns:
            (is_safe, reason)
        """
        if not self.enabled:
            return True, ""

        for pattern in self.compiled_patterns:
            if pattern.search(text):
                return False, f"检测到危险内容: {pattern.pattern}"

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
