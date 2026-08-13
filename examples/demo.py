"""
Demo - 蒸馏自己+筛选+聊天的完整流程

注意：
- 仿真模式只支持筛选，不支持聊天
- 聊天必须接LLM API
- 蒸馏必须接LLM API
"""

from dating_agent import DatingAgent, PersonalityProfile
from dating_agent.llm_client import LLMClient, LLMConfig


def main():
    # ========================================
    # 方案A：仿真模式（只筛选，不聊天）
    # ========================================
    print("=== 方案A：仿真模式（只筛选） ===\n")

    my_profile = PersonalityProfile(
        name="示例用户",
        gender="女",
        age=27,
        personality_tags=["独立", "有主见", "喜欢深度交流"],
        likes=["有幽默感", "情绪稳定", "有自己热爱的事情"],
        dislikes=["大男子主义", "没文化装文化", "情绪不稳定"],
        dealbreakers=["抽烟酗酒", "有暴力倾向"],
        bonus_traits=["喜欢小动物", "爱看书", "会做饭"],
    )

    sample_profiles = [
        {
            "id": "1001",
            "name": "小明",
            "bio": "喜欢打游戏和看动漫，性格开朗，找个能一起玩的",
            "interests": ["游戏", "动漫"],
            "photo_description": "自拍，背景是电脑桌",
        },
        {
            "id": "1002",
            "name": "阿杰",
            "bio": "独立音乐人，喜欢村上春树和旅行，情绪稳定，养了一只猫",
            "interests": ["音乐", "文学", "旅行"],
            "photo_description": "在书店看书的照片",
            "simulated_replies": [
                "哈哈你也喜欢村上春树吗？我最喜欢《挪威的森林》",
                "我养了只橘猫叫胖虎，你喜欢猫吗？",
                "最近在读一本关于日本文化的书，挺有意思的",
                "周末一般去演出或者看书，你呢？",
                "感觉跟你聊天挺开心的，要不要出来喝杯咖啡？",
            ],
        },
    ]

    agent = DatingAgent(my_profile)  # 无API = 规则模式
    agent.swipe(sample_profiles)

    # ========================================
    # 方案B：LLM模式（蒸馏+筛选+聊天）
    # ========================================
    print("\n\n=== 方案B：LLM模式（蒸馏+筛选+聊天） ===\n")
    print("⚠️ 本方案需要LLM API，请先设置环境变量：")
    print("  export LLM_API_KEY='your-key'")
    print("  export LLM_BASE_URL='https://api.deepseek.com/v1'")
    print("  export LLM_MODEL='deepseek-chat'\n")

    try:
        llm = LLMClient(LLMConfig.from_env())
        print(f"✅ LLM连接成功: {llm.config.model}")
    except Exception as e:
        print(f"❌ LLM连接失败: {e}")
        print("跳过方案B，直接退出")
        return

    # 示例聊天记录（真实场景从交友平台导出）
    sample_chat_logs = [
        {"role": "me", "content": "哈哈哈哈你也喜欢这个啊"},
        {"role": "them", "content": "对啊，我也觉得超有意思的"},
        {"role": "me", "content": "那你平时还喜欢干嘛"},
        {"role": "them", "content": "看书旅行，你呢"},
        {"role": "me", "content": "我啊，看书发呆撸猫，三件套"},
    ]

    basic_info = {"name": "示例用户", "gender": "女", "age": 27}

    # 蒸馏
    print("🧪 正在蒸馏性格档案...")
    distiller = agent.distiller
    profile = distiller.distill(sample_chat_logs, basic_info)
    print(f"✅ 蒸馏完成！")
    print(f"   性格标签: {', '.join(profile.personality_tags)}")
    print(f"   喜欢: {', '.join(profile.likes)}")
    print(f"   讨厌: {', '.join(profile.dislikes)}\n")

    # 用蒸馏出的档案创建新Agent
    agent2 = DatingAgent(profile, llm=llm)
    agent2.swipe(sample_profiles)
    agent2.chat_with_matches(rounds=3)
    agent2.report()


if __name__ == "__main__":
    main()
