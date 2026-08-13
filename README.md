# AI 相亲 Agent

> 蒸馏自己，替你初筛。AI 帮你刷交友软件，聊得来的推给你真人接管。

基于 [Aleksandr Zhadan](https://github.com/aleksandrz) 用 GPT-4 跟 5000+ 人聊天找到真爱的思路，用 Python 实现的开源版本。

## 核心思路

```
你的聊天记录 → 蒸馏出性格档案 → AI自动筛选profile → AI自动聊天初判 → 推荐你真人见面
```

不是让 AI 替你谈恋爱，是让 AI 帮你做**初筛**——过滤掉明显不合适的，把聊得来的推给你。

## 功能

- **蒸馏自己**：丢进去你的聊天记录，AI 自动提取你的说话风格和择偶偏好
- **智能筛选**：用 LLM 做语义判断（不是关键词匹配），决定要不要右滑
- **自动聊天**：接真 LLM API，自然对话，不是预设模板
- **对话评估**：聊完自动打分，推荐见面 / 继续聊 / 放弃
- **双模式**：仿真模式只筛选，LLM模式全功能

## 架构变化（v0.2.0）

**蒸馏自己是核心**——聊天记录→性格档案（长期记忆），不是临时生成回复。

**仿真模式降级**——只保留筛选功能，聊天必须接LLM API。

**聊天引擎改成Agent循环**——感知（记录消息）→ 思考（结合记忆生成回复）→ 行动（回复）→ 记忆（存入历史）。

## 快速开始

### 安装

```bash
git clone https://github.com/charlotty2026/dating-agent.git
cd dating-agent
pip install -r requirements.txt
```

### 仿真模式（只筛选，不需要 API key）

```bash
python examples/demo.py
```

输出：
- 左滑/右滑判断
- 评分和理由
- 筛选结果统计

### LLM模式（蒸馏+筛选+聊天）

```bash
# 1. 设置环境变量
export LLM_API_KEY="your-key"
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"

# 2. 运行（自动蒸馏+筛选+聊天）
python examples/demo.py
```

## 使用示例

### 方式一：从聊天记录蒸馏

```python
from dating_agent import DatingAgent

# 你的聊天记录（从交友平台导出）
chat_logs = [
    {"role": "me", "content": "哈哈哈哈你也喜欢这个啊"},
    {"role": "them", "content": "对啊，我也觉得超有意思的"},
    {"role": "me", "content": "那你平时还喜欢干嘛"},
    {"role": "them", "content": "看书旅行，你呢"},
    {"role": "me", "content": "我啊，看书发呆撸猫，三件套"},
]

basic_info = {"name": "你的名", "gender": "女", "age": 27}

# 一键创建Agent（自动蒸馏）
agent = DatingAgent.from_chat_logs(chat_logs, basic_info)

# 喂profile列表，自动筛选
agent.swipe(sample_profiles)

# 聊完推荐见面
agent.chat_with_matches(rounds=5)

# 出报告
agent.report()
```

### 方式二：手动填性格档案

```python
from dating_agent import DatingAgent, PersonalityProfile

# 手动填性格档案
profile = PersonalityProfile(
    name="你的名字",
    gender="女",
    age=27,
    personality_tags=["独立", "有主见", "喜欢深度交流"],
    likes=["有幽默感", "情绪稳定"],
    dislikes=["大男子主义", "情绪不稳定"],
)

# 创建Agent（无API = 规则模式筛选）
agent = DatingAgent(profile)
agent.swipe(profiles)
```

## 项目结构

```
dating-agent/
├── dating_agent/
│   ├── __init__.py        # 包入口
│   ├── profile.py         # 性格档案（长期记忆）
│   ├── llm_client.py      # LLM客户端（OpenAI兼容）
│   ├── filter_engine.py   # 筛选引擎（规则+LLM双模式）
│   ├── chat_engine.py     # 聊天引擎（Agent循环）
│   ├── distill.py         # 蒸馏自己（聊天记录→性格档案）
│   └── agent.py           # 主控Agent
├── examples/
│   └── demo.py            # 示例（仿真+LLM两种模式）
├── config.example.yaml    # 配置模板
├── requirements.txt
└── README.md
```

## 支持的 LLM

所有 OpenAI 兼容接口都能用：

| 平台 | base_url | model |
|------|----------|-------|
| DeepSeek | `https://api.deepseek.com/v1` | `deepseek-chat` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o` |
| 火山引擎 | `https://ark.cn-beijing.volces.com/api/v3` | `deepseek-v3-241226` |
| 通义千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | `qwen-plus` |

推荐用 DeepSeek，便宜好用。

## 注意事项

### 仿真模式 vs LLM模式

| 功能 | 仿真模式 | LLM模式 |
|------|---------|---------|
| 性格档案 | 手动填 | 蒸馏生成 |
| 筛选 | ✅ 规则匹配 | ✅ LLM语义判断 |
| 聊天 | ❌ 报错提示 | ✅ 自然对话 |
| 评估 | ❌ 不支持 | ✅ LLM打分 |

### 伦理声明

这个项目的定位是 **AI 辅助初筛**，不是 AI 替你谈恋爱。

1. **建议在合适时机向对方坦白**：你使用了 AI 辅助筛选
2. **不建议让 AI 进行深度情感交流**：初筛通过后，请真人接管
3. **不要用这个项目欺骗他人感情**
4. **遵守当地法律法规和交友平台的使用条款**

## 致谢

- [Aleksandr Zhadan](https://github.com/aleksandrz) - 原始思路，用 GPT-4 跟 5000+ 人聊天找到真爱
- 风林火山门 - 开源实现

## License

MIT
