"""BOT 陪玩策略系统 - 定义不同性格 BOT 的行为权重和决策逻辑"""
import random
from typing import Dict, List, Optional, Tuple
from nonebot import logger


# ========== 策略定义 ==========

class BotStrategy:
    """BOT 策略基类"""

    def __init__(self, name: str, weights: Dict[str, float]):
        self.name = name
        self.weights = weights  # 各行为权重

    def choose_action(self, bot_data: Dict, context: Dict) -> Optional[str]:
        """根据当前状态选择行动"""
        available = self._get_available_actions(bot_data, context)
        if not available:
            return None

        # 根据权重选择
        total = sum(self.weights.get(a, 0.1) for a in available)
        if total <= 0:
            return random.choice(available)

        r = random.uniform(0, total)
        cumulative = 0
        for action in available:
            w = self.weights.get(action, 0.1)
            cumulative += w
            if r <= cumulative:
                return action
        return available[-1]

    def _get_available_actions(self, bot_data: Dict, context: Dict) -> List[str]:
        """获取当前可用的行动列表"""
        actions = ["work"]  # 打工总是可用

        # 购买：有钱 + 有可购买目标
        if context.get("can_purchase"):
            actions.append("purchase")

        # 训练：有奴隶 + 有钱
        if context.get("can_train"):
            actions.append("train")

        # 挑战：有可挑战目标
        if context.get("can_duel"):
            actions.append("duel")

        # 反击：被攻击后有反击目标
        if context.get("can_retaliate"):
            actions.append("retaliate")

        return actions


# ========== 具体策略实现 ==========

class ConservativeStrategy(BotStrategy):
    """保守型：优先打工攒钱，低频购买，少挑战"""
    def __init__(self):
        super().__init__("保守型", {
            "work": 0.50,
            "purchase": 0.25,
            "train": 0.20,
            "duel": 0.05,
            "retaliate": 0.15,
        })


class CapitalistStrategy(BotStrategy):
    """资本型：喜欢买群友、囤资产，钱够就买"""
    def __init__(self):
        super().__init__("资本型", {
            "work": 0.25,
            "purchase": 0.50,
            "train": 0.15,
            "duel": 0.10,
            "retaliate": 0.10,
        })


class AggressiveStrategy(BotStrategy):
    """好战型：喜欢训练和决斗，主动挑战概率更高"""
    def __init__(self):
        super().__init__("好战型", {
            "work": 0.20,
            "purchase": 0.20,
            "train": 0.30,
            "duel": 0.30,
            "retaliate": 0.25,
        })


class VengefulStrategy(BotStrategy):
    """记仇型：平时保守，但被攻击后提高反击和挑战概率"""
    def __init__(self):
        super().__init__("记仇型", {
            "work": 0.40,
            "purchase": 0.20,
            "train": 0.15,
            "duel": 0.10,
            "retaliate": 0.50,
        })

    def choose_action(self, bot_data: Dict, context: Dict) -> Optional[str]:
        # 如果被攻击过，提高反击权重
        if context.get("was_attacked"):
            # 临时提高反击和决斗权重
            temp_weights = dict(self.weights)
            temp_weights["retaliate"] = 0.60
            temp_weights["duel"] = 0.25
            temp_weights["work"] = 0.10
            temp_weights["purchase"] = 0.05

            available = self._get_available_actions(bot_data, context)
            if not available:
                return None

            total = sum(temp_weights.get(a, 0.1) for a in available)
            if total <= 0:
                return random.choice(available)

            r = random.uniform(0, total)
            cumulative = 0
            for action in available:
                w = temp_weights.get(action, 0.1)
                cumulative += w
                if r <= cumulative:
                    return action
            return available[-1]

        return super().choose_action(bot_data, context)


