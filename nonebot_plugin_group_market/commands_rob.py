"""抢劫指令"""
import random
import time
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg

from .config import plugin_config
from .storage import ensure_player, load_player, save_player, list_group_players
from .utils import get_member_nickname, check_permission
from .extension.anti_spam import check_cooldown

rob_cmd = on_command("抢劫", aliases={"rob"}, priority=5, block=True)

@rob_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await rob_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "rob")
    if not allowed:
        if msg:
            await rob_cmd.finish(msg)
        return

    group_id = event.group_id
    user_id = event.user_id

    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)

    now = int(time.time())
    cfg = plugin_config.rob

    if not check_permission(event):
        remaining = cfg.cooldown - (now - user_data.get("lastRobTime", 0))
        if remaining > 0:
            h = remaining // 3600
            m = (remaining % 3600) // 60
            await rob_cmd.finish(f"⏳ 抢劫冷却中...\n剩余: {h}小时{m}分钟")

    # 解析目标
    target_id = None
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            target_id = int(seg.data["qq"])
            break

    if target_id is None:
        # 随机目标
        players = await list_group_players(group_id)
        players = [p for p in players if p != user_id]
        if not players:
            await rob_cmd.finish("群里没有可抢劫的目标")
        target_id = random.choice(players)

    if target_id == user_id:
        await rob_cmd.finish("不能抢劫自己！")

    if str(target_id) == user_data.get("master", ""):
        await rob_cmd.finish("不能抢劫你的主人！")

    target_data = await load_player(group_id, target_id)
    if not target_data:
        await rob_cmd.finish("目标玩家没有参与游戏")

    target_nick = await get_member_nickname(bot, group_id, target_id)

    if random.random() < cfg.successRate:
        rob_amount = min(int(target_data["currency"] * 0.2), 100)
        if rob_amount <= 0:
            await rob_cmd.finish(f"{target_nick} 太穷了，没什么可抢的")
        user_data["currency"] += rob_amount
        target_data["currency"] -= rob_amount
        await save_player(group_id, user_id, user_data)
        await save_player(group_id, target_id, target_data)
        reply = (
            f"🔪 抢劫成功！\n"
            f"你从 {target_nick} 手中抢到了 {rob_amount} 金币！"
        )

        # BOT 陪玩触发
        try:
            from .bot_actions import try_bot_auto_action
            bot_msg = await try_bot_auto_action(bot, group_id, user_id, "rob")
            if bot_msg:
                reply += "\n\n" + bot_msg
        except Exception:
            pass

        await rob_cmd.finish(reply)
    else:
        penalty = min(int(user_data["currency"] * cfg.penalty), 50)
        user_data["currency"] -= penalty
        await save_player(group_id, user_id, user_data)
        reply = (
            f"😢 抢劫失败！\n"
            f"你被罚款 {penalty} 金币"
        )

        # BOT 陪玩触发
        try:
            from .bot_actions import try_bot_auto_action
            bot_msg = await try_bot_auto_action(bot, group_id, user_id, "rob")
            if bot_msg:
                reply += "\n\n" + bot_msg
        except Exception:
            pass

        await rob_cmd.finish(reply)
