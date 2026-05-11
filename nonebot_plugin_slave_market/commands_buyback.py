"""回购自己指令"""
import time
import datetime
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .config import plugin_config
from .storage import ensure_player, load_player, save_player
from .utils import get_member_nickname, check_permission, format_currency

buyback_cmd = on_command("回购自己", priority=5, block=True)

@buyback_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await buyback_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    user_id = event.user_id

    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)

    master = user_data.get("master", "")
    if not master:
        await buyback_cmd.finish("你是自由身，不需要回购！")

    buyback_price = int(user_data["value"] * 2)
    if user_data["currency"] < buyback_price:
        await buyback_cmd.finish(f"💰 金币不足！\n回购价格: {buyback_price} 金币")

    now = int(time.time())
    cfg = plugin_config.buyBack

    # 每周重置次数
    last_buyback = user_data.get("lastBuyBackTime", 0)
    last_date = datetime.datetime.fromtimestamp(last_buyback)
    current_date = datetime.datetime.now()
    last_week = last_date.isocalendar()[1]
    current_week = current_date.isocalendar()[1]

    if current_week != last_week and now - last_buyback > 604800:
        user_data["buyBackTimes"] = 0

    if user_data.get("buyBackTimes", 0) >= cfg.maxTimes:
        await buyback_cmd.finish(f"❌ 本周回购次数已达上限 ({cfg.maxTimes}次)")

    if not check_permission(event):
        remaining = cfg.cooldown - (now - last_buyback)
        if remaining > 0:
            h = remaining // 3600
            m = (remaining % 3600) // 60
            await buyback_cmd.finish(f"⏳ 回购冷却中...\n剩余: {h}小时{m}分钟")

    # 扣金币
    user_data["currency"] -= buyback_price
    # 扣税
    tax = int(user_data["currency"] * cfg.taxRate)
    user_data["currency"] -= tax

    # 身价提升
    user_data["value"] = int(user_data["value"] * 1.2)
    user_data["master"] = ""
    user_data["lastBuyBackTime"] = now
    user_data["buyBackTimes"] = user_data.get("buyBackTimes", 0) + 1

    # 前主人失去奴隶
    try:
        master_id = int(master)
        master_data = await load_player(group_id, master_id)
        if master_data:
            master_data["slave"] = [s for s in master_data.get("slave", []) if s != user_id]
            await save_player(group_id, master_id, master_data)
    except ValueError:
        pass

    await save_player(group_id, user_id, user_data)

    await buyback_cmd.finish(
        f"✅ 回购成功！\n"
        f"花费: {buyback_price} 金币\n"
        f"税率: {tax} 金币\n"
        f"新身价: {user_data['value']} 金币\n"
        f"剩余金币: {user_data['currency']} 金币"
    )
