"""
LLM客户端 - 统一接口，支持OpenAI/DeepSeek/火山引擎等兼容API
"""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM配置"""
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    model: str = "deepseek-chat"
    temperature: float = 0.8
    max_tokens: int = 1024

    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1"),
            model=os.getenv("LLM_MODEL", "deepseek-chat"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.8")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1024")),
        )

    @classmethod
    def from_dict(cls, d: dict):
        return cls(
            api_key=d.get("api_key", ""),
            base_url=d.get("base_url", "https://api.deepseek.com/v1"),
            model=d.get("model", "deepseek-chat"),
            temperature=d.get("temperature", 0.8),
            max_tokens=d.get("max_tokens", 1024),
        )


class LLMClient:
    """LLM客户端封装"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self._client = None

    @property
    def client(self):
        """懒加载openai客户端"""
        if self._client is None:
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError(
                    "需要安装openai库: pip install openai"
                )
            self._client = OpenAI(
                api_key=self.config.api_key,
                base_url=self.config.base_url,
            )
        return self._client

    def chat(self, messages: list, **kwargs) -> str:
        """
        调用LLM对话

        Args:
            messages: [{"role": "system/user/assistant", "content": "..."}]
            **kwargs: 覆盖默认参数

        Returns:
            LLM回复文本
        """
        params = {
            "model": kwargs.get("model", self.config.model),
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        response = self.client.chat.completions.create(**params)
        return response.choices[0].message.content

    def chat_json(self, messages: list, **kwargs) -> dict:
        """
        调用LLM并解析JSON输出

        Returns:
            解析后的dict
        """
        import json

        text = self.chat(messages, **kwargs)

        # 尝试提取JSON
        # 先找```json ... ```块
        if "```json" in text:
            start = text.index("```json") + 7
            end = text.index("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.index("```") + 3
            end = text.index("```", start)
            text = text[start:end].strip()

        # 去掉可能的markdown
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # 尝试找到第一个{和最后一个}
            first = text.find("{")
            last = text.rfind("}")
            if first != -1 and last != -1:
                return json.loads(text[first:last+1])
            raise ValueError(f"LLM输出无法解析为JSON: {text[:200]}")
