"""训练指令"""
import random
import time
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg

from .config import plugin_config
from .storage import load_player, save_player
from .utils import get_member_nickname, check_permission
from .extension.config import ext_config
from .extension.utils import give_exp_and_track
from .extension.group_storage import record_season_stat
from .extension.anti_spam import check_cooldown

train_cmd = on_command("训练", aliases={"一键训练"}, priority=5, block=True)


@train_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await train_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "train")
    if not allowed:
        if msg:
            await train_cmd.finish(msg)
        return

    group_id = event.group_id
    user_id = event.user_id

    user_data = await load_player(group_id, user_id)
    if not user_data:
        await train_cmd.finish("你还没有参与游戏")

    now = int(time.time())
    cfg = plugin_config.training

    if not check_permission(event):
        remaining = cfg.cooldown - (now - user_data.get("lastTrainedTime", 0))
        if remaining > 0:
            h = remaining // 3600
            m = (remaining % 3600) // 60
            await train_cmd.finish(f"⏳ 训练冷却中...\n剩余: {h}小时{m}分钟")

    msg_text = event.get_plaintext().strip()
    is_batch = "一键" in msg_text

    slaves = user_data.get("slave", [])
    if not slaves:
        await train_cmd.finish("你没有奴隶可以训练")

    results = []
    if is_batch:
        for slave_id in slaves:
            sdata = await load_player(group_id, slave_id)
            if not sdata:
                continue
            sname = await get_member_nickname(bot, group_id, slave_id)
            cost = int(sdata["value"] * cfg.costRate)

            if user_data["currency"] < cost:
                results.append(f"❌ {sname} 金币不足，跳过")
                continue

            user_data["currency"] -= cost
            if random.random() < cfg.successRate:
                increase = int(sdata["value"] * cfg.valueIncreaseRate)
                sdata["value"] += increase
                results.append(f"✅ {sname} 训练成功！身价 +{increase}")
            else:
                sdata["value"] = max(100, sdata["value"] - 20)
                results.append(f"❌ {sname} 训练失败...身价 -20")

            await save_player(group_id, slave_id, sdata)

        # 扩展追踪
        success_count = sum(1 for r in results if "成功" in r)
        user_data["trainSuccessCount"] = user_data.get("trainSuccessCount", 0) + success_count
        if ext_config.level.enabled:
            from .extension.utils import add_exp
            add_exp(user_data, ext_config.level.trainExp * success_count)
        give_exp_and_track(user_data, 0, "train")
        await record_season_stat(group_id, user_id, "trainCount", success_count)

        user_data["lastTrainedTime"] = now
        await save_player(group_id, user_id, user_data)
        reply = f"📋 {await get_member_nickname(bot, group_id, user_id)} 的一键训练结果:\n" + "\n".join(results)

        # BOT 陪玩触发
        try:
            from .bot_actions import try_bot_auto_action
            bot_msg = await try_bot_auto_action(bot, group_id, user_id, "train")
            if bot_msg:
                reply += "\n\n" + bot_msg
        except Exception:
            pass

        await train_cmd.finish(reply)
    else:
        # 训练指定奴隶
        target_id = None
        for seg in event.message:
            if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
                target_id = int(seg.data["qq"])
                break

        if target_id is None:
            text = args.extract_plain_text().strip()
            if text.isdigit():
                target_id = int(text)

        if target_id is None or target_id not in slaves:
            await train_cmd.finish("请 @ 你要训练的奴隶")

        sdata = await load_player(group_id, target_id)
        sname = await get_member_nickname(bot, group_id, target_id)
        cost = int(sdata["value"] * cfg.costRate)

        if user_data["currency"] < cost:
            await train_cmd.finish(f"💰 金币不足！\n训练费用: {cost} 金币")

        user_data["currency"] -= cost
        if random.random() < cfg.successRate:
            increase = int(sdata["value"] * cfg.valueIncreaseRate)
            sdata["value"] += increase
            await save_player(group_id, target_id, sdata)
            # 扩展追踪
            user_data["trainSuccessCount"] = user_data.get("trainSuccessCount", 0) + 1
            if ext_config.level.enabled:
                from .extension.utils import add_exp
                add_exp(user_data, ext_config.level.trainExp)
            give_exp_and_track(user_data, 0, "train")
            await record_season_stat(group_id, user_id, "trainCount")
            user_data["lastTrainedTime"] = now
            await save_player(group_id, user_id, user_data)
            reply = f"✅ {sname} 训练成功！\n身价 +{increase}"

            # BOT 陪玩触发
            try:
                from .bot_actions import try_bot_auto_action
                bot_msg = await try_bot_auto_action(bot, group_id, user_id, "train")
                if bot_msg:
                    reply += "\n\n" + bot_msg
            except Exception:
                pass

            await train_cmd.finish(reply)
        else:
            sdata["value"] = max(100, sdata["value"] - 20)
            await save_player(group_id, target_id, sdata)
            user_data["lastTrainedTime"] = now
            await save_player(group_id, user_id, user_data)
            reply = f"❌ {sname} 训练失败...\n身价 -20"

            # BOT 陪玩触发
            try:
                from .bot_actions import try_bot_auto_action
                bot_msg = await try_bot_auto_action(bot, group_id, user_id, "train")
                if bot_msg:
                    reply += "\n\n" + bot_msg
            except Exception:
                pass

            await train_cmd.finish(reply)
