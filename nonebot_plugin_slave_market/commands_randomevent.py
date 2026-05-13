"""随机事件系统"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .storage import ensure_player
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.group_storage import get_today_event, ensure_group_data
from .extension.anti_spam import check_cooldown

today_event_cmd = on_command("今日事件", aliases={"群事件", "今天事件"}, priority=5, block=True)


@today_event_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await today_event_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "event")
    if not allowed:
        if msg:
            await today_event_cmd.finish(msg)
        return

    if not ext_config.randomEvent.enabled:
        await today_event_cmd.finish("随机事件系统已关闭")

    group_id = event.group_id
    await ensure_group_data(group_id)
    evt = await get_today_event(group_id)

    if not evt:
        await today_event_cmd.finish("今天没有特殊事件，一切正常~")

    lines = [
        f"📢 今日群事件",
        f"━━━━━━━━━━━━━━",
        f"📌 {evt['name']}",
        f"📝 {evt['description']}",
    ]

    effect = evt.get("effect", {})
    if effect:
        lines.append("\n📊 效果影响:")
        if "workIncome" in effect:
            lines.append(f"  • 打工收益: {'+' if effect['workIncome'] > 0 else ''}{int(effect['workIncome']*100)}%")
        if "bankInterest" in effect:
            lines.append(f"  • 银行利息: {'+' if effect['bankInterest'] > 0 else ''}{int(effect['bankInterest']*100)}%")
        if "trainSuccess" in effect:
            lines.append(f"  • 训练成功率: {'+' if effect['trainSuccess'] > 0 else ''}{int(effect['trainSuccess']*100)}%")
        if "arenaReward" in effect:
            lines.append(f"  • 决斗奖励: {'+' if effect['arenaReward'] > 0 else ''}{int(effect['arenaReward']*100)}%")
        if "purchaseCost" in effect:
            lines.append(f"  • 购买价格: {'+' if effect['purchaseCost'] > 0 else ''}{int(effect['purchaseCost']*100)}%")
        if "purchaseTaxCut" in effect:
            lines.append(f"  • 购买税率降低")

    lines.append("━━━━━━━━━━━━━━")
    lines.append("事件每天0点自动刷新")

    await today_event_cmd.finish("\n".join(lines))
