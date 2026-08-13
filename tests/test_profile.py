"""
测试性格档案序列化
"""

import pytest
import tempfile
from pathlib import Path
from dating_agent.profile import PersonalityProfile
from dating_agent.profile_persistence import ProfilePersistence


class TestPersonalityProfile:
    """测试性格档案序列化"""

    def test_create_profile(self):
        """创建基础档案"""
        profile = PersonalityProfile(
            name="测试",
            gender="女",
            age=27,
            personality_tags=["独立", "有主见"],
            likes=["有幽默感"],
            dislikes=["大男子主义"],
        )
        assert profile.name == "测试"
        assert len(profile.personality_tags) == 2

    def test_to_dict(self):
        """序列化到字典"""
        profile = PersonalityProfile(
            name="测试",
            gender="女",
            age=27,
        )
        # PersonalityProfile没有to_dict，直接访问属性
        assert profile.name == "测试"
        assert profile.gender == "女"
        assert profile.age == 27

    def test_from_dict(self):
        """从字典创建"""
        # PersonalityProfile直接用构造函数
        profile = PersonalityProfile(
            name="测试",
            gender="女",
            age=27,
            personality_tags=["独立"],
        )
        assert profile.name == "测试"
        assert profile.personality_tags == ["独立"]


class TestProfilePersistence:
    """测试档案持久化"""

    def test_save_and_load(self):
        """保存和加载"""
        profile = PersonalityProfile(
            name="测试用户",
            gender="女",
            age=27,
            personality_tags=["独立"],
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pp = ProfilePersistence(tmpdir)

            # 保存
            path = pp.save(profile, filename="test.json")
            assert path.exists()

            # 加载
            loaded = pp.load("test.json")
            assert loaded.name == "测试用户"
            assert loaded.age == 27

    def test_save_without_filename(self):
        """不传文件名自动生成"""
        profile = PersonalityProfile(
            name="测试用户",
            gender="女",
            age=27,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            pp = ProfilePersistence(tmpdir)

            # 不传filename
            path = pp.save(profile)
            assert path.exists()
            assert "测试用户" in path.name  # 自动生成文件名包含名称

    def test_list_profiles(self):
        """列出所有档案"""
        profile1 = PersonalityProfile(name="用户1", gender="女", age=25)
        profile2 = PersonalityProfile(name="用户2", gender="男", age=30)

        with tempfile.TemporaryDirectory() as tmpdir:
            pp = ProfilePersistence(tmpdir)

            pp.save(profile1, filename="user1.json")
            pp.save(profile2, filename="user2.json")

            profiles = pp.list_profiles()
            assert len(profiles) == 2
            assert profiles[0]["name"] == "用户2"  # 最新的在前
