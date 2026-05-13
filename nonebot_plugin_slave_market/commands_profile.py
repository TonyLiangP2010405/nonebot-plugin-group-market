"""个人信息面板"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg

from .storage import ensure_player, load_player
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.utils import get_level_threshold, format_level_bar, get_today_event
from .extension.group_storage import ensure_group_data

profile_cmd = on_command("我的信息", aliases={"个人信息", "个人面板"}, priority=5, block=True)
view_profile_cmd = on_command("查看信息", priority=5, block=True)


@profile_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await profile_cmd.finish("该指令仅群聊可用")

    if not ext_config.profile.enabled:
        await profile_cmd.finish("个人信息面板已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    await _send_profile(bot, event, group_id, user_id, nickname, data, profile_cmd)


@view_profile_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await view_profile_cmd.finish("该指令仅群聊可用")

    if not ext_config.profile.enabled:
        await view_profile_cmd.finish("个人信息面板已关闭")

    group_id = event.group_id
    target_id = None
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            target_id = int(seg.data["qq"])
            break

    if target_id is None:
        text = args.extract_plain_text().strip()
        if text.isdigit():
            target_id = int(text)

    if target_id is None:
        await view_profile_cmd.finish("请 @ 要查看的用户")

    target_nick = await get_member_nickname(bot, group_id, target_id)
    data = await load_player(group_id, target_id)
    if not data:
        await view_profile_cmd.finish("该用户还没有参与游戏")

    await _send_profile(bot, event, group_id, target_id, target_nick, data, view_profile_cmd)


async def _send_profile(bot, event, group_id, user_id, nickname, data, matcher):
    level = data.get("level", 1)
    exp = data.get("exp", 0)
    threshold = get_level_threshold(level)
    bar = format_level_bar(exp, threshold)
    currency = data.get("currency", 0)
    bank_balance = data.get("bank", {}).get("balance", 0)
    value = data.get("value", 100)
    master = data.get("master", "")
    slaves = data.get("slave", [])
    duel_stats = data.get("duelStats", {"wins": 0, "losses": 0})
    ranking = data.get("ranking", {"score": 1000, "tier": "青铜"})
    equipped_title = data.get("equippedTitle", "")
    achievements = data.get("achievements", [])
    inventory = data.get("inventory", {})
    continuous_sign = data.get("continuousSignInDays", 0)

    title_text = ""
    if equipped_title:
        from .extension.utils import get_title_info
        tinfo = get_title_info(equipped_title)
        if tinfo:
            title_text = f"[{tinfo['name']}] "

    master_text = "自由身"
    if master:
        try:
            mname = await get_member_nickname(bot, group_id, int(master))
            master_text = mname
        except:
            master_text = "未知"

    inv_count = sum(inventory.values()) if inventory else 0

    lines = [
        f"📊 {title_text}{nickname} 的信息面板",
        f"━━━━━━━━━━━━━━",
        f"💰 金币: {currency}",
        f"🏦 银行存款: {bank_balance}",
        f"💎 身价: {value}",
        f"🏆 等级: Lv.{level} (exp: {exp}/{threshold})",
        f"{bar}",
        f"👑 主人: {master_text}",
        f"🧑‍🌾 奴隶: {len(slaves)}人",
        f"⚔️ 决斗: {duel_stats.get('wins', 0)}胜 {duel_stats.get('losses', 0)}负",
        f"📊 排位: {ranking.get('tier', '青铜')} ({ranking.get('score', 1000)}分)",
        f"🏅 成就: {len(achievements)}个",
        f"🎒 道具: {inv_count}件",
        f"🔥 连续签到: {continuous_sign}天",
    ]

    # 今日事件
    event_data = await get_today_event(group_id)
    if event_data:
        lines.append(f"📢 今日事件: {event_data['name']} - {event_data['description']}")

    lines.append("━━━━━━━━━━━━━━")

    await matcher.finish("\n".join(lines))
