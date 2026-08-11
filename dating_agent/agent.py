"""
主控Agent - 串联筛选+聊天+评估的完整流程
"""

import json
from typing import Optional
from .llm_client import LLMClient, LLMConfig
from .profile import PersonalityProfile
from .filter_engine import FilterEngine
from .chat_engine import ChatEngine


class DatingAgent:
    """
    相亲Agent - 主控

    使用流程：
    1. 创建你的性格档案（手动填 or 用Distiller从聊天记录蒸馏）
    2. 创建Agent
    3. 喂profile列表，Agent自动筛选
    4. 筛选通过的，Agent自动聊天
    5. 聊得好的，推给你真人接管

    ⚠️ 伦理声明：
    本项目用于"AI帮你初筛"，不建议AI伪装成你进行深度情感交流。
    建议在合适时机向对方坦白使用了AI辅助筛选。
    """

    def __init__(self, profile: PersonalityProfile,
                 llm: Optional[LLMClient] = None):
        self.profile = profile
        self.llm = llm
        self.filter_engine = FilterEngine(profile, llm)
        self.chat_engine = ChatEngine(profile, llm)
        self.matches = []       # 初筛通过
        self.shortlisted = []   # 聊天后推荐见面
        self.dropped = []       # 聊天后放弃

    def swipe(self, profiles: list[dict], verbose: bool = True) -> list:
        """
        批量筛选profile

        Args:
            profiles: [{"id", "name", "bio", "interests", "photo_description"}, ...]
            verbose: 打印过程

        Returns:
            初筛通过的profile列表
        """
        if verbose:
            mode = "LLM模式" if self.llm else "规则模式(无API)"
            print(f"🤖 {self.profile.name}的相亲Agent启动 [{mode}]")
            print(f"📋 性格档案: {', '.join(self.profile.personality_tags)}")
            print(f"📊 收到 {len(profiles)} 个profile\n")

        for i, p in enumerate(profiles):
            result = self.filter_engine.evaluate(
                bio=p.get("bio", ""),
                interests=p.get("interests", []),
                photo_description=p.get("photo_description", ""),
            )

            if result["should_swipe_right"]:
                self.matches.append(p)
                if verbose:
                    print(f"  ✅ 右滑 #{i+1}: {p.get('name', '匿名')} "
                          f"(评分: {result['score']}/100)")
                    print(f"     原因: {result['reason']}")
            else:
                if verbose:
                    print(f"  ❌ 左滑 #{i+1}: {p.get('name', '匿名')} "
                          f"(评分: {result['score']}/100)")

        if verbose:
            print(f"\n📊 初筛结果: {len(profiles)}人 → 右滑 {len(self.matches)}人")

        return self.matches

    def chat_with_matches(self, rounds: int = 5,
                          verbose: bool = True) -> list:
        """
        跟所有匹配的人聊天

        Args:
            rounds: 每人聊几轮
            verbose: 打印过程

        Returns:
            推荐见面的候选人列表
        """
        if verbose:
            mode = "LLM" if self.llm else "仿真"
            print(f"\n💬 AI开始自动聊天 [{mode}模式] "
                  f"(每人对聊{rounds}轮)\n")

        for match in self.matches:
            match_id = str(match.get("id", id(match)))
            name = match.get("name", "匿名")

            if verbose:
                print(f"{'='*40}")
                print(f"💬 与 {name} 聊天中...")

            # AI发第一条
            opener = self.chat_engine.start_conversation(match_id)
            if verbose:
                print(f"  🤖 你: {opener}")

            for r in range(rounds):
                # 模拟对方回复（真实场景从平台API获取）
                their_reply = match.get("simulated_replies", ["嗯嗯，你呢？"])[r] \
                    if "simulated_replies" in match \
                    else f"模拟回复第{r+1}轮"

                if verbose:
                    print(f"  👤 对方: {their_reply}")

                ai_reply = self.chat_engine.reply(match_id, their_reply)
                if verbose:
                    print(f"  🤖 你: {ai_reply}")

            # 评估
            result = self.chat_engine.evaluate(match_id)
            if verbose:
                print(f"  📊 评估: {result['score']}/100 - {result['reason']}")

            if result.get("should_meet"):
                match["eval_score"] = result["score"]
                match["eval_reason"] = result["reason"]
                self.shortlisted.append(match)
                if verbose:
                    print(f"  ⭐ 推荐见面！")
            elif result.get("should_drop"):
                self.dropped.append(match)
                if verbose:
                    print(f"  💤 建议放弃")
            else:
                if verbose:
                    print(f"  🤔 可以再聊聊")

            if verbose:
                print()

        return self.shortlisted

    def report(self) -> dict:
        """输出运行报告"""
        print("=" * 50)
        print(f"📋 {self.profile.name}的相亲Agent运行报告")
        print("=" * 50)
        print(f"初筛通过: {len(self.matches)}人")
        print(f"推荐见面: {len(self.shortlisted)}人")
        print(f"建议放弃: {len(self.dropped)}人")

        if self.shortlisted:
            print(f"\n🎯 推荐你真人见面的候选人:")
            for i, s in enumerate(self.shortlisted):
                print(f"  {i+1}. {s.get('name', '匿名')} "
                      f"- 匹配度: {s.get('eval_score', 0)}/100")
                print(f"     理由: {s.get('eval_reason', '')}")

        print(f"\n💡 接下来: 真人见面，你自己判断~")
        print(f"\n⚠️ 伦理提醒: 建议见面时坦白使用了AI辅助初筛")

        return {
            "total_matches": len(self.matches),
            "shortlisted": self.shortlisted,
            "dropped": len(self.dropped),
        }

    def save_results(self, filepath: str):
        """保存结果到JSON"""
        data = {
            "profile": {
                "name": self.profile.name,
                "tags": self.profile.personality_tags,
            },
            "matches": len(self.matches),
            "shortlisted": [
                {
                    "name": m.get("name", "匿名"),
                    "score": m.get("eval_score", 0),
                    "reason": m.get("eval_reason", ""),
                }
                for m in self.shortlisted
            ],
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 结果已保存到 {filepath}")
