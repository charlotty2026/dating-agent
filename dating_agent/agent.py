"""
主控Agent - 串联蒸馏+筛选+聊天的完整流程

使用流程：
1. 准备聊天记录（从交友平台导出）
2. 用Distiller蒸馏出性格档案
3. 创建Agent
4. 喂profile列表，Agent自动筛选
5. 筛选通过的，Agent自动聊天
6. 聊得好的，推给你真人接管

⚠️ 伦理声明：
本项目用于"AI帮你初筛"，不建议AI伪装成你进行深度情感交流。
建议在合适时机向对方坦白使用了AI辅助筛选。
"""

import json
import uuid
from typing import Optional
from .llm_client import LLMClient, LLMConfig
from .profile import PersonalityProfile
from .filter_engine import FilterEngine
from .chat_engine import ChatEngine
from .distill import Distiller


class DatingAgent:
    """
    相亲Agent - 主控

    核心能力：
    1. 蒸馏自己：聊天记录→性格档案（长期记忆）
    2. 智能筛选：按性格档案判断要不要右滑
    3. 自动聊天：接LLM API，自然对话
    4. 对话评估：聊完打分，推荐见面/继续聊/放弃
    """

    def __init__(self, profile: PersonalityProfile,
                 llm: Optional[LLMClient] = None):
        self.profile = profile
        self.llm = llm
        self.filter_engine = FilterEngine(profile, llm)
        self.chat_engine = ChatEngine(profile, llm)
        self.distiller = Distiller(llm) if llm else None
        self.matches = []       # 初筛通过
        self.shortlisted = []   # 聊天后推荐见面
        self.dropped = []       # 聊天后放弃

    @classmethod
    def from_chat_logs(cls, chat_logs: list, basic_info: dict,
                       llm: Optional[LLMClient] = None) -> "DatingAgent":
        """
        从聊天记录直接创建Agent（蒸馏+初始化一步到位）

        Args:
            chat_logs: 你的聊天记录
            basic_info: {"name": "...", "gender": "...", "age": 27}
            llm: LLM客户端

        Returns:
            DatingAgent
        """
        if not llm:
            raise ValueError("蒸馏功能需要LLM API！")

        print(f"🧪 正在蒸馏你的性格档案...")
        profile = cls._distill_profile(llm, chat_logs, basic_info)
        print(f"✅ 蒸馏完成！性格标签: {', '.join(profile.personality_tags[:5])}")

        return cls(profile, llm)

    @staticmethod
    def _distill_profile(llm: LLMClient, chat_logs: list,
                         basic_info: dict) -> PersonalityProfile:
        """内部方法：蒸馏性格档案"""
        distiller = Distiller(llm)
        return distiller.distill(chat_logs, basic_info)

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
        if not self.llm:
            print("⚠️ 聊天功能需要接LLM API！")
            print("请设置环境变量后重试：")
            print("  export LLM_API_KEY='your-key'")
            print("  export LLM_BASE_URL='https://api.deepseek.com/v1'")
            return []

        if verbose:
            print(f"\n💬 AI开始自动聊天 [LLM模式] (每人对聊{rounds}轮)\n")

        for match in self.matches:
            match_id = str(match.get("id", str(uuid.uuid4())))
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
