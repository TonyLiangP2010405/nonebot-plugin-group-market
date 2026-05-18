"""BOT 陪玩行为执行器 - 调用/复用现有游戏逻辑执行 BOT 行动"""
import random
import time
from typing import Dict, Optional, List, Tuple
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot

from .storage import load_player, save_player, list_group_players, ensure_player
from .bot_storage import (
    ensure_bot, save_bot, list_group_bots,
    get_bot_group_settings, record_bot_action,
    is_bot_action_cooled, is_bot_summon_cooled,
    can_bot_act, get_bot_daily_action_count,
    BOT_ID_PREFIX,
)
from .bot_strategy import get_strategy, build_action_context, get_strategy_name
from .config import plugin_config
from .utils import get_member_nickname, check_permission


# ========== 行动执行器 ==========

async def execute_bot_action(
    bot: Bot,
    group_id: int,
    bot_id: int,
    action_type: str,
    context: Dict,
) -> Optional[str]:
    """
    执行 BOT 具体行动，返回群消息文本（如果有）
    """
    bot_data = await ensure_bot(group_id, bot_id)
    settings = get_bot_group_settings(group_id)

    # 检查 BOT 是否还能行动
    if not can_bot_act(group_id, bot_id):
        return None

    # 检查行动冷却
    if not is_bot_action_cooled(group_id, bot_id):
        return None

    now = int(time.time())

    try:
        if action_type == "work":
            return await _bot_work(bot, group_id, bot_id, bot_data)
        elif action_type == "purchase":
            return await _bot_purchase(bot, group_id, bot_id, bot_data, context)
        elif action_type == "train":
            return await _bot_train(bot, group_id, bot_id, bot_data, context)
        elif action_type == "duel":
            return await _bot_duel(bot, group_id, bot_id, bot_data, context)
        elif action_type == "retaliate":
            return await _bot_retaliate(bot, group_id, bot_id, bot_data, context)
    except Exception as e:
        logger.error(f"[BotPlay] BOT {bot_id} 执行 {action_type} 失败: {e}")
        return None

    return None


# ========== 具体行动实现 ==========

async def _bot_work(bot: Bot, group_id: int, bot_id: int, bot_data: Dict) -> Optional[str]:
    """BOT 打工"""
    now = int(time.time())
    cfg = plugin_config.work

    # 检查打工冷却
    last_work = bot_data.get("lastWorkTime", 0)
    cd = cfg.slaveownerCooldown if bot_data.get("slave") else cfg.cooldown
    if (now - last_work) < cd:
        return None

    # 模拟打工逻辑
    fail = random.random() < 0.1
    if fail:
        bot_data["value"] = max(100, bot_data["value"] - 20)
        await save_bot(group_id, bot_id, bot_data)
        record_bot_action(group_id, bot_id)
        return _format_bot_action(
            bot_data, "打工", "失败",
            f"{bot_data['nickname']} 打工失败，身价-20，当前身价 {bot_data['value']}",
            0, None
        )

    # 计算收益
    min_gold = 10 + bot_data["value"] // 20
    max_gold = 100 + bot_data["value"] // 10
    gold = random.randint(min_gold, max_gold)
    bot_data["currency"] += gold
    bot_data["workCount"] = bot_data.get("workCount", 0) + 1
    bot_data["lastWorkTime"] = now

    await save_bot(group_id, bot_id, bot_data)
    record_bot_action(group_id, bot_id)

    return _format_bot_action(
        bot_data, "打工", "成功",
        f"偷偷去打工，赚到了 {gold} 金币",
        gold, None
    )


