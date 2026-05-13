"""等级和经验系统"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .storage import ensure_player, load_player, save_player, list_group_players
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.utils import get_level_threshold, format_level_bar
from .extension.anti_spam import check_cooldown

level_cmd = on_command("我的等级", aliases={"等级信息", "我的信息"}, priority=5, block=True)
level_rank_cmd = on_command("等级排行", aliases={"等级排行榜"}, priority=5, block=True)


@level_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await level_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "level")
    if not allowed:
        if msg:
            await level_cmd.finish(msg)
        return

    if not ext_config.level.enabled:
        await level_cmd.finish("等级系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    level = data.get("level", 1)
    exp = data.get("exp", 0)
    threshold = get_level_threshold(level)

    bar = format_level_bar(exp, threshold)

    await level_cmd.finish(
        f"📊 {nickname} 的等级信息\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏆 等级: Lv.{level}\n"
        f"⭐ 经验: {exp} / {threshold}\n"
        f"{bar}\n"
        f"━━━━━━━━━━━━━━\n"
        f"💡 打工/训练/决斗/排位/购买/任务都能获得经验"
    )


@level_rank_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await level_rank_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "level_rank")
    if not allowed:
        if msg:
            await level_rank_cmd.finish(msg)
        return

    if not ext_config.level.enabled:
        await level_rank_cmd.finish("等级系统已关闭")

    group_id = event.group_id
    players = await list_group_players(group_id)

    items = []
    for pid in players:
        pdata = await load_player(group_id, pid)
        if pdata:
            items.append({
                "name": await get_member_nickname(bot, group_id, pid),
                "level": pdata.get("level", 1),
                "exp": pdata.get("exp", 0),
            })

    if not items:
        await level_rank_cmd.finish("暂无等级数据")

    items.sort(key=lambda x: (x["level"], x["exp"]), reverse=True)

    lines = ["🏆 等级排行榜"]
    for i, item in enumerate(items[:15], 1):
        lines.append(f"{i}. {item['name']} - Lv.{item['level']} (exp: {item['exp']})")

    await level_rank_cmd.finish("\n".join(lines))
