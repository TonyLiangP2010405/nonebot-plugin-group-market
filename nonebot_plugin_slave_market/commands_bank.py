"""银行指令"""
import math
import time
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg

from .config import plugin_config
from .storage import ensure_player, load_player, save_player
from .utils import get_member_nickname

deposit_cmd = on_command("存款", aliases={"一键存款"}, priority=5, block=True)
withdraw_cmd = on_command("取款", priority=5, block=True)
upgrade_cmd = on_command("升级信用", aliases={"一键升级信用"}, priority=5, block=True)
bank_info_cmd = on_command("银行信息", priority=5, block=True)
interest_cmd = on_command("领取利息", priority=5, block=True)
transfer_cmd = on_command("转账", priority=5, block=True)


@deposit_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await deposit_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)

    bank = user_data.setdefault("bank", {
        "balance": 0, "level": 1, "limit": plugin_config.bank.initialLimit,
        "upgradePrice": plugin_config.bank.initialUpgradePrice, "lastInterestTime": 0
    })

    msg_text = event.get_plaintext().strip()
    is_batch = "一键" in msg_text

    if is_batch:
        amount = user_data["currency"]
    else:
        text = args.extract_plain_text().strip()
        if not text.isdigit():
            await deposit_cmd.finish("请输入存款金额\n例如: #存款 100")
        amount = int(text)

    if amount <= 0:
        await deposit_cmd.finish("存款金额必须大于0")

    if user_data["currency"] < amount:
        await deposit_cmd.finish(f"💰 金币不足！\n当前: {user_data['currency']} 金币")

    if bank["balance"] + amount > bank["limit"]:
        await deposit_cmd.finish(
            f"❌ 超出银行限额！\n"
            f"当前存款: {bank['balance']}\n"
            f"限额: {bank['limit']}\n"
            f"可存: {bank['limit'] - bank['balance']} 金币"
        )

    user_data["currency"] -= amount
    bank["balance"] += amount
    await save_player(group_id, user_id, user_data)

    await deposit_cmd.finish(
        f"✅ 存款成功！\n"
        f"存入: {amount} 金币\n"
        f"银行余额: {bank['balance']} 金币\n"
        f"剩余金币: {user_data['currency']} 金币"
    )


@withdraw_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await withdraw_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)
    bank = user_data.setdefault("bank", {
        "balance": 0, "level": 1, "limit": plugin_config.bank.initialLimit,
        "upgradePrice": plugin_config.bank.initialUpgradePrice, "lastInterestTime": 0
    })

    text = args.extract_plain_text().strip()
    if not text.isdigit():
        await withdraw_cmd.finish("请输入取款金额\n例如: #取款 100")
    amount = int(text)

    if amount <= 0:
        await withdraw_cmd.finish("取款金额必须大于0")
    if bank["balance"] < amount:
        await withdraw_cmd.finish(f"❌ 银行余额不足！\n当前存款: {bank['balance']} 金币")

    bank["balance"] -= amount
    user_data["currency"] += amount
    await save_player(group_id, user_id, user_data)

    await withdraw_cmd.finish(
        f"✅ 取款成功！\n"
        f"取出: {amount} 金币\n"
        f"银行余额: {bank['balance']} 金币\n"
        f"持有金币: {user_data['currency']} 金币"
    )


@upgrade_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await upgrade_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)
    bank = user_data.setdefault("bank", {
        "balance": 0, "level": 1, "limit": plugin_config.bank.initialLimit,
        "upgradePrice": plugin_config.bank.initialUpgradePrice, "lastInterestTime": 0
    })

    msg_text = event.get_plaintext().strip()
    is_batch = "一键" in msg_text

    results = []
    while True:
        price = bank["upgradePrice"]
        if user_data["currency"] < price:
            if not results:
                await upgrade_cmd.finish(f"💰 金币不足！\n升级需要: {price} 金币")
            break

        user_data["currency"] -= price
        bank["level"] += 1
        bank["limit"] = int(bank["limit"] * plugin_config.bank.limitIncreaseMulti)
        bank["upgradePrice"] = int(bank["upgradePrice"] * plugin_config.bank.upgradePriceMulti)
        results.append(f"等级 {bank['level']-1} → {bank['level']}, 限额 {bank['limit']}")

        if not is_batch:
            break

    await save_player(group_id, user_id, user_data)

    if is_batch:
        reply = f"📋 一键升级信用结果:\n" + "\n".join(results)
    else:
        reply = (
            f"✅ 升级成功！\n"
            f"当前等级: {bank['level']}\n"
            f"银行限额: {bank['limit']} 金币\n"
            f"下次升级: {bank['upgradePrice']} 金币\n"
            f"剩余金币: {user_data['currency']} 金币"
        )
    await upgrade_cmd.finish(reply)


