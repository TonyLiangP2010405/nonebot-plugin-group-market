"""打工指令"""
import random
import time
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg

from .config import plugin_config
from .storage import ensure_player, load_player, save_player
from .utils import get_member_nickname, check_permission
from .extension.config import ext_config
from .extension.utils import get_work_income_multiplier, give_exp_and_track
from .extension.group_storage import record_season_stat, get_today_event
from .extension.anti_spam import check_cooldown

work_cmd = on_command("打工", aliases={"工作", "一键打工"}, priority=5, block=True)

@work_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await work_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "work")
    if not allowed:
        if msg:
            await work_cmd.finish(msg)
        return

    group_id = event.group_id
    user_id = event.user_id

    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)

    now = int(time.time())
    cd = plugin_config.work.slaveownerCooldown if user_data["slave"] else plugin_config.work.cooldown

    if not check_permission(event):
        remaining = cd - (now - user_data["lastWorkingTime"])
        if remaining > 0:
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60
            await work_cmd.finish(f"⏳ 打工冷却中...\n剩余时间: {hours}小时{minutes}分钟")

    msg_text = event.get_plaintext().strip()
    is_batch = "一键" in msg_text

    results = []
    if is_batch and user_data["slave"]:
        for slave_id in user_data["slave"]:
            slave_data = await load_player(group_id, slave_id)
            if not slave_data:
                continue
            slave_nick = await get_member_nickname(bot, group_id, slave_id)
            fail = random.random() < 0.1
            if fail:
                slave_data["value"] = max(100, slave_data["value"] - 20)
                await save_player(group_id, slave_id, slave_data)
                results.append(f"❌ {slave_nick} 打工失败，身价-20")
            else:
                min_gold = 5 + slave_data["value"] // 20
                max_gold = 20 + slave_data["value"] // 10
                gold = random.randint(min_gold, max_gold)
                slave_data["currency"] += gold
                await save_player(group_id, slave_id, slave_data)
                results.append(f"✅ {slave_nick} 赚了 {gold} 金币")
    else:
        # 自己打工
        fail = random.random() < 0.1
        if fail:
            user_data["value"] = max(100, user_data["value"] - 20)
            await save_player(group_id, user_id, user_data)
            await work_cmd.finish("❌ 打工失败，身价-20")
        else:
            min_gold = 10 + user_data["value"] // 20
            max_gold = 100 + user_data["value"] // 10
            gold = random.randint(min_gold, max_gold)
            user_data["currency"] += gold

    # 扩展追踪
    if ext_config.level.enabled:
        exp_gain = ext_config.level.workExp
        if is_batch:
            exp_gain *= len([r for r in results if "赚了" in r])
        from .extension.utils import add_exp
        add_exp(user_data, exp_gain)
    user_data["workCount"] = user_data.get("workCount", 0) + (len([r for r in results if "赚了" in r]) if is_batch else 1)
    give_exp_and_track(user_data, 0, "work")
    await record_season_stat(group_id, user_id, "currencyGrowth", gold if not is_batch else sum([int(r.split("赚了 ")[1].split(" 金币")[0]) for r in results if "赚了" in r]))

    user_data["lastWorkingTime"] = now
    await save_player(group_id, user_id, user_data)

    if results:
        reply = f"📋 {nickname} 的一键打工结果:\n" + "\n".join(results)
    else:
        reply = f"✅ {nickname} 打工成功！\n获得金币: {gold}"
    await work_cmd.finish(reply)
