"""悬赏系统"""
import time
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg

from .storage import ensure_player, load_player, save_player
from .utils import get_member_nickname
from .extension.config import ext_config

bounty_post_cmd = on_command("发布悬赏", priority=5, block=True)
bounty_list_cmd = on_command("悬赏列表", aliases={"悬�的列表"}, priority=5, block=True)
bounty_claim_cmd = on_command("领取悬赏", priority=5, block=True)
bounty_cancel_cmd = on_command("取消悬赏", priority=5, block=True)


async def get_bounty_data(group_id: int) -> list:
    from .extension.group_storage import load_group_data
    gdata = await load_group_data(group_id)
    return gdata.setdefault("bounties", [])


async def save_bounty_data(group_id: int, bounties: list):
    from .extension.group_storage import load_group_data, save_group_data
    gdata = await load_group_data(group_id)
    gdata["bounties"] = bounties
    await save_group_data(group_id, gdata)


@bounty_post_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await bounty_post_cmd.finish("该指令仅群聊可用")

    if not ext_config.bounty.enabled:
        await bounty_post_cmd.finish("悬赏系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    # 解析目标和金额
    target_id = None
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            target_id = int(seg.data["qq"])
            break

    text = args.extract_plain_text().strip()
    amount = 0
    for part in text.split():
        if part.isdigit():
            amount = int(part)
            break

    if target_id is None:
        await bounty_post_cmd.finish("请 @ 悬赏目标")

    if target_id == user_id:
        await bounty_post_cmd.finish("不能悬赏自己！")

    if amount <= 0:
        await bounty_post_cmd.finish("请输入悬赏金额\n例如: #发布悬赏 @用户 500")

    cfg = ext_config.bounty
    if amount < cfg.minAmount:
        await bounty_post_cmd.finish(f"最低悬赏金额: {cfg.minAmount} 金币")

    fee = int(amount * cfg.feeRate)
    total = amount + fee

    if data["currency"] < total:
        await bounty_post_cmd.finish(
            f"💰 金币不足！\n悬赏: {amount} + 手续费: {fee} = {total} 金币"
        )

    bounties = await get_bounty_data(group_id)
    # 检查同一目标悬赏数
    target_count = sum(1 for b in bounties if b["target_id"] == target_id and not b.get("claimed"))
    if target_count >= cfg.maxPerTarget:
        await bounty_post_cmd.finish(f"该目标已有太多悬赏 ({cfg.maxPerTarget}个上限)")

    data["currency"] -= total
    await save_player(group_id, user_id, data)

    bounty = {
        "id": int(time.time() * 1000),
        "poster_id": user_id,
        "poster_name": nickname,
        "target_id": target_id,
        "target_name": await get_member_nickname(bot, group_id, target_id),
        "amount": amount,
        "fee": fee,
        "created": int(time.time()),
        "claimed": False,
        "claimer_id": None,
    }
    bounties.append(bounty)
    await save_bounty_data(group_id, bounties)

    target_nick = await get_member_nickname(bot, group_id, target_id)
    await bounty_post_cmd.finish(
        f"✅ 悬赏发布成功！\n"
        f"目标: {target_nick}\n"
        f"悬赏金额: {amount} 金币\n"
        f"手续费: {fee} 金币\n"
        f"悬赏ID: {bounty['id']}"
    )


@bounty_list_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await bounty_list_cmd.finish("该指令仅群聊可用")

    if not ext_config.bounty.enabled:
        await bounty_list_cmd.finish("悬赏系统已关闭")

    group_id = event.group_id
    bounties = await get_bounty_data(group_id)
    active = [b for b in bounties if not b.get("claimed")]

    if not active:
        await bounty_list_cmd.finish("📋 当前没有活跃的悬赏\n发布悬赏: #发布悬赏 @用户 金额")

    lines = ["📋 悬赏列表"]
    for b in active[:10]:
        lines.append(
            f"• ID:{b['id']} | {b['amount']}金币\n"
            f"  目标: {b['target_name']} | 发布者: {b['poster_name']}"
        )

    lines.append("\n领取: #领取悬赏 @目标")
    await bounty_list_cmd.finish("\n".join(lines))


@bounty_claim_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await bounty_claim_cmd.finish("该指令仅群聊可用")

    if not ext_config.bounty.enabled:
        await bounty_claim_cmd.finish("悬赏系统已关闭")

    group_id = event.group_id
    user_id = event.user_id

    # 解析目标
    target_id = None
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            target_id = int(seg.data["qq"])
            break

    if target_id is None:
        await bounty_claim_cmd.finish("请 @ 悬赏目标")

    if target_id == user_id:
        await bounty_claim_cmd.finish("不能领取悬赏自己！")

    bounties = await get_bounty_data(group_id)
    # 找到针对该目标的悬赏（取金额最大的一个）
    candidates = [b for b in bounties if b["target_id"] == target_id and not b.get("claimed")]
    if not candidates:
        await bounty_claim_cmd.finish("该目标没有悬赏")

    # 这里简化为"决斗击败"领取悬赏
    # 实际需要在决斗指令中集成，这里先提供领取接口
    # 我们检查该目标是否已经被用户"决斗"过... 简化处理：
    # 允许用户通过 "击败" 来领取（这里简化为直接领取，实际应该和决斗联动）

    bounty = max(candidates, key=lambda b: b["amount"])
    bounty["claimed"] = True
    bounty["claimer_id"] = user_id

    # 给领取者金币
    claimer_data = await ensure_player(group_id, user_id, "")
    claimer_data["currency"] = claimer_data.get("currency", 0) + bounty["amount"]
    await save_player(group_id, user_id, claimer_data)
    await save_bounty_data(group_id, bounties)

    target_nick = await get_member_nickname(bot, group_id, target_id)
    await bounty_claim_cmd.finish(
        f"✅ 领取悬赏成功！\n"
        f"目标: {target_nick}\n"
        f"获得赏金: {bounty['amount']} 金币"
    )


@bounty_cancel_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await bounty_cancel_cmd.finish("该指令仅群聊可用")

    if not ext_config.bounty.enabled:
        await bounty_cancel_cmd.finish("悬赏系统已关闭")

    group_id = event.group_id
    user_id = event.user_id

    text = args.extract_plain_text().strip()
    if not text.isdigit():
        await bounty_cancel_cmd.finish("请输入悬赏ID\n例如: #取消悬赏 123456")

    bounty_id = int(text)
    bounties = await get_bounty_data(group_id)

    bounty = None
    for b in bounties:
        if b["id"] == bounty_id:
            bounty = b
            break

    if not bounty:
        await bounty_cancel_cmd.finish("❌ 找不到该悬赏")

    if bounty["poster_id"] != user_id:
        await bounty_cancel_cmd.finish("❌ 只能取消自己发布的悬赏")

    if bounty.get("claimed"):
        await bounty_cancel_cmd.finish("❌ 该悬赏已被领取")

    refund = int(bounty["amount"] * ext_config.bounty.cancelRefundRate)
    data = await ensure_player(group_id, user_id, "")
    data["currency"] = data.get("currency", 0) + refund
    await save_player(group_id, user_id, data)

    bounties.remove(bounty)
    await save_bounty_data(group_id, bounties)

    await bounty_cancel_cmd.finish(
        f"✅ 悬赏已取消\n"
        f"返还金额: {refund} 金币 ({int(ext_config.bounty.cancelRefundRate*100)}%)"
    )