@bank_info_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await bank_info_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)
    bank = user_data.setdefault("bank", {
        "balance": 0, "level": 1, "limit": plugin_config.bank.initialLimit,
        "upgradePrice": plugin_config.bank.initialUpgradePrice, "lastInterestTime": 0
    })

    # 计算可领利息
    now = int(time.time())
    hours = min((now - bank.get("lastInterestTime", 0)) // 3600, plugin_config.bank.maxInterestTime)
    interest = int(bank["balance"] * plugin_config.bank.interestRate * hours)

    await bank_info_cmd.finish(
        f"🏦 {nickname} 的银行信息\n"
        f"━━━━━━━━━━━━━━\n"
        f"💰 存款: {bank['balance']} 金币\n"
        f"📊 等级: {bank['level']}\n"
        f"📈 限额: {bank['limit']} 金币\n"
        f"🔧 升级费用: {bank['upgradePrice']} 金币\n"
        f"💵 可领利息: {interest} 金币 ({hours}小时)\n"
        f"━━━━━━━━━━━━━━"
    )


@interest_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await interest_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)
    bank = user_data.setdefault("bank", {
        "balance": 0, "level": 1, "limit": plugin_config.bank.initialLimit,
        "upgradePrice": plugin_config.bank.initialUpgradePrice, "lastInterestTime": 0
    })

    now = int(time.time())
    hours = min((now - bank.get("lastInterestTime", 0)) // 3600, plugin_config.bank.maxInterestTime)
    if hours <= 0:
        await interest_cmd.finish("⏳ 暂无利息可领取，请稍后再来")

    interest = int(bank["balance"] * plugin_config.bank.interestRate * hours)
    if interest <= 0:
        await interest_cmd.finish("⏳ 存款太少，暂无利息")

    bank["balance"] += interest
    bank["lastInterestTime"] = now
    await save_player(group_id, user_id, user_data)

    await interest_cmd.finish(
        f"✅ 领取利息成功！\n"
        f"利息: {interest} 金币\n"
        f"银行余额: {bank['balance']} 金币"
    )


@transfer_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await transfer_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    user_id = event.user_id

    # 解析金额和目标
    text = args.extract_plain_text().strip()
    parts = text.split()
    if not parts[0].isdigit():
        await transfer_cmd.finish("请输入转账金额\n例如: #转账 100 @用户")
    amount = int(parts[0])

    target_id = None
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            target_id = int(seg.data["qq"])
            break

    if target_id is None:
        await transfer_cmd.finish("请 @ 转账目标")

    if target_id == user_id:
        await transfer_cmd.finish("不能转账给自己！")

    if amount < plugin_config.transfer.minAmount:
        await transfer_cmd.finish(f"最低转账金额: {plugin_config.transfer.minAmount} 金币")

    nickname = await get_member_nickname(bot, group_id, user_id)
    user_data = await ensure_player(group_id, user_id, nickname)

    fee = int(amount * plugin_config.transfer.feeRate)
    total = amount + fee

    if user_data["currency"] < total:
        await transfer_cmd.finish(
            f"💰 金币不足！\n"
            f"转账: {amount} 金币\n"
            f"手续费: {fee} 金币\n"
            f"总计: {total} 金币\n"
            f"当前: {user_data['currency']} 金币"
        )

    target_data = await ensure_player(group_id, target_id, "")

    user_data["currency"] -= total
    target_data["currency"] += amount

    await save_player(group_id, user_id, user_data)
    await save_player(group_id, target_id, target_data)

    target_nick = await get_member_nickname(bot, group_id, target_id)
    await transfer_cmd.finish(
        f"✅ 转账成功！\n"
        f"转给: {target_nick}\n"
        f"金额: {amount} 金币\n"
        f"手续费: {fee} 金币\n"
        f"剩余: {user_data['currency']} 金币"
    )
