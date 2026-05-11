"""排行榜指令 (#奴隶市场 / #排行榜)"""
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .storage import load_player, list_group_players
from .utils import get_member_nickname

rankings_cmd = on_command("奴隶市场", aliases={"排行榜"}, priority=5, block=True)


@rankings_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await rankings_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    players = await list_group_players(group_id)

    msg_text = event.get_plaintext()
    sort_by = "value" if "身价" in msg_text or "价值" in msg_text else "currency"

    items = []
    for pid in players:
        pdata = await load_player(group_id, pid)
        if not pdata:
            continue
        pname = await get_member_nickname(bot, group_id, pid)
        slave_count = len(pdata.get("slave", []))
        items.append({
            "name": pname,
            "currency": pdata.get("currency", 0),
            "value": pdata.get("value", 100),
            "slave_count": slave_count,
        })

    if not items:
        await rankings_cmd.finish("暂无排行榜数据")

    items.sort(key=lambda x: x[sort_by], reverse=True)

    lines = [f"📊 {'身价' if sort_by == 'value' else '金币'}排行榜"]
    for i, item in enumerate(items[:15], 1):
        lines.append(
            f"{i}. {item['name']} - "
            f"{'身价' if sort_by == 'value' else '金币'}: {item[sort_by]} "
            f"(奴隶: {item['slave_count']}人)"
        )

    await rankings_cmd.finish("\n".join(lines))
