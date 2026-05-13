"""我的奴隶 / 放生奴隶 指令"""
import time
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg

from .storage import ensure_player, load_player, save_player, player_exists
from .utils import get_member_nickname
from .extension.anti_spam import check_cooldown

myslave_cmd = on_command("我的奴隶", aliases={"我的群友"}, priority=5, block=True)
release_cmd = on_command("放生奴隶", priority=5, block=True)


@myslave_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await myslave_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "myslave")
    if not allowed:
        if msg:
            await myslave_cmd.finish(msg)
        return

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)

    lines = [
        f"📊 {nickname} 的奴隶信息",
        f"💰 金币: {user_data['currency']}",
        f"💎 身价: {user_data['value']}",
    ]

    if user_data.get("master"):
        master_nick = await get_member_nickname(bot, group_id, int(user_data["master"]))
        lines.append(f"👑 主人: {master_nick}")
    else:
        lines.append("👑 主人: 无（自由身）")

    slaves = user_data.get("slave", [])
    if slaves:
        lines.append(f"\n🧑‍🌾 奴隶 ({len(slaves)}人):")
        for sid in slaves:
            sdata = await load_player(group_id, sid)
            sname = await get_member_nickname(bot, group_id, sid)
            sval = sdata["value"] if sdata else "?"
            lines.append(f"  • {sname} (身价: {sval})")
    else:
        lines.append("\n🧑‍🌾 奴隶: 无")

    await myslave_cmd.finish("\n".join(lines))


@release_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await release_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "release")
    if not allowed:
        if msg:
            await release_cmd.finish(msg)
        return

    group_id = event.group_id
    user_id = event.user_id

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
        await release_cmd.finish("请 @ 你要放生的奴隶")

    user_data = await load_player(group_id, user_id)
    if not user_data:
        await release_cmd.finish("你还没有参与游戏")

    if target_id not in user_data.get("slave", []):
        await release_cmd.finish("该用户不是你的奴隶")

    # 移除奴隶关系
    user_data["slave"] = [s for s in user_data["slave"] if s != target_id]
    await save_player(group_id, user_id, user_data)

    target_data = await load_player(group_id, target_id)
    if target_data:
        target_data["master"] = ""
        await save_player(group_id, target_id, target_data)

    target_nick = await get_member_nickname(bot, group_id, target_id)
    await release_cmd.finish(f"✅ 你已放生 {target_nick}")
