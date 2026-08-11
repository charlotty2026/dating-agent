"""
Demo - 不需要API key也能跑的仿真模式
"""

from dating_agent import DatingAgent
from dating_agent.profile import PersonalityProfile


def main():
    # 1. 创建性格档案（你也可以用Distiller从聊天记录蒸馏）
    my_profile = PersonalityProfile(
        name="示例用户",
        gender="女",
        age=27,
        personality_tags=[
            "独立", "有主见", "喜欢深度交流",
            "文学审美在线", "务实", "有创业精神",
        ],
        likes=["有幽默感", "情绪稳定", "有自己热爱的事情", "能接住梗"],
        dislikes=["大男子主义", "没文化装文化", "情绪不稳定", "整天打游戏"],
        dealbreakers=["抽烟酗酒", "有暴力倾向"],
        bonus_traits=["喜欢小动物", "爱看书", "会做饭", "爱旅行"],
    )

    # 2. 模拟一些profile（真实场景从交友平台API获取）
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
        {
            "id": "1003",
            "name": "大刘",
            "bio": "创业中，喜欢哲学和深度对话，会做饭",
            "interests": ["哲学", "创业", "读书", "做饭"],
            "photo_description": "咖啡厅工作照",
            "simulated_replies": [
                "你好！看到你的简介觉得挺有意思的",
                "你觉得一个人最重要的品质是什么？",
                "我也喜欢深度交流，表面聊天太无聊了",
                "周末喜欢自己做饭研究菜谱，你呢？",
                "聊了这么多感觉挺投缘的，有空出来聊聊？",
            ],
        },
        {
            "id": "1004",
            "name": "王总",
            "bio": "事业有成，就想找个听话的，抽烟喝酒应酬多",
            "interests": ["车", "表", "高尔夫"],
            "photo_description": "车里自拍，手上有烟",
        },
    ]

    # 3. 启动Agent（无API = 仿真模式，有API = 真LLM模式）
    # 要用真LLM：
    #   from dating_agent.llm_client import LLMClient, LLMConfig
    #   llm = LLMClient(LLMConfig.from_env())
    #   agent = DatingAgent(my_profile, llm=llm)

    agent = DatingAgent(my_profile)  # 仿真模式

    # 4. 筛选
    agent.swipe(sample_profiles)

    # 5. 聊天
    agent.chat_with_matches(rounds=5)

    # 6. 出报告
    agent.report()

    # 7. 保存结果
    agent.save_results("results.json")


if __name__ == "__main__":
    main()