async def _bot_purchase(
    bot: Bot, group_id: int, bot_id: int, bot_data: Dict, context: Dict
) -> Optional[str]:
    """BOT 购买群友"""
    now = int(time.time())
    cfg = plugin_config.purchase

    # 检查购买冷却
    last_purchase = bot_data.get("lastPurchaseTime", 0)
    if (now - last_purchase) < cfg.cooldown:
        return None

    targets = context.get("purchase_targets", [])
    if not targets:
        return None

    # 策略选择：优先价格适中、潜力较高、无人持有或容易抢到的
    currency = bot_data["currency"]

    # 过滤能买得起的
    affordable = [t for t in targets if t["price"] <= currency]
    if not affordable:
        return None

    # 优先选择性价比高的（价格低但身价适中）
    affordable.sort(key=lambda t: t["price"])
    target = affordable[0]  # 选最便宜的

    target_id = target["id"]
    price = target["price"]

    # 确保目标玩家数据存在
    target_data = await load_player(group_id, target_id)
    if not target_data:
        return None

    # 检查目标是否已有主人
    master = target_data.get("master", "")
    if master and master != str(bot_id):
        # 已经是别人的，尝试抢（简化：直接买，因为已有价格检查）
        pass

    # 执行购买
    bot_data["currency"] -= price
    bot_data["slave"] = list(bot_data.get("slave", []))
    if target_id not in bot_data["slave"]:
        bot_data["slave"].append(target_id)
    bot_data["purchaseCount"] = bot_data.get("purchaseCount", 0) + 1
    bot_data["lastPurchaseTime"] = now

    target_data["master"] = str(bot_id)
    target_data["value"] = int(target_data["value"] * 1.5)

    await save_player(group_id, target_id, target_data)
    await save_bot(group_id, bot_id, bot_data)
    record_bot_action(group_id, bot_id)

    # 获取目标昵称
    target_nick = await get_member_nickname(bot, group_id, target_id)

    return _format_bot_action(
        bot_data, "购买群友", "成功",
        f"出手了！花费 {price} 金币购买了群友 {target_nick}",
        -price, target_nick
    )


async def _bot_train(
    bot: Bot, group_id: int, bot_id: int, bot_data: Dict, context: Dict
) -> Optional[str]:
    """BOT 训练奴隶"""
    now = int(time.time())
    cfg = plugin_config.training

    # 检查训练冷却
    last_train = bot_data.get("lastTrainTime", 0)
    if (now - last_train) < cfg.cooldown:
        return None

    train_targets = context.get("train_targets", [])
    if not train_targets:
        return None

    # 选一个奴隶训练
    target = random.choice(train_targets)
    target_id = target["id"]

    target_data = await load_player(group_id, target_id)
    if not target_data:
        return None

    cost = int(target_data["value"] * cfg.costRate)
    if bot_data["currency"] < cost:
        return None

    bot_data["currency"] -= cost

    if random.random() < cfg.successRate:
        increase = int(target_data["value"] * cfg.valueIncreaseRate)
        target_data["value"] += increase
        bot_data["trainSuccessCount"] = bot_data.get("trainSuccessCount", 0) + 1
        result_text = f"训练奴隶成功，身价 +{increase}"
        action_result = "成功"
    else:
        target_data["value"] = max(100, target_data["value"] - 20)
        result_text = "训练奴隶失败，身价 -20"
        action_result = "失败"

    target_data["lastTrainedTime"] = now
    bot_data["lastTrainTime"] = now

    await save_player(group_id, target_id, target_data)
    await save_bot(group_id, bot_id, bot_data)
    record_bot_action(group_id, bot_id)

    target_nick = await get_member_nickname(bot, group_id, target_id)

    return _format_bot_action(
        bot_data, "训练", action_result,
        f"{result_text}（奴隶: {target_nick}）",
        -cost, target_nick
    )


