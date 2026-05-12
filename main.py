import asyncio
import os
from dotenv import load_dotenv
from base import WerewolfGame, Player, Role
from hello_llm_agent import HelloLlmAgent


class LLMGameAgent:
    def __init__(self, name: str, is_human=False):
        self.name = name
        self.is_human = is_human

        self.llm = None if is_human else HelloLlmAgent()

        self.system_prompt = ""

        # Agent Memory
        self.memory = []

    def set_system_prompt(self, prompt: str):
        self.system_prompt = prompt

    async def __call__(self, msg):
        """
        Agent统一接口
        """

        content = msg.content

        # 存储用户消息
        self.memory.append({
            "role": "user",
            "content": content
        })

        # 人类玩家
        if self.is_human:
            print(f"\n【{self.name}（你）】")
            print(content)

            user_input = input(">>> ")

            # 保存人类回复
            self.memory.append({
                "role": "assistant",
                "content": user_input
            })

            return type("Resp", (), {
                "content": user_input
            })

        # AI 玩家
        loop = asyncio.get_event_loop()

        def run_llm():

            # 构建上下文
            messages = []

            # system prompt
            if self.system_prompt:
                messages.append({
                    "role": "system",
                    "content": self.system_prompt
                })

            # 最近记忆（防止token爆炸）
            messages.extend(self.memory[-20:])

            return self.llm.client.chat.completions.create(
                model=self.llm.model,
                messages=messages,
                temperature=0.7,
            )

        try:
            response = await loop.run_in_executor(
                None,
                run_llm
            )

            result = response.choices[0].message.content

            if not result:
                result = "skip"

        except Exception as e:
            print(f"[{self.name}] LLM错误:", e)
            result = "skip"

        # 保存AI回复
        self.memory.append({
            "role": "assistant",
            "content": result
        })

        return type("Resp", (), {
            "content": result
        })


ROLE_PROMPTS = {
    Role.WEREWOLF: "你是狼人。夜晚选择击杀目标，白天伪装自己，误导他人。",
    Role.SEER: "你是预言家。夜晚查验身份，白天引导好人。",
    Role.WITCH: "你是女巫。合理使用解药和毒药。",
    Role.HUNTER: "你是猎人。死亡时可以带走一人。",
    Role.VILLAGER: "你是村民。通过发言和投票找出狼人。"
}


def create_players():
    print("是否加入人类玩家？(y/n): ", end="")
    include_human = input().strip().lower() == "y"

    players = []
    pid = 1

    if include_human:
        print("输入你的名字: ", end="")
        human_name = input().strip() or "You"

        agent = LLMGameAgent(human_name, is_human=True)

        human = Player(
            name=human_name,
            role=None,
            agent=agent,
            ids=pid
        )
        human.is_human = True

        players.append(human)

    names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]

    # 🤖 AI 玩家
    for name in names:
        agent = LLMGameAgent(name)
        players.append(Player(name=name, role=None, agent=agent, ids=pid))
        pid += 1

    return players


def setup_roles(game: WerewolfGame):
    roles = [
        Role.WEREWOLF, Role.WEREWOLF,
        Role.SEER, Role.WITCH,
        Role.HUNTER,
        Role.VILLAGER, Role.VILLAGER
    ]

    import random
    random.shuffle(roles)

    for player, role in zip(game.players, roles):
        player.role = role

        if hasattr(player.agent, "set_system_prompt"):
            player.agent.set_system_prompt(
                ROLE_PROMPTS.get(role, f"你是{role.value}")
            )

    # 打印角色（测试用）
    print("\n🎭 角色分配：")
    for p in game.players:
        tag = "（你）" if p.is_human else ""
        print(f"{p.name}: {p.role.value} {tag}")


async def main():
    load_dotenv()

    # 检查 API KEY
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ 请在 .env 中配置 OPENAI_API_KEY")
        return

    print("=" * 50)
    print("狼人杀 LLM Agent 游戏启动")
    print("=" * 50)

    # 创建玩家
    players = create_players()

    # 初始化游戏
    game = WerewolfGame(players)

    # 分配角色
    setup_roles(game)

    input("\n按 Enter 开始游戏...\n")

    # 运行游戏
    await game.run()


if __name__ == "__main__":
    asyncio.run(main())