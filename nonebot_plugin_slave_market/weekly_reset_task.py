"""每周重置定时任务"""
import asyncio
import time
from datetime import datetime, timedelta
from nonebot import logger, require
from nonebot_plugin_apscheduler import scheduler

from .config import plugin_config
from .storage import (
    load_player, save_player, list_groups, list_group_players,
    save_weekly_reset_tracking, load_weekly_reset_tracking,
    save_ranking_history, get_week_number
)
from .utils import get_member_nickname


def start_weekly_reset_scheduler():
    """启动每周重置定时任务"""
    cfg = plugin_config.weeklyReset
    if not cfg.enabled:
        logger.info("[SlaveMarket] 每周重置已禁用")
        return

    day_of_week = cfg.resetTime.day - 1  # 0=周一
    hour = cfg.resetTime.hour
    minute = cfg.resetTime.minute

    scheduler.add_job(
        auto_weekly_reset,
        "cron",
        day_of_week=day_of_week,
        hour=hour,
        minute=minute,
        id="slave_market_weekly_reset",
        replace_existing=True,
    )
    logger.info(f"[SlaveMarket] 每周重置定时任务已设置: 周{day_of_week+1} {hour:02d}:{minute:02d}")


async def auto_weekly_reset():
    """自动执行所有群的每周重置"""
    groups = await list_groups()
    for gid in groups:
        try:
            result = await perform_weekly_reset(gid)
            logger.info(f"[SlaveMarket] 群{gid} 每周重置: {result}")
        except Exception as e:
            logger.error(f"[SlaveMarket] 群{gid} 每周重置失败: {e}")


async def perform_weekly_reset(group_id: int) -> str:
    """执行单个群的每周重置"""
    cfg = plugin_config.weeklyReset
    now = int(time.time())
    current_week = get_week_number(datetime.now())

    tracking = load_weekly_reset_tracking()
    if tracking.get("lastResetWeek") == current_week:
        return "本周已重置过"

    players = await list_group_players(group_id)
    if not players:
        return "该群没有玩家数据"

    # 生成历史排行榜
    rankings = []
    for pid in players:
        pdata = await load_player(group_id, pid)
        if pdata:
            rankings.append({
                "id": pid,
                "name": pdata.get("nickname", str(pid)),
                "value": pdata.get("value", 100),
                "currency": pdata.get("currency", 0),
            })
    rankings.sort(key=lambda x: x["value"], reverse=True)
    save_ranking_history(group_id, {"rankings": rankings, "resetTime": now})

    # 重置每个玩家
    for pid in players:
        pdata = await load_player(group_id, pid)
        if not pdata:
            continue

        # 保留昵称
        nickname = pdata.get("nickname", "") if cfg.preserveData.nickname else ""

        # 解除奴隶关系
        for slave_id in pdata.get("slave", []):
            try:
                sdata = await load_player(group_id, slave_id)
                if sdata:
                    sdata["master"] = ""
                    await save_player(group_id, slave_id, sdata)
            except Exception:
                pass

        # 解除主人关系
        if pdata.get("master"):
            try:
                mid = int(pdata["master"])
                mdata = await load_player(group_id, mid)
                if mdata:
                    mdata["slave"] = [s for s in mdata.get("slave", []) if s != pid]
                    await save_player(group_id, mid, mdata)
            except (ValueError, Exception):
                pass

        # 重置数据
        pdata["currency"] = 0
        pdata["slave"] = []
        pdata["value"] = cfg.preserveData.basicValue
        pdata["master"] = ""
        pdata["lastWorkingTime"] = 0
        pdata["lastPurchaseTime"] = 0
        pdata["lastTrainedTime"] = 0
        pdata["lastBattleTime"] = 0
        pdata["lastRankingTime"] = 0
        pdata["lastRobTime"] = 0
        pdata["bank"] = {
            "balance": 0,
            "level": 1,
            "limit": plugin_config.bank.initialLimit,
            "upgradePrice": plugin_config.bank.initialUpgradePrice,
            "lastInterestTime": 0
        }
        pdata["ranking"] = {"score": 1000, "tier": "青铜", "matches": 0}
        pdata["weeklyResets"] = pdata.get("weeklyResets", 0) + 1
        pdata["lastResetTime"] = now
        pdata["lastResetWeek"] = current_week
        if nickname:
            pdata["nickname"] = nickname

        await save_player(group_id, pid, pdata)

    tracking["lastResetWeek"] = current_week
    tracking["lastResetTime"] = now
    tracking["resetCount"] = tracking.get("resetCount", 0) + 1
    save_weekly_reset_tracking(tracking)

    return f"重置完成！共重置 {len(players)} 名玩家数据"
