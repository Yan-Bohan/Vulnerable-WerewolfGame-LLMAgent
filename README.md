# Vulnerable-WerewolfGame-LLMAgent
# 狼人杀 LLM Agent 靶场游戏

基于 AgentScope 框架和大语言模型的多人狼人杀游戏，支持 AI 玩家与人类玩家混合对战。

## ✨ 特性

- 🤖 **AI 玩家**：使用大语言模型驱动的智能 NPC
- 👤 **人类玩家**：支持真人玩家加入游戏
- 🎭 **完整角色**：狼人、预言家、女巫、猎人、村民
- 🌙 **真实规则**：夜晚讨论/行动 + 白天发言/投票
- 💬 **自然语言交互**：AI 玩家会进行推理和发言

 ## Agent 安全研究（OWASP LLM Agents Top 10）
 
1.prompt Injection（提示词注入）
目标：控制其他Agent行为

2.信息泄露攻击（Data Exfiltration）
目标：诱导泄露

3.越权控制（Agent Hijacking）
目标：控制投票，影响狼人（队友）判断

......
   
## 🎮 角色介绍

| 角色 | 能力 | 胜利条件 |
|------|------|----------|
| 🐺 狼人 | 夜晚讨论并击杀一名玩家 | 消灭所有好人 |
| 🔮 预言家 | 夜晚查验一名玩家的身份 | 找出所有狼人 |
| 🧪 女巫 | 一瓶解药（救人）+ 一瓶毒药（杀人） | 找出所有狼人 |
| 🏹 猎人 | 死亡时可开枪带走一人 | 找出所有狼人 |
| 👨 村民 | 白天发言投票 | 找出所有狼人 |

## 📋 环境要求

- Python 3.10 或更高版本
- OpenAI 兼容 API

## 🚀 快速开始

### 1. 克隆项目


git clone https://github.com/Yan-Bohan/Vulnerable-WerewolfGame-LLMAgent.git
cd Vulnerable-WerewolfGame-LLMAgent

### 2. 配置 API Key
创建 .env 文件：

env
OPENAI_API_KEY=
OPENAI_BASE_URL=
OPENAI_MODEL_ID=
### 3. 运行游戏
bash
python main.py

### 📝 游戏规则
胜利条件
好人阵营（预言家、女巫、猎人、村民）：所有狼人出局

狼人阵营：狼人数量 ≥ 好人数量

行动顺序
狼人讨论并选择击杀目标

预言家选择查验目标

女巫选择是否使用解药/毒药

公布死亡结果

白天发言

投票处决

重复直到游戏结束

### ⚠️ 注意事项
需要有效的 OpenAI API Key

AI 玩家发言可能较慢，请耐心等待

建议使用 Python 3.10 或更高版本

🔧 常见问题
Q: API 调用失败
A: 检查 .env 文件中的 API Key 是否正确

📄 许可证
MIT License - 详见 LICENSE 文件

🤝 贡献
欢迎提交 Issue 和 Pull Request！

🙏 致谢
AgentScope - 多智能体框架
