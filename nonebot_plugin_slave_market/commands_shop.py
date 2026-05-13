"""道具商店系统"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg

from .storage import ensure_player, save_player
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.utils import get_item_info, get_item_name, give_item, consume_item, random_box_reward

shop_cmd = on_command("商店", aliases={"道具商店", "商城"}, priority=5, block=True)
buy_item_cmd = on_command("购买道具", aliases={"买道具"}, priority=5, block=True)
my_items_cmd = on_command("我的道具", aliases={"道具", "背包"}, priority=5, block=True)
use_item_cmd = on_command("使用道具", priority=5, block=True)
gift_item_cmd = on_command("赠送道具", priority=5, block=True)


@shop_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await shop_cmd.finish("该指令仅群聊可用")

    if not ext_config.shop.enabled:
        await shop_cmd.finish("商店系统已关闭")

    lines = ["🛒 道具商店"]
    lines.append("━━━━━━━━━━━━━━")
    for item in ext_config.shop.items:
        lines.append(f"• {item['name']} - {item['price']}金币")
        lines.append(f"  {item['description']}")

    lines.append("━━━━━━━━━━━━━━")
    lines.append("购买: #购买道具 道具名")
    lines.append("使用: #使用道具 道具名")
    lines.append("赠送: #赠送道具 @用户 道具名")

    await shop_cmd.finish("\n".join(lines))


@buy_item_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await buy_item_cmd.finish("该指令仅群聊可用")

    if not ext_config.shop.enabled:
        await buy_item_cmd.finish("商店系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    item_name = args.extract_plain_text().strip()
    if not item_name:
        await buy_item_cmd.finish("请输入要购买的道具名\n例如: #购买道具 打工加成卡")

    # 模糊匹配
    item = None
    for it in ext_config.shop.items:
        if it["name"] == item_name or it["id"] == item_name:
            item = it
            break

    if item is None:
        await buy_item_cmd.finish(f"❌ 没有找到道具 '{item_name}'，输入 #商店 查看列表")

    price = item["price"]
    if data["currency"] < price:
        await buy_item_cmd.finish(f"💰 金币不足！{item['name']} 需要 {price} 金币")

    # 检查库存上限
    inv = data.setdefault("inventory", {})
    current = inv.get(item["id"], 0)
    if current >= item.get("maxStack", 99):
        await buy_item_cmd.finish(f"❌ {item['name']} 已达持有上限 ({item.get('maxStack', 99)})")

    data["currency"] -= price
    give_item(data, item["id"])
    await save_player(group_id, user_id, data)

    await buy_item_cmd.finish(
        f"✅ 购买成功！\n"
        f"{item['name']} x1\n"
        f"花费: {price} 金币\n"
        f"剩余: {data['currency']} 金币"
    )


@my_items_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await my_items_cmd.finish("该指令仅群聊可用")

    if not ext_config.shop.enabled:
        await my_items_cmd.finish("商店系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    inv = data.get("inventory", {})
    if not inv:
        await my_items_cmd.finish("🎒 背包空空如也\n去 #商店 买点东西吧！")

    lines = [f"🎒 {nickname} 的背包"]
    lines.append("━━━━━━━━━━━━━━")
    for item_id, count in inv.items():
        name = get_item_name(item_id)
        lines.append(f"• {name} x{count}")

    lines.append("━━━━━━━━━━━━━━")
    lines.append("使用: #使用道具 道具名")
    await my_items_cmd.finish("\n".join(lines))


@use_item_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await use_item_cmd.finish("该指令仅群聊可用")

    if not ext_config.shop.enabled:
        await use_item_cmd.finish("商店系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    item_name = args.extract_plain_text().strip()
    if not item_name:
        await use_item_cmd.finish("请输入要使用的道具名")

    # 查找道具ID
    item_id = None
    item_cfg = None
    for it in ext_config.shop.items:
        if it["name"] == item_name or it["id"] == item_name:
            item_id = it["id"]
            item_cfg = it
            break

    if item_id is None:
        await use_item_cmd.finish(f"❌ 没有找到道具 '{item_name}'")

    if not consume_item(data, item_id):
        await use_item_cmd.finish(f"❌ 你没有 {item_cfg['name']}，去 #商店 购买吧")

    # 道具效果
    result_text = ""
    if item_id == "work_boost":
        result_text = "已激活打工加成卡！下次打工收益 +50%"
    elif item_id == "train_protect":
        result_text = "已激活训练保护券！下次训练失败不掉身价"
    elif item_id == "arena_shield":
        result_text = "已激活决斗保护盾！下次决斗减少失败惩罚"
    elif item_id == "bank_expand":
        bank = data.setdefault("bank", {})
        bank["limit"] = bank.get("limit", 1000) + 500
        result_text = "银行限额 +500！"
    elif item_id == "task_refresh":
        result_text = "任务刷新券已准备就绪，使用 #刷新任务 时自动消耗"
    elif item_id == "random_box":
        reward = random_box_reward()
        if reward["type"] == "currency":
            data["currency"] += reward["amount"]
        elif reward["type"] == "exp":
            from .extension.utils import add_exp
            add_exp(data, reward["amount"])
        elif reward["type"] == "item":
            give_item(data, reward["itemId"], reward["amount"])
        result_text = reward["text"]
    else:
        result_text = f"使用了 {item_cfg['name']}"

    await save_player(group_id, user_id, data)
    await use_item_cmd.finish(f"✅ {result_text}")


@gift_item_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await gift_item_cmd.finish("该指令仅群聊可用")

    if not ext_config.shop.enabled:
        await gift_item_cmd.finish("商店系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    # 解析目标
    target_id = None
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            target_id = int(seg.data["qq"])
            break

    item_name = args.extract_plain_text().strip()
    # 去掉@的QQ号
    if target_id:
        for seg in event.message:
            if seg.type == "at":
                item_name = item_name.replace(str(seg.data.get("qq", "")), "").strip()

    if target_id is None:
        await gift_item_cmd.finish("请 @ 要赠送的用户")

    if target_id == user_id:
        await gift_item_cmd.finish("不能赠送给自己！")

    if not item_name:
        await gift_item_cmd.finish("请输入要赠送的道具名")

    # 查找道具
    item_id = None
    item_cfg = None
    for it in ext_config.shop.items:
        if it["name"] == item_name or it["id"] == item_name:
            item_id = it["id"]
            item_cfg = it
            break

    if item_id is None:
        await gift_item_cmd.finish(f"❌ 没有找到道具 '{item_name}'")

    if not consume_item(data, item_id):
        await gift_item_cmd.finish(f"❌ 你没有 {item_cfg['name']}")

    # 给目标
    from .storage import ensure_player as ep2
    target_data = await ep2(group_id, target_id, "")
    give_item(target_data, item_id)
    await save_player(group_id, user_id, data)
    await save_player(group_id, target_id, target_data)

    target_nick = await get_member_nickname(bot, group_id, target_id)
    await gift_item_cmd.finish(f"✅ 你向 {target_nick} 赠送了 {item_cfg['name']} x1")
