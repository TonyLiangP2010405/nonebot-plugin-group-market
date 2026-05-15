"""称号系统"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg

from .storage import ensure_player, save_player
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.utils import get_title_info
from .extension.anti_spam import check_cooldown

title_cmd = on_command("我的称号", aliases={"称号", "称号列表"}, priority=5, block=True)
equip_title_cmd = on_command("佩戴称号", priority=5, block=True)


@title_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await title_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "title")
    if not allowed:
        if msg:
            await title_cmd.finish(msg)
        return

    if not ext_config.title.enabled:
        await title_cmd.finish("称号系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    owned = data.setdefault("titles", [])
    equipped = data.get("equippedTitle", "")

    # 检查是否有新称号可解锁
    titles_def = ext_config.title.titles
    newly = []
    for tdef in titles_def:
        tid = tdef["id"]
        if tid in owned:
            continue
        # 检查获得条件
        if _check_title_condition(data, tid):
            owned.append(tid)
            newly.append(tdef["name"])

    if newly:
        await save_player(group_id, user_id, data)

    lines = [f"👑 {nickname} 的称号"]
    if newly:
        lines.append(f"🎉 新解锁称号: {'、'.join(newly)}")

    lines.append(f"\n当前佩戴: {get_title_info(equipped)['name'] if equipped else '无'}")
    lines.append("\n已拥有:")

    for tdef in titles_def:
        tid = tdef["id"]
        if tid in owned:
            mark = "▸" if tid == equipped else "  "
            rare_mark = "🔥" if tdef.get("rare") else ""
            lines.append(f"{mark} {tdef['name']} {rare_mark}\n    来源: {tdef['source']}")

    if not owned:
        lines.append("(暂无称号)")

    lines.append("\n佩戴: /佩戴称号 称号名")
    await title_cmd.finish("\n".join(lines))


@equip_title_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await equip_title_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "equip_title")
    if not allowed:
        if msg:
            await equip_title_cmd.finish(msg)
        return

    if not ext_config.title.enabled:
        await equip_title_cmd.finish("称号系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    title_name = args.extract_plain_text().strip()
    if not title_name:
        await equip_title_cmd.finish("请输入要佩戴的称号名")

    # 查找称号
    found = None
    for tdef in ext_config.title.titles:
        if tdef["name"] == title_name or tdef["id"] == title_name:
            found = tdef
            break

    if not found:
        await equip_title_cmd.finish(f"❌ 没有找到称号 '{title_name}'")

    if found["id"] not in data.get("titles", []):
        await equip_title_cmd.finish(f"❌ 你还没有解锁称号 '{found['name']}'")

    data["equippedTitle"] = found["id"]
    await save_player(group_id, user_id, data)
    await equip_title_cmd.finish(f"✅ 已佩戴称号: {found['name']}")


def _check_title_condition(data: dict, title_id: str) -> bool:
    """检查称号解锁条件"""
    checks = {
        "novice": lambda d: True,
        "rich": lambda d: d.get("bank", {}).get("balance", 0) >= 10000,
        "duelist": lambda d: d.get("duelStats", {}).get("wins", 0) >= 10,
        "collector": lambda d: len(d.get("slave", [])) >= 5,
        "master": lambda d: d.get("level", 1) >= 20,
        "legend": lambda d: d.get("level", 1) >= 50,
        "early_bird": lambda d: d.get("continuousSignInDays", 0) >= 7,
        "dedication": lambda d: d.get("continuousSignInDays", 0) >= 30,
    }
    fn = checks.get(title_id)
    return fn(data) if fn else False