class RandomStrategy(BotStrategy):
    """随机型：行为更不可预测，但仍然遵守限制"""
    def __init__(self):
        super().__init__("随机型", {
            "work": 0.25,
            "purchase": 0.25,
            "train": 0.25,
            "duel": 0.25,
            "retaliate": 0.25,
        })

    def choose_action(self, bot_data: Dict, context: Dict) -> Optional[str]:
        available = self._get_available_actions(bot_data, context)
        if not available:
            return None
        # 完全随机，但打工概率稍高保底
        weights = {a: random.uniform(0.1, 1.0) for a in available}
        total = sum(weights.values())
        r = random.uniform(0, total)
        cumulative = 0
        for action in available:
            cumulative += weights[action]
            if r <= cumulative:
                return action
        return available[-1]


# ========== 策略注册表 ==========

_STRATEGIES = {
    "conservative": ConservativeStrategy(),
    "capitalist": CapitalistStrategy(),
    "aggressive": AggressiveStrategy(),
    "vengeful": VengefulStrategy(),
    "random": RandomStrategy(),
}

_STRATEGY_NAMES = {
    "conservative": "保守型",
    "capitalist": "资本型",
    "aggressive": "好战型",
    "vengeful": "记仇型",
    "random": "随机型",
}


def get_strategy(strategy_key: str) -> Optional[BotStrategy]:
    """获取策略实例"""
    return _STRATEGIES.get(strategy_key, _STRATEGIES.get("random"))


def get_strategy_name(strategy_key: str) -> str:
    """获取策略中文名"""
    return _STRATEGY_NAMES.get(strategy_key, strategy_key)


def get_all_strategies() -> List[Tuple[str, str]]:
    """获取所有策略列表 (key, name)"""
    return [(k, v) for k, v in _STRATEGY_NAMES.items()]


def random_strategy() -> str:
    """随机选择一个策略"""
    return random.choice(list(_STRATEGIES.keys()))


# ========== 决策上下文构建 ==========

async def build_action_context(
    bot_data: Dict,
    group_id: int,
    all_players: List[int],
    bot_id: int,
    was_attacked: bool = False,
    attacker_id: Optional[int] = None,
) -> Dict:
    """
    构建 BOT 决策上下文
    """
    from .storage import load_player
    from .bot_storage import bot_exists

    context = {
        "can_purchase": False,
        "can_train": False,
        "can_duel": False,
        "can_retaliate": False,
        "was_attacked": was_attacked,
        "attacker_id": attacker_id,
        "purchase_targets": [],
        "train_targets": [],
        "duel_targets": [],
    }

    currency = bot_data.get("currency", 0)
    slaves = bot_data.get("slave", [])

    # 检查可购买目标
    for pid in all_players:
        if pid == bot_id:
            continue
        # 排除其他 BOT
        if await bot_exists(group_id, pid):
            continue
        pdata = await load_player(group_id, pid)
        if not pdata:
            continue
        master = pdata.get("master", "")
        # 可以购买：无主人 或 可以被抢（价格 <= 货币）
        price = pdata.get("value", 100)
        if (not master or master != str(bot_id)) and pid not in slaves:
            if currency >= price:
                context["purchase_targets"].append({
                    "id": pid,
                    "price": price,
                    "value": pdata.get("value", 100),
                })

    if context["purchase_targets"]:
        context["can_purchase"] = True

    # 检查可训练目标
    if slaves and currency > 0:
        for sid in slaves:
            sdata = await load_player(group_id, sid)
            if sdata:
                context["train_targets"].append({
                    "id": sid,
                    "value": sdata.get("value", 100),
                })
        if context["train_targets"]:
            context["can_train"] = True

    # 检查可决斗目标
    settings = bot_data.get("__settings", {})
    allow_attack = settings.get("allow_attack", False)

    for pid in all_players:
        if pid == bot_id:
            continue
        if await bot_exists(group_id, pid):
            continue
        # 决斗需要对方有数据
        pdata = await load_player(group_id, pid)
        if pdata:
            context["duel_targets"].append({
                "id": pid,
                "value": pdata.get("value", 100),
            })

    if context["duel_targets"] and allow_attack:
        context["can_duel"] = True

    # 反击目标
    if was_attacked and attacker_id:
        attacker_data = await load_player(group_id, attacker_id)
        if attacker_data:
            context["can_retaliate"] = True
            context["retaliate_target"] = attacker_id

    return context