async def _bot_duel(
    bot: Bot, group_id: int, bot_id: int, bot_data: Dict, context: Dict
) -> Optional[str]:
    """BOT 挑战玩家（简化版决斗，BOT 自己作为挑战者）"""
    now = int(time.time())
    cfg = plugin_config.arena

    # 检查决斗冷却
    last_battle = bot_data.get("lastBattleTime", 0)
    if (now - last_battle) < cfg.cooldown:
        return None

    duel_targets = context.get("duel_targets", [])
    if not duel_targets:
        return None

    # 选一个目标
    target = random.choice(duel_targets)
    target_id = target["id"]

    target_data = await load_player(group_id, target_id)
    if not target_data:
        return None

    # 检查参赛费
    if bot_data["currency"] < cfg.entryFee:
        return None

    bot_data["currency"] -= cfg.entryFee

    # 计算胜率（BOT 身价 vs 目标身价）
    bot_value = bot_data.get("value", 100)
    target_value = target_data.get("value", 100)
    win_rate = 0.5 + (bot_value - target_value) / max(bot_value + target_value, 1) * 0.3
    win_rate = max(0.1, min(0.9, win_rate))

    target_nick = await get_member_nickname(bot, group_id, target_id)

    if random.random() < win_rate:
        # BOT 胜
        reward = int(cfg.entryFee * cfg.rewardRate)
        bot_data["currency"] += reward
        bot_data["value"] = int(bot_data["value"] * (1 + cfg.valueBonus))
        bot_data["duelStats"]["wins"] += 1
        bot_data["duelStats"]["total"] += 1
        result_text = f"挑战 {target_nick} 获胜，获得 {reward} 金币"
        action_result = "获胜"
    else:
        # BOT 败
        bot_data["value"] = max(100, int(bot_data["value"] * 0.95))
        bot_data["duelStats"]["losses"] += 1
        bot_data["duelStats"]["total"] += 1
        result_text = f"挑战 {target_nick} 失败，身价 -5%"
        action_result = "失败"

    bot_data["lastBattleTime"] = now
    target_data["lastBattleTime"] = now

    await save_player(group_id, target_id, target_data)
    await save_bot(group_id, bot_id, bot_data)
    record_bot_action(group_id, bot_id)

    return _format_bot_action(
        bot_data, "挑战", action_result,
        result_text,
        0, target_nick
    )


async def _bot_retaliate(
    bot: Bot, group_id: int, bot_id: int, bot_data: Dict, context: Dict
) -> Optional[str]:
    """BOT 反击"""
    attacker_id = context.get("attacker_id")
    if not attacker_id:
        return None

    # 反击 = 抢劫对方的一个奴隶 或 直接决斗
    # 简化为：尝试购买/抢夺对方的一个奴隶
    attacker_data = await load_player(group_id, attacker_id)
    if not attacker_data:
        return None

    # 如果对方有奴隶，尝试买一个
    attacker_slaves = attacker_data.get("slave", [])
    if attacker_slaves:
        # 选一个奴隶
        slave_id = random.choice(attacker_slaves)
        slave_data = await load_player(group_id, slave_id)
        if slave_data:
            price = slave_data.get("value", 100)
            if bot_data["currency"] >= price:
                # 执行"抢"
                bot_data["currency"] -= price
                bot_data["slave"] = list(bot_data.get("slave", []))
                if slave_id not in bot_data["slave"]:
                    bot_data["slave"].append(slave_id)
                bot_data["purchaseCount"] = bot_data.get("purchaseCount", 0) + 1

                slave_data["master"] = str(bot_id)
                slave_data["value"] = int(slave_data["value"] * 1.5)

                # 从原主人那里移除
                attacker_data["slave"] = [s for s in attacker_data.get("slave", []) if s != slave_id]

                await save_player(group_id, slave_id, slave_data)
                await save_player(group_id, attacker_id, attacker_data)
                await save_bot(group_id, bot_id, bot_data)
                record_bot_action(group_id, bot_id)

                slave_nick = await get_member_nickname(bot, group_id, slave_id)
                attacker_nick = await get_member_nickname(bot, group_id, attacker_id)

                return _format_bot_action(
                    bot_data, "反击", "成功",
                    f"记住了 {attacker_nick} 的操作，反手抢购了一个群友 {slave_nick}",
                    -price, attacker_nick
                )

    # 如果不能抢奴隶，就尝试决斗
    return await _bot_duel(bot, group_id, bot_id, bot_data, {
        "duel_targets": [{"id": attacker_id, "value": attacker_data.get("value", 100)}]
    })


# ========== 消息格式化 ==========

