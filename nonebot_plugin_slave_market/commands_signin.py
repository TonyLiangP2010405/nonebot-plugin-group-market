"""签到系统"""
import time
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .storage import ensure_player, save_player
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.utils import get_today_str, add_exp

signin_cmd = on_command("签到", aliases={"每日签到", "打卡"}, priority=5, block=True)
signin_rank_cmd = on_command("签到排行", priority=5, block=True)


@signin_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await signin_cmd.finish("该指令仅群聊可用")

    if not ext_config.signIn.enabled:
        await signin_cmd.finish("签到系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    today = get_today_str()
    last_sign = data.get("lastSignInDate", "")
    continuous = data.get("continuousSignInDays", 0)

    if last_sign == today:
        await signin_cmd.finish("⏳ 今天已经签到过了，明天再来吧！")

    # 判断是否连续
    yesterday = (time.time() - 86400)
    yesterday_str = time.strftime("%Y-%m-%d", time.localtime(yesterday))
    if last_sign == yesterday_str:
        continuous += 1
    else:
        continuous = 1

    cfg = ext_config.signIn
    bonus = min(cfg.continuousBonus * (continuous - 1), cfg.maxContinuousBonus)
    total_reward = cfg.baseReward + bonus
    exp_reward = cfg.rewardExp

    data["currency"] = data.get("currency", 0) + total_reward
    data["lastSignInDate"] = today
    data["continuousSignInDays"] = continuous
    data["totalSignInDays"] = data.get("totalSignInDays", 0) + 1

    # 里程碑奖励
    milestone_text = ""
    if continuous == 7:
        data["currency"] += cfg.milestone7.get("currency", 0)
        exp_reward += cfg.milestone7.get("exp", 0)
        milestone_text = "\n🎁 7天连续签到额外奖励！"
    elif continuous == 30:
        data["currency"] += cfg.milestone30.get("currency", 0)
        exp_reward += cfg.milestone30.get("exp", 0)
        milestone_text = "\n🎁 30天连续签到额外奖励！"

    leveled_up, new_level, old_level = add_exp(data, exp_reward)
    await save_player(group_id, user_id, data)

    level_text = f"\n🆙 等级提升！{old_level} → {new_level}" if leveled_up else ""

    await signin_cmd.finish(
        f"✅ {nickname} 签到成功！\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 金币 +{total_reward}\n"
        f"⭐ 经验 +{exp_reward}\n"
        f"🔥 连续签到: {continuous} 天\n"
        f"📊 累计签到: {data['totalSignInDays']} 天\n"
        f"{milestone_text}{level_text}"
    )


@signin_rank_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await signin_rank_cmd.finish("该指令仅群聊可用")

    if not ext_config.signIn.enabled:
        await signin_rank_cmd.finish("签到系统已关闭")

    from .storage import list_group_players, load_player
    group_id = event.group_id
    players = await list_group_players(group_id)

    items = []
    for pid in players:
        pdata = await load_player(group_id, pid)
        if pdata:
            items.append({
                "name": await get_member_nickname(bot, group_id, pid),
                "continuous": pdata.get("continuousSignInDays", 0),
                "total": pdata.get("totalSignInDays", 0),
            })

    if not items:
        await signin_rank_cmd.finish("暂无签到数据")

    items.sort(key=lambda x: (x["continuous"], x["total"]), reverse=True)

    lines = ["🔥 签到排行榜"]
    for i, item in enumerate(items[:15], 1):
        lines.append(f"{i}. {item['name']} - 连续{item['continuous']}天 (累计{item['total']}天)")

    await signin_rank_cmd.finish("\n".join(lines))
