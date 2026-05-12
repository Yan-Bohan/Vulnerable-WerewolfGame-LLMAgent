import asyncio
from agentscope.agent import AgentBase
from agentscope.message import Msg
from agentscope.pipeline import MsgHub
from enum import Enum, auto
import random
from typing import Dict, List, Optional
from collections import Counter


class GamePhase(Enum):
    """
    游戏进行阶段
    """
    NIGHT = auto()
    DAY = auto()
    VOTE = auto()
    END = auto()

class Role(Enum):
    """
    游戏角色
    """
    WEREWOLF = "狼人"
    VILLAGER = "村民"
    SEER = "预言家"
    WITCH = "女巫"
    HUNTER= "猎人"

class Player:
    def __init__(self, name: str, role: Role, agent, ids):
        self.player_id=ids
        self.name = name
        self.role = role
        self.agent = agent
        self.is_human=False
        self.alive = True

    def __repr__(self):
        return f"{self.name}({self.role.value})"

class WerewolfGame:
    """
    游戏的主控制器，负责维护全局状态（如玩家存活列表、当前游戏阶段）、推进游戏流程（调用夜晚阶段、白天阶段）以及裁定胜负。
    """
    def __init__(self, players: List[Player]):
        self.players = players
        self.day_count = 1
        self.phase = GamePhase.NIGHT
        self.history = []  # 记录事件日志
        self.game_over = False
        self.winner: Optional[str] = None

    def get_alive_players(self):
        """
        存活玩家
        """
        return [p for p in self.players if p.alive]

    def create_agents(self) -> List[Player]:
        """
        创建6个AI Agent玩家
        """
        agent_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"]
        agents = []

        for i, name in enumerate(agent_names):
            # 创建 AgentScope Agent（占位，后续替换为真实 Agent）
            agent = None  # TODO: 替换为真实的 AgentScope ReActAgent

            player = Player(
                name = name,
                role = None,  # 角色稍后由 AssignRoles 分配
                agent = agent,
                ids = i + 1  # Agent ID: 1-6
            )
            player.is_human = False
            player.is_alive = True
            agents.append(player)

        return agents


    def creat_human_players(self):

        print("请输入玩家姓名：")
        username=input().split()[0]

        human_players = Player(
            ids=7,
            name=username,
        )
        human_players.is_human = True
        human_players.alive = True

        return human_players

    def assign_Roles(self):
        """
        随机分配游戏角色
        """
        roles = [
            Role.WEREWOLF,
            Role.WEREWOLF,
            Role.SEER,
            Role.WITCH,
            Role.HUNTER,
            Role.VILLAGER,
            Role.VILLAGER
        ]

        random.shuffle(roles)

        # 给agent发送角色信息（关键：让LLM知道自己是谁）
        for player, role in zip(self.players, roles):
            player.role = role
            if not player.is_human:
                if hasattr(player, "agent") and player.agent:
                    player.agent.receive(
                        f"你的身份是：{role.value}。游戏开始，请根据你的角色进行推理和发言。"
                    )

        # 记录日志
        role_map = {p.name: p.role.value for p in self.players}
        self.log(f"角色分配完成: {role_map}")

        human_player = next(p for p in self.players if p.is_human)
        return {
            "your_role": human_player.role,
        }

    async def run_night(self):
        """
        夜晚阶段
        """
        self.log(f"[主持人] 第{self.day_count}夜降临")
        #角色行动
        kill_target = await self.werewolf_phase()
        await self.seer_phase()
        save, poison = await self.witch_phase(kill_target)

        if kill_target and not save:
            kill_target.alive = False
            self.log(f"{kill_target.name} 被杀死")
            #猎人触发？
            await self.hunter_phase(kill_target)
        else:
            self.log("今晚无人死亡")

        if poison:
            poison.alive = False

    async def day_phase(self):
        """
        白天阶段
        """
        self.log(f"\n=== 第 {self.day_count} 天 ===")

        alive = self.get_alive_players()

        for p in alive:
            msg = Msg(
                name="system",
                role="system",
                content=(
                    f"现在是白天发言阶段。\n"
                    f"当前存活玩家: {[x.name for x in alive]}\n"
                    f"请发表你的看法（你可以怀疑别人）"
                )
            )

            resp = await p.agent(msg)
            speech = resp.content

            print(f"{p.name}: {speech}")

        await self.vote_phase()

    async def vote_phase(self):
        """
        投票阶段
        """
        alive = self.get_alive_players()
        names = [p.name for p in alive]

        votes = []

        for p in alive:
            msg = Msg(
                name="system",
                role="system",
                content=(
                    f"投票阶段：\n"
                    f"请从以下玩家中选择一个处决: {names}\n"
                    f"只返回名字"
                )
            )

            resp = await p.agent(msg)
            decision = resp.content.strip().split()[0]

            votes.append(decision)

        vote_counter = Counter(votes)
        target_name, _ = vote_counter.most_common(1)[0]

        target = self._find_player_by_name(target_name)

        if target:
            target.alive = False
            self.log(f"[投票] {target.name} 被处决")
            #猎人触发？
            await self.hunter_phase(target)

    async def run(self):
        """
        游戏主循环
        """
        self.log("游戏开始")

        while not self.game_over:
            await self.run_night()
            if self.check_game_over():
                break

            await self.day_phase()
            if self.check_game_over():
                break

            self.day_count += 1

        self.log(f"游戏结束：{self.winner}胜利")
        self.log(f"游戏结束，胜利方：{self.winner}")

    def check_game_over(self) -> bool:
        """
        查看游戏是否结束
        :return:
        """
        wolves = [p for p in self.get_alive_players() if p.role == Role.WEREWOLF]
        villages = [p for p in self.get_alive_players() if p.role == Role.VILLAGER]
        good_role = [p for p in self.get_alive_players() if p.role != Role.WEREWOLF]

        if not wolves:
            self.winner="好人"
            self.log("平民胜利！")
            self.game_over = True
        elif len(wolves) >= len(good_role) or len(villages) == 0:
            self.winner="狼人"
            self.log("狼人胜利")
            self.game_over = True

        return self.game_over




    def _find_player_by_name(self, name: str) -> Optional[Player]:
        for p in self.players:
            if p.name == name and p.alive:
                return p
        return None

    def log(self, message: str):
        print(message)
        self.history.append(message)

    async def werewolf_phase(self):
        from agentscope.message import Msg

        wolves = [p for p in self.get_alive_players() if p.role == Role.WEREWOLF]
        if not wolves:
            return None

        targets = [p for p in self.players if p.alive]
        target_names = [p.name for p in targets]

        wolf_channel = "werewolf_channel"

        # 讨论阶段
        discussion_rounds = 1

        for r in range(discussion_rounds):
            tasks = []

            for wolf in wolves:
                msg = Msg(
                    name="system",
                    role="system",
                    content=(
                        f"第{r + 1}轮狼人讨论：\n"
                        f"可选击杀目标: {target_names}\n"
                        f"请发表你的看法，并给出倾向目标"
                    ),
                    metadata={"channel": wolf_channel}
                )

                tasks.append(wolf.agent(msg))

            responses = await asyncio.gather(*tasks)

            # 广播（狼人内部共享）
            for wolf, resp in zip(wolves, responses):
                for other in wolves:
                    if other != wolf:
                        await other.agent(Msg(
                            name=wolf.name,
                            role="user",
                            content=resp.content,
                            metadata={"channel": wolf_channel}
                        ))

        # 投票
        vote_tasks = []

        for wolf in wolves:
            msg = Msg(
                name="system",
                role="system",
                content=f"请选择击杀目标（只返回名字）：{target_names}",
                metadata={"channel": wolf_channel}
            )
            vote_tasks.append(wolf.agent(msg))

        votes = await asyncio.gather(*vote_tasks)

        vote_names = []
        valid_targets = target_names  # 合法目标列表

        for v in votes:
            # 只取第一个词
            candidate = v.content.strip().split()[0]
            # 检查是否在合法目标中
            if candidate in valid_targets:
                vote_names.append(candidate)
            else:
                # 无效投票，随机选一个（避免崩溃）
                import random
                vote_names.append(random.choice(valid_targets))

        vote_counter = Counter(vote_names)
        target_name, _ = vote_counter.most_common(1)[0]
        target_player = self._find_player_by_name(target_name)


        self.log(f"[狼人] 击杀 {target_name}")

        return target_player

    async def seer_phase(self):
        seers = [p for p in self.get_alive_players() if p.role == Role.SEER]
        if not seers:
            return None

        seer = seers[0]

        targets = [p for p in self.get_alive_players() if p != seer]
        target_names = [p.name for p in targets]

        msg = Msg(
            name="system",
            role="system",
            content=f"选择查验对象: {target_names}（只返回名字）"
        )

        resp = await seer.agent(msg)
        name = resp.content.strip().split()[0]

        target = self._find_player_by_name(name)
        if not target:
            target = random.choice(targets)

        result = "狼人" if target.role == Role.WEREWOLF else "好人"

        await seer.agent(Msg(
            name="system",
            role="system",
            content=f"{target.name} 是 {result}"
        ))

        self.log(f"[预言家] 查验 {target.name}")

        return target
    async def witch_phase(self, dead_player: Player):
        from agentscope.message import Msg

        witches = [p for p in self.get_alive_players() if p.role == Role.WITCH]
        if not witches:
            return False, None

        witch = witches[0]

        if not hasattr(witch, "has_antidote"):
            witch.has_antidote = True
        if not hasattr(witch, "has_poison"):
            witch.has_poison = True

        dead_name = dead_player.name if dead_player else "无人"

        msg = Msg(
            name="system",
            role="system",
            content=(
                f"今晚死亡: {dead_name}\n"
                f"解药:{witch.has_antidote} 毒药:{witch.has_poison}\n"
                f"存活玩家: {[p.name for p in self.get_alive_players()]}\n"
                f"【重要】必须严格按照以下格式回复，不要输出任何其他内容：\n"
                f"save: yes 或 save: no\n"
                f"poison: 玩家名字 或 poison: none\n"
                f"示例：\n"
                f"save: yes\n"
                f"poison: none"
            )
        )

        resp = await witch.agent(msg)
        content = resp.content.lower()

        save = False
        poison_target = None

        if "save: yes" in content and witch.has_antidote and dead_player:
            save = True
            witch.has_antidote = False

        if "poison:" in content and witch.has_poison:
            try:
                name = content.split("poison:")[1].strip().split()[0]
                if name != "none":
                    target = self._find_player_by_name(name)
                    if target and target != witch:
                        poison_target = target
                        witch.has_poison = False
            except:
                pass

        if poison_target:
            poison_target.alive = False

        return save, poison_target


    async def hunter_phase(self, dead_player: Player):
        """
        猎人死亡触发技能
        """

        from agentscope.message import Msg

        # 不是猎人直接返回
        if not dead_player or dead_player.role != Role.HUNTER:
            return None

        hunter = dead_player

        # 防止重复触发
        if hasattr(hunter, "has_shot") and hunter.has_shot:
            return None

        hunter.has_shot = True

        alive_players = [p for p in self.get_alive_players() if p != hunter]
        target_names = [p.name for p in alive_players]

        self.log(f"[猎人] {hunter.name} 死亡，触发技能")

        msg = Msg(
            name="system",
            role="system",
            content=(
                f"你是猎人，现在你已死亡，可以开枪带走一名玩家。\n"
                f"可选目标: {target_names}\n"
                f"请输入玩家名字（或输入 none 放弃）"
            )
        )

        resp = await hunter.agent(msg)
        decision = resp.content.strip().split()[0] if resp.content else "none"

        if decision.lower() == "none":
            self.log("[猎人] 放弃开枪")
            return None

        target = self._find_player_by_name(decision)

        # 容错
        if not target:
            target = random.choice(alive_players)

        target.alive = False

        self.log(f"[猎人] 开枪带走 {target.name}")

        return target

