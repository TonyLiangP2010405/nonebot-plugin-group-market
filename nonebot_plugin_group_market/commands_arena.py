"""决斗指令"""
import random
import time
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment

from .config import plugin_config
from .storage import load_player, save_player
from .utils import get_member_nickname, check_permission
from .extension.config import ext_config
from .extension.utils import give_exp_and_track
from .extension.group_storage import record_season_stat
from .extension.anti_spam import check_cooldown

arena_cmd = on_command("决斗", priority=5, block=True)


@arena_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await arena_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "duel")
    if not allowed:
        if msg:
            await arena_cmd.finish(msg)
        return

    group_id = event.group_id
    user_id = event.user_id

    user_data = await load_player(group_id, user_id)
    if not user_data:
        await arena_cmd.finish("你还没有参与游戏")

    # 解析两个 @ 目标
    at_ids = []
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            at_ids.append(int(seg.data["qq"]))

    if len(at_ids) != 2:
        await arena_cmd.finish("请 @ 两个奴隶进行决斗\n例如: /决斗 @奴隶1 @奴隶2")

    slave1_id, slave2_id = at_ids

    # 检查是否都是自己的奴隶
    slaves = user_data.get("slave", [])
    if slave1_id not in slaves:
        await arena_cmd.finish("第一个目标不是你的奴隶")
    if slave2_id not in slaves:
        await arena_cmd.finish("第二个目标不是你的奴隶")

    now = int(time.time())
    cfg = plugin_config.arena

    # 检查参赛费
    if user_data["currency"] < cfg.entryFee:
        await arena_cmd.finish(f"💰 参赛费不足！\n需要: {cfg.entryFee} 金币")

    slave1_data = await load_player(group_id, slave1_id)
    slave2_data = await load_player(group_id, slave2_id)
    if not slave1_data or not slave2_data:
        await arena_cmd.finish("奴隶数据不存在")

    # 检查冷却
    if not check_permission(event):
        s1_cd = cfg.cooldown - (now - slave1_data.get("lastBattleTime", 0))
        s2_cd = cfg.cooldown - (now - slave2_data.get("lastBattleTime", 0))
        if s1_cd > 0:
            await arena_cmd.finish(f"⏳ 奴隶1 决斗冷却中...\n剩余: {s1_cd // 3600}小时")
        if s2_cd > 0:
            await arena_cmd.finish(f"⏳ 奴隶2 决斗冷却中...\n剩余: {s2_cd // 3600}小时")

    # 扣除参赛费
    user_data["currency"] -= cfg.entryFee

    # 计算胜率
    win_rate = 0.5 + (slave1_data["value"] - slave2_data["value"]) / max(slave1_data["value"] + slave2_data["value"], 1) * 0.3
    win_rate = max(0.1, min(0.9, win_rate))

    s1_name = await get_member_nickname(bot, group_id, slave1_id)
    s2_name = await get_member_nickname(bot, group_id, slave2_id)

    if random.random() < win_rate:
        # slave1 胜
        reward = int(cfg.entryFee * cfg.rewardRate)
        user_data["currency"] += reward
        slave1_data["value"] = int(slave1_data["value"] * (1 + cfg.valueBonus))
        slave2_data["value"] = max(100, int(slave2_data["value"] * 0.95))

        slave1_data["lastBattleTime"] = now
        slave2_data["lastBattleTime"] = now
        # 扩展追踪
        duel_stats = user_data.setdefault("duelStats", {"wins": 0, "losses": 0, "total": 0})
        duel_stats["wins"] += 1
        duel_stats["total"] += 1
        if ext_config.level.enabled:
            from .extension.utils import add_exp
            add_exp(user_data, ext_config.level.arenaExp)
        give_exp_and_track(user_data, 0, "arena")
        await record_season_stat(group_id, user_id, "duelWins")
        await save_player(group_id, slave1_id, slave1_data)
        await save_player(group_id, slave2_id, slave2_data)
        await save_player(group_id, user_id, user_data)

        await arena_cmd.finish(
            f"⚔️ 决斗结果 ⚔️\n"
            f"{s1_name} VS {s2_name}\n"
            f"🏆 胜利者: {s1_name}\n"
            f"💰 获得奖励: {reward} 金币\n"
            f"📈 {s1_name} 身价 +{int(slave1_data['value'] * cfg.valueBonus)}\n"
            f"📉 {s2_name} 身价 -5%"
        )
    else:
        # slave2 胜
        reward = int(cfg.entryFee * cfg.rewardRate)
        user_data["currency"] += reward
        slave2_data["value"] = int(slave2_data["value"] * (1 + cfg.valueBonus))
        slave1_data["value"] = max(100, int(slave1_data["value"] * 0.95))

        slave1_data["lastBattleTime"] = now
        slave2_data["lastBattleTime"] = now
        # 扩展追踪（失败也给少量经验）
        duel_stats = user_data.setdefault("duelStats", {"wins": 0, "losses": 0, "total": 0})
        duel_stats["losses"] += 1
        duel_stats["total"] += 1
        if ext_config.level.enabled:
            from .extension.utils import add_exp
            add_exp(user_data, ext_config.level.arenaExp // 2)
        give_exp_and_track(user_data, 0, "arena")
        await save_player(group_id, slave1_id, slave1_data)
        await save_player(group_id, slave2_id, slave2_data)
        await save_player(group_id, user_id, user_data)

        await arena_cmd.finish(
            f"⚔️ 决斗结果 ⚔️\n"
            f"{s1_name} VS {s2_name}\n"
            f"🏆 胜利者: {s2_name}\n"
            f"💰 获得奖励: {reward} 金币\n"
            f"📈 {s2_name} 身价 +{int(slave2_data['value'] * cfg.valueBonus)}\n"
            f"📉 {s1_name} 身价 -5%"
        )
