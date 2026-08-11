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
- **双模式**：有 API key 用真 LLM，没有就用规则引擎仿真

## 快速开始

### 安装

```bash
git clone https://github.com/charlotty2026/dating-agent.git
cd dating-agent
pip install -r requirements.txt
```

### 仿真模式（不需要 API key）

```bash
python examples/demo.py
```

### LLM 模式（接真 API）

```bash
# 1. 复制配置文件
cp config.example.yaml config.yaml

# 2. 填入你的 API key（支持 DeepSeek / OpenAI / 火山引擎等）
# 编辑 config.yaml

# 3. 设置环境变量
export LLM_API_KEY="your-key"
export LLM_BASE_URL="https://api.deepseek.com/v1"
export LLM_MODEL="deepseek-chat"

# 4. 运行（修改 demo.py 加上 llm 参数）
```

### 用代码

```python
from dating_agent import DatingAgent, PersonalityProfile, LLMClient, LLMConfig

# 你的性格档案
profile = PersonalityProfile(
    name="你的名字",
    gender="女",
    age=27,
    personality_tags=["独立", "有主见", "喜欢深度交流"],
    likes=["有幽默感", "情绪稳定"],
    dislikes=["大男子主义", "情绪不稳定"],
)

# 接 LLM（不传 llm 就是仿真模式）
llm = LLMClient(LLMConfig.from_env())
agent = DatingAgent(profile, llm=llm)

# 筛选
agent.swipe(profiles)

# 聊天
agent.chat_with_matches(rounds=5)

# 出报告
agent.report()
```

### 蒸馏自己（从聊天记录提取风格）

```python
from dating_agent import Distiller, LLMClient, LLMConfig

llm = LLMClient(LLMConfig.from_env())
distiller = Distiller(llm)

# 你的聊天记录
chat_logs = [
    {"role": "me", "content": "哈哈你说的那个我也觉得"},
    {"role": "them", "content": "真的吗？那你平时喜欢干嘛"},
    {"role": "me", "content": "看书发呆撸猫，三件套"},
    # ... 更多记录
]

profile = distiller.distill(chat_logs, {"name": "你", "gender": "女", "age": 27})
print(profile.chat_style)  # AI提取出的你的说话风格
```

## 项目结构

```
dating-agent/
├── dating_agent/
│   ├── __init__.py        # 包入口
│   ├── profile.py         # 性格档案
│   ├── llm_client.py      # LLM客户端（OpenAI兼容）
│   ├── filter_engine.py   # 筛选引擎（规则+LLM双模式）
│   ├── chat_engine.py     # 聊天引擎（仿真+LLM双模式）
│   ├── distill.py         # 蒸馏自己（从聊天记录提取风格）
│   └── agent.py           # 主控Agent
├── examples/
│   └── demo.py            # 示例
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

## ⚠️ 伦理声明

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