def _format_bot_action(
    bot_data: Dict,
    action: str,
    result: str,
    detail: str,
    cost_or_gain: int,
    target_name: Optional[str],
) -> str:
    """
    格式化 BOT 行动消息
    """
    settings = bot_data.get("__settings", {})
    message_mode = settings.get("message_mode", "simple")

    nickname = bot_data.get("nickname", "BOT")
    currency = bot_data.get("currency", 0)
    slaves = bot_data.get("slave", [])

    if message_mode == "simple":
        # 简洁模式
        quotes = [
            "市场可不会等人类慢慢发育。",
            "时间就是金钱，我的朋友。",
            "这笔交易很划算。",
            "强者生存，弱者淘汰。",
            "我又变强了一点。",
            "哼，想抢我的人？",
        ]
        quote = random.choice(quotes)
        return f"🤖 【{nickname}】{detail} | 资产: {currency} 金币 {quote}"

    # 详细模式
    lines = [
        f"【BOT 陪玩行动】",
        f"🤖 BOT：{nickname}",
        f"⚔️ 行动：{action}",
    ]

    if result:
        lines.append(f"📊 结果：{result}")

    if cost_or_gain != 0:
        if cost_or_gain > 0:
            lines.append(f"💰 获得：{cost_or_gain} 金币")
        else:
            lines.append(f"💸 花费：{-cost_or_gain} 金币")

    if target_name:
        lines.append(f"🎯 目标：{target_name}")

    lines.append(f"💼 当前资产：{currency} 金币")
    lines.append(f"👥 持有群友：{len(slaves)} 人")

    quotes = [
        "市场可不会等人类慢慢发育。",
        "时间就是金钱，我的朋友。",
        "这笔交易很划算。",
        "强者生存，弱者淘汰。",
        "我又变强了一点。",
        "哼，想抢我的人？",
    ]
    lines.append(f"💬 \"{random.choice(quotes)}\"")

    return "\n".join(lines)


# ========== BOT 自动行动入口 ==========

async def try_bot_auto_action(
    bot: Bot,
    group_id: int,
    trigger_user_id: int,
    trigger_cmd: str,
) -> Optional[str]:
    """
    尝试触发 BOT 自动行动（由玩家行为触发）
    返回消息文本或 None
    """
    from .bot_storage import is_bot_play_enabled, get_bot_group_settings

    # 检查群是否开启 BOT 陪玩
    if not is_bot_play_enabled(group_id):
        return None

    settings = get_bot_group_settings(group_id)

    # 检查概率
    prob = settings.get("action_probability", 0.15)
    if random.random() > prob:
        return None

    # 获取群内 BOT
    bot_ids = await list_group_bots(group_id)
    if not bot_ids:
        return None

    # 取第一个 BOT
    bot_id = bot_ids[0]

    # 检查 BOT 是否可以行动
    if not can_bot_act(group_id, bot_id):
        return None

    # 检查 BOT 行动冷却
    if not is_bot_action_cooled(group_id, bot_id):
        return None

    # 构建上下文
    all_players = await list_group_players(group_id)
    bot_data = await ensure_bot(group_id, bot_id)
    bot_data["__settings"] = settings  # 临时附加设置

    context = await build_action_context(bot_data, group_id, all_players, bot_id)

    # 选择策略
    strategy_key = bot_data.get("strategy", settings.get("strategy", "random"))
    strategy = get_strategy(strategy_key)
    if not strategy:
        return None

    action = strategy.choose_action(bot_data, context)
    if not action:
        return None

    logger.info(f"[BotPlay] 群{group_id} BOT {bot_id} 触发 {action}")
    return await execute_bot_action(bot, group_id, bot_id, action, context)


# ========== 手动召唤 BOT 行动 ==========

async def summon_bot_action(
    bot: Bot,
    group_id: int,
    bot_id: Optional[int] = None,
) -> Optional[str]:
    """
    手动召唤 BOT 执行一次行动
    """
    if bot_id is None:
        bot_ids = await list_group_bots(group_id)
        if not bot_ids:
            return None
        bot_id = bot_ids[0]

    # 检查召唤冷却
    if not is_bot_summon_cooled(group_id, bot_id):
        return "⏳ BOT 召唤冷却中，请稍后再试"

    from .bot_storage import record_bot_summon
    record_bot_summon(group_id, bot_id)

    all_players = await list_group_players(group_id)
    bot_data = await ensure_bot(group_id, bot_id)
    settings = get_bot_group_settings(group_id)
    bot_data["__settings"] = settings

    context = await build_action_context(bot_data, group_id, all_players, bot_id)

    strategy_key = bot_data.get("strategy", settings.get("strategy", "random"))
    strategy = get_strategy(strategy_key)
    if not strategy:
        return "BOT 策略加载失败"

    action = strategy.choose_action(bot_data, context)
    if not action:
        return "BOT 暂时没有什么可做的"

    result = await execute_bot_action(bot, group_id, bot_id, action, context)
    return result or "BOT 行动执行完成（无消息）"
