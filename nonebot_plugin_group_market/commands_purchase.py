"""购买奴隶指令"""
import time
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg

from .config import plugin_config
from .storage import ensure_player, load_player, save_player, player_exists
from .utils import get_member_nickname, check_permission
from .extension.config import ext_config
from .extension.utils import give_exp_and_track
from .extension.group_storage import record_season_stat
from .extension.anti_spam import check_cooldown

purchase_cmd = on_command("购买群友", aliases={"购买奴隶"}, priority=5, block=True)

@purchase_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await purchase_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "purchase")
    if not allowed:
        if msg:
            await purchase_cmd.finish(msg)
        return

    group_id = event.group_id
    user_id = event.user_id

    # 解析 @ 目标
    target_id = None
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            target_id = int(seg.data["qq"])
            break

    # 尝试从文本解析 QQ 号
    if target_id is None:
        text = args.extract_plain_text().strip()
        if text.isdigit():
            target_id = int(text)

    if target_id is None:
        await purchase_cmd.finish("请 @ 你要购买的群友")

    if target_id == user_id:
        await purchase_cmd.finish("不能购买自己！")

    # 排除机器人
    try:
        member = await bot.get_group_member_info(group_id=group_id, user_id=target_id)
        if str(member.get("role")).lower() in ("bot", "机器人") or member.get("is_robot"):
            await purchase_cmd.finish("不能购买机器人！")
    except Exception:
        pass

    nickname = await get_member_nickname(bot, group_id, user_id)
    target_nick = await get_member_nickname(bot, group_id, target_id)

    user_data = await ensure_player(group_id, user_id, nickname)

    # 冷却检查
    now = int(time.time())
    if not check_permission(event):
        remaining = plugin_config.purchase.cooldown - (now - user_data["lastPurchaseTime"])
        if remaining > 0:
            await purchase_cmd.finish(f"⏳ 购买冷却中...\n剩余: {remaining // 3600}小时{remaining % 3600 // 60}分钟")

    # 确保目标玩家数据存在（未参与过游戏的群友也可以被购买）
    target_data = await ensure_player(group_id, target_id, target_nick)

    # 不能购买已有主人的
    if target_data.get("master") and target_data["master"] != str(user_id):
        await purchase_cmd.finish(f"❌ {target_nick} 已经是别人的奴隶了！")

    # 不能购买自己的奴隶
    if target_id in user_data.get("slave", []):
        await purchase_cmd.finish(f"{target_nick} 已经是你的奴隶了！")

    # 计算价格
    price = target_data["value"]
    if user_data["currency"] < price:
        await purchase_cmd.finish(f"💰 金币不足！\n需要: {price} 金币\n当前: {user_data['currency']} 金币")

    # 执行购买
    user_data["currency"] -= price
    user_data["slave"] = list(user_data.get("slave", []))
    user_data["slave"].append(target_id)
    user_data["lastPurchaseTime"] = now

    target_data["master"] = str(user_id)
    target_data["value"] = int(target_data["value"] * 1.5)

    # 扩展追踪
    if ext_config.level.enabled:
        from .extension.utils import add_exp
        add_exp(user_data, ext_config.level.purchaseExp)
    user_data["purchaseCount"] = user_data.get("purchaseCount", 0) + 1
    give_exp_and_track(user_data, 0, "purchase")
    await record_season_stat(group_id, user_id, "purchaseCount")

    await save_player(group_id, user_id, user_data)
    await save_player(group_id, target_id, target_data)

    reply = (
        f"✅ {nickname} 成功购买了 {target_nick}！\n"
        f"花费: {price} 金币\n"
        f"{target_nick} 的新身价: {target_data['value']} 金币"
    )

    # BOT 陪玩触发
    try:
        from .bot_actions import try_bot_auto_action
        bot_msg = await try_bot_auto_action(bot, group_id, user_id, "purchase")
        if bot_msg:
            reply += "\n\n" + bot_msg
    except Exception:
        pass

    await purchase_cmd.finish(reply)
