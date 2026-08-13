"""
性格档案持久化 - 保存和加载蒸馏结果
"""

import json
from pathlib import Path
from typing import Optional
from .profile import PersonalityProfile


class ProfilePersistence:
    """性格档案持久化"""

    def __init__(self, storage_dir: str = ".dating_agent_cache"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)

    def save(self, profile: PersonalityProfile, filename: Optional[str] = None) -> Path:
        """
        保存性格档案

        Args:
            profile: 性格档案
            filename: 文件名（可选，默认用名字+时间戳）

        Returns:
            保存路径
        """
        if filename is None:
            import time
            filename = f"{profile.name}_{int(time.time())}.json"

        filepath = self.storage_dir / filename

        data = {
            "name": profile.name,
            "gender": profile.gender,
            "age": profile.age,
            "personality_tags": profile.personality_tags,
            "likes": profile.likes,
            "dislikes": profile.dislikes,
            "chat_style": profile.chat_style,
            "dealbreakers": profile.dealbreakers,
            "bonus_traits": profile.bonus_traits,
            "created_at": int(time.time()),
        }

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return filepath

    def load(self, filename: str) -> PersonalityProfile:
        """
        加载性格档案

        Args:
            filename: 文件名（在.storage_dir目录下）

        Returns:
            PersonalityProfile
        """
        filepath = self.storage_dir / filename

        if not filepath.exists():
            raise FileNotFoundError(f"找不到文件: {filepath}")

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        return PersonalityProfile(
            name=data["name"],
            gender=data["gender"],
            age=data["age"],
            personality_tags=data.get("personality_tags", []),
            likes=data.get("likes", []),
            dislikes=data.get("dislikes", []),
            chat_style=data.get("chat_style", ""),
            dealbreakers=data.get("dealbreakers", []),
            bonus_traits=data.get("bonus_traits", []),
        )

    def list_profiles(self) -> list:
        """列出所有保存的性格档案"""
        profiles = []
        for filepath in self.storage_dir.glob("*.json"):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                profiles.append({
                    "filename": filepath.name,
                    "name": data["name"],
                    "created_at": data.get("created_at", 0),
                })
            except:
                pass
        return sorted(profiles, key=lambda x: x["created_at"], reverse=True)
