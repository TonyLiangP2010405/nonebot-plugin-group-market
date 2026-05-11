"""每周重置相关指令"""
import time
from datetime import datetime, timedelta
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.permission import SUPERUSER

from .config import plugin_config
from .storage import load_player, save_player, list_groups, list_group_players
from .storage import save_weekly_reset_tracking, load_weekly_reset_tracking, save_ranking_history, get_last_week_ranking_history
from .utils import get_member_nickname, check_permission

reset_status_cmd = on_command("奴隶重置状态", priority=5, block=True)
manual_reset_cmd = on_command("手动奴隶重置", priority=5, block=True)
reset_help_cmd = on_command("奴隶重置帮助", priority=5, block=True)
last_week_cmd = on_command("上周排行榜", priority=5, block=True)


@reset_status_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await reset_status_cmd.finish("该指令仅群聊可用")

    cfg = plugin_config.weeklyReset
    now = datetime.now()

    # 计算下次重置时间
    days_until = (cfg.resetTime.day - now.isoweekday()) % 7
    next_reset = now + timedelta(days=days_until)
    next_reset = next_reset.replace(
        hour=cfg.resetTime.hour, minute=cfg.resetTime.minute, second=0, microsecond=0
    )
    if next_reset <= now:
        next_reset += timedelta(days=7)

    tracking = load_weekly_reset_tracking()

    await reset_status_cmd.finish(
        f"📅 每周重置状态\n"
        f"━━━━━━━━━━━━━━\n"
        f"⏰ 下次重置: {next_reset.strftime('%Y-%m-%d %H:%M')}\n"
        f"📊 已重置次数: {tracking.get('resetCount', 0)}\n"
        f"🔧 上次重置: {datetime.fromtimestamp(tracking.get('lastResetTime', 0)).strftime('%Y-%m-%d %H:%M') if tracking.get('lastResetTime') else '从未'}\n"
        f"━━━━━━━━━━━━━━"
    )


@manual_reset_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await manual_reset_cmd.finish("该指令仅群聊可用")

    # 权限检查
    if not check_permission(event):
        # 检查群管理员
        try:
            info = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
            if info.get("role") not in ("owner", "admin"):
                await manual_reset_cmd.finish("只有管理员可以手动重置")
        except Exception:
            await manual_reset_cmd.finish("只有管理员可以手动重置")

    from .weekly_reset_task import perform_weekly_reset
    result = await perform_weekly_reset(event.group_id)
    await manual_reset_cmd.finish(result)


@reset_help_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await reset_help_cmd.finish("该指令仅群聊可用")

    cfg = plugin_config.weeklyReset
    await reset_help_cmd.finish(
        f"📖 每周重置帮助\n"
        f"━━━━━━━━━━━━━━\n"
        f"⏰ 自动重置时间: 每周{['一','二','三','四','五','六','日'][cfg.resetTime.day-1]} {cfg.resetTime.hour:02d}:{cfg.resetTime.minute:02d}\n\n"
        f"🔄 重置内容:\n"
        f"  • 所有玩家金币归零\n"
        f"  • 清空奴隶和主人关系\n"
        f"  • 身价重置为 {cfg.preserveData.basicValue}\n"
        f"  • 银行数据重置\n"
        f"  • 排位数据重置\n"
        f"  • 保存上周排行榜历史\n\n"
        f"💡 手动重置: #手动奴隶重置 (仅管理员)\n"
        f"━━━━━━━━━━━━━━"
    )


@last_week_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await last_week_cmd.finish("该指令仅群聊可用")

    history = get_last_week_ranking_history(event.group_id)
    if not history:
        await last_week_cmd.finish("暂无上周排行榜数据")

    lines = ["📊 上周排行榜"]
    for i, item in enumerate(history.get("rankings", [])[:15], 1):
        lines.append(f"{i}. {item.get('name', '?')} - {item.get('value', 0)}")

    await last_week_cmd.finish("\n".join(lines))
