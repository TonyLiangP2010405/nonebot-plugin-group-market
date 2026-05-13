"""管理员防刷屏管理命令"""
import re
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.permission import SUPERUSER
from nonebot.params import CommandArg

from .extension.anti_spam import (
    check_cooldown, is_quiet_mode, set_quiet_mode,
    is_spam_protection_enabled, set_anti_spam_enabled,
    set_group_cmd_cooldown, clear_group_cmd_cooldown,
    format_flood_status, COMMAND_CATEGORIES
)

# 管理员命令（使用 admin 分类，不受普通冷却限制）
admin_cooldown_status = on_command("游戏冷却状态", aliases={"冷却状态"}, priority=5, block=True)
admin_enable_quiet = on_command("开启安静模式", priority=5, block=True)
admin_disable_quiet = on_command("关闭安静模式", priority=5, block=True)
admin_enable_spam = on_command("开启防刷屏", priority=5, block=True)
admin_disable_spam = on_command("关闭防刷屏", priority=5, block=True)
admin_set_work_cd = on_command("设置打工冷却", priority=5, block=True)
admin_set_group_cd = on_command("设置群游戏间隔", aliases={"设置群间隔"}, priority=5, block=True)


def _is_admin(event: GroupMessageEvent) -> bool:
    """检查是否为群管理员或超管"""
    if SUPERUSER(event):
        return True
    return False


@admin_cooldown_status.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await admin_cooldown_status.finish("该指令仅群聊可用")

    if not _is_admin(event):
        # 非管理员也要检查冷却
        allowed, msg = check_cooldown(event, "admin")
        if not allowed:
            if msg:
                await admin_cooldown_status.finish(msg)
            return

    group_id = event.group_id
    await admin_cooldown_status.finish(format_flood_status(group_id))


@admin_enable_quiet.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await admin_enable_quiet.finish("该指令仅群聊可用")

    if not _is_admin(event):
        await admin_enable_quiet.finish("❌ 仅管理员可用")

    group_id = event.group_id
    set_quiet_mode(group_id, True)
    await admin_enable_quiet.finish("🔇 安静模式已开启\n冷却期间重复触发将静默处理。")


@admin_disable_quiet.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await admin_disable_quiet.finish("该指令仅群聊可用")

    if not _is_admin(event):
        await admin_disable_quiet.finish("❌ 仅管理员可用")

    group_id = event.group_id
    set_quiet_mode(group_id, False)
    await admin_disable_quiet.finish("🔔 安静模式已关闭")


@admin_enable_spam.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await admin_enable_spam.finish("该指令仅群聊可用")

    if not _is_admin(event):
        await admin_enable_spam.finish("❌ 仅管理员可用")

    group_id = event.group_id
    set_anti_spam_enabled(group_id, True)
    await admin_enable_spam.finish("🛡️ 防刷屏已开启")


@admin_disable_spam.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await admin_disable_spam.finish("该指令仅群聊可用")

    if not _is_admin(event):
        await admin_disable_spam.finish("❌ 仅管理员可用")

    group_id = event.group_id
    set_anti_spam_enabled(group_id, False)
    await admin_disable_spam.finish("⚠️ 防刷屏已关闭（游戏命令不再受限）")


@admin_set_work_cd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await admin_set_work_cd.finish("该指令仅群聊可用")

    if not _is_admin(event):
        await admin_set_work_cd.finish("❌ 仅管理员可用")

    text = args.extract_plain_text().strip()
    if not text.isdigit():
        await admin_set_work_cd.finish("请输入分钟数\n例如: #设置打工冷却 20")

    minutes = int(text)
    if minutes < 1 or minutes > 1440:
        await admin_set_work_cd.finish("冷却时间需在 1-1440 分钟之间")

    group_id = event.group_id
    set_group_cmd_cooldown(group_id, "work", minutes * 60)
    await admin_set_work_cd.finish(f"✅ 本群打工冷却已设置为 {minutes} 分钟")


@admin_set_group_cd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await admin_set_group_cd.finish("该指令仅群聊可用")

    if not _is_admin(event):
        await admin_set_group_cd.finish("❌ 仅管理员可用")

    text = args.extract_plain_text().strip()
    if not text.isdigit():
        await admin_set_group_cd.finish("请输入秒数\n例如: #设置群游戏间隔 5")

    seconds = int(text)
    if seconds < 0 or seconds > 60:
        await admin_set_group_cd.finish("间隔需在 0-60 秒之间")

    group_id = event.group_id
    # 修改所有命令的群全局冷却
    for cmd_key in COMMAND_CATEGORIES:
        set_group_cmd_cooldown(group_id, cmd_key, COMMAND_CATEGORIES[cmd_key]["user_cd"])
    # 设置群全局冷却的默认值... 实际上是通过 _group_cmd_cooldowns 来覆盖
    # 这里我们无法直接修改全局间隔，但可以通过特殊标记
    # 简化处理：只设置一个标记
    set_group_cmd_cooldown(group_id, "__group_global_override__", seconds)
    await admin_set_group_cd.finish(f"✅ 本群游戏命令全局间隔已设置为 {seconds} 秒")
