"""
测试筛选引擎 - 规则匹配模式
"""

import pytest
from dating_agent.filter_engine import FilterEngine
from dating_agent.profile import PersonalityProfile


class TestFilterEngineRules:
    """测试规则匹配模式"""

    @pytest.fixture
    def sample_profile(self):
        return PersonalityProfile(
            name="测试",
            gender="女",
            age=27,
            personality_tags=["独立", "有主见"],
            likes=["有幽默感", "情绪稳定"],
            dislikes=["大男子主义"],
            dealbreakers=["抽烟酗酒", "暴力倾向"],
            bonus_traits=["喜欢小动物", "爱看书"],
        )

    @pytest.fixture
    def filter_engine(self, sample_profile):
        return FilterEngine(sample_profile)

    def test_hit_dealbreaker(self, filter_engine):
        """命中dealbreaker应左滑"""
        result = filter_engine._evaluate_with_rules(
            bio="我喜欢抽烟酗酒",
            interests=[],
            photo_description=""
        )
        assert result["should_swipe_right"] is False
        assert result["score"] == 0
        assert "命中硬性门槛" in result["reason"]

    def test_negative_dealbreaker(self, filter_engine):
        """否定句不应命中dealbreaker"""
        result = filter_engine._evaluate_with_rules(
            bio="我不抽烟酗酒，很健康",
            interests=[],
            photo_description=""
        )
        # 不应该因为"抽烟酗酒"被拦截
        assert "命中硬性门槛" not in result["reason"]

    def test_match_like(self, filter_engine):
        """命中like应加分"""
        result = filter_engine._evaluate_with_rules(
            bio="我很有幽默感，情绪也很稳定",
            interests=[],
            photo_description=""
        )
        assert result["score"] > 50

    def test_match_dislike(self, filter_engine):
        """命中dislike应减分"""
        result = filter_engine._evaluate_with_rules(
            bio="我就是大男子主义",
            interests=[],
            photo_description=""
        )
        assert result["score"] < 50

    def test_bonus_interest(self, filter_engine):
        """bonus_traits兴趣应加分"""
        result = filter_engine._evaluate_with_rules(
            bio="我喜欢小动物",
            interests=["看书"],
            photo_description=""
        )
        # bonus_traits匹配"看书"，应加分
        assert result["score"] >= 50  # 至少50分（基础分）

    def test_normal_profile_pass(self, filter_engine):
        """正常profile应右滑"""
        result = filter_engine._evaluate_with_rules(
            bio="我喜欢看书和旅行，有幽默感",
            interests=["旅行", "看书"],
            photo_description="公园散步照"
        )
        # 命中like和bonus_traits，应右滑
        assert result["should_swipe_right"] is True
