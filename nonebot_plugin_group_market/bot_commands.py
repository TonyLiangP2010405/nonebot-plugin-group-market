"""BOT 陪玩命令集 - /开启陪玩 /关闭陪玩 /陪玩状态 /召唤陪玩 /陪玩设置 /重置陪玩"""
import time
import random
from nonebot import on_command, logger, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

from .bot_storage import (
    ensure_bot, save_bot, list_group_bots, delete_bot, reset_bot,
    is_bot_play_enabled, set_bot_play_enabled,
    get_bot_group_settings, set_bot_group_setting,
    BOT_ID_PREFIX, generate_bot_id,
    can_bot_act, get_bot_daily_action_count,
    is_bot_action_cooled, is_bot_summon_cooled,
)
from .bot_strategy import get_all_strategies, get_strategy_name
from .bot_actions import summon_bot_action, try_bot_auto_action
from .storage import list_group_players


# ========== 权限检查 ==========

def _is_admin_or_superuser(event: GroupMessageEvent) -> bool:
    """检查是否为管理员/群主/SUPERUSER"""
    # 优先检查 SUPERUSER
    if str(event.user_id) in get_driver().config.superusers:
        return True
    # 如果适配器支持，检查群角色
    try:
        role = getattr(event.sender, "role", None)
        if role in ("owner", "admin"):
            return True
    except Exception:
        pass
    return False


# ========== 命令定义 ==========

bot_enable_cmd = on_command("开启陪玩", aliases={"启用陪玩", "打开陪玩"}, priority=5, block=True)
bot_disable_cmd = on_command("关闭陪玩", aliases={"停用陪玩", "关闭陪玩"}, priority=5, block=True)
bot_status_cmd = on_command("陪玩状态", aliases={"bot状态", "bot信息"}, priority=5, block=True)
bot_summon_cmd = on_command("召唤陪玩", aliases={"召唤bot", "叫陪玩"}, priority=5, block=True)
bot_settings_cmd = on_command("陪玩设置", aliases={"bot设置"}, priority=5, block=True)
bot_reset_cmd = on_command("重置陪玩", aliases={"重置bot", "重置陪玩数据"}, priority=5, block=True)


# ========== 开启陪玩 ==========

@bot_enable_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await bot_enable_cmd.finish("该指令仅群聊可用")

    if not _is_admin_or_superuser(event):
        await bot_enable_cmd.finish("❌ 仅群管理员/SUPERUSER 可开启 BOT 陪玩")

    group_id = event.group_id

    # 检查是否已有 BOT
    bot_ids = await list_group_bots(group_id)
    if not bot_ids:
        # 创建新 BOT
        bot_id = generate_bot_id(group_id, 0)
        settings = get_bot_group_settings(group_id)
        strategy = settings.get("strategy", "random")
        if strategy == "random":
            from .bot_strategy import random_strategy
            strategy = random_strategy()
        bot_data = await ensure_bot(group_id, bot_id, strategy=strategy)
        bot_ids = [bot_id]
    else:
        bot_id = bot_ids[0]
        bot_data = await ensure_bot(group_id, bot_id)
        strategy = bot_data.get("strategy", "random")

    set_bot_play_enabled(group_id, True)
    await bot_enable_cmd.finish(
        f"✅ 本群 BOT 陪玩已开启！\n"
        f"🤖 BOT：{bot_data.get('nickname', '未知')}\n"
        f"🎯 策略：{get_strategy_name(strategy)}\n"
        f"💡 玩家执行游戏命令后，BOT 有概率自动响应。\n"
        f"发送 /陪玩状态 查看详情，/召唤陪玩 手动触发一次行动。"
    )


# ========== 关闭陪玩 ==========

@bot_disable_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await bot_disable_cmd.finish("该指令仅群聊可用")

    if not _is_admin_or_superuser(event):
        await bot_disable_cmd.finish("❌ 仅群管理员/SUPERUSER 可关闭 BOT 陪玩")

    group_id = event.group_id
    set_bot_play_enabled(group_id, False)
    await bot_disable_cmd.finish("🔕 本群 BOT 陪玩已关闭。\nBOT 将不再自动行动。")


# ========== 陪玩状态 ==========

@bot_status_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await bot_status_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    enabled = is_bot_play_enabled(group_id)

    if not enabled:
        await bot_status_cmd.finish(
            "🤖 BOT 陪玩状态\n"
            "━━━━━━━━━━━━━━\n"
            "状态：❌ 未开启\n"
            "━━━━━━━━━━━━━━\n"
            "群管理员可发送 /开启陪玩 开启"
        )

    bot_ids = await list_group_bots(group_id)
    if not bot_ids:
        await bot_status_cmd.finish("⚠️ BOT 数据异常，请尝试 /重置陪玩")

    bot_id = bot_ids[0]
    bot_data = await ensure_bot(group_id, bot_id)
    settings = get_bot_group_settings(group_id)

    strategy_key = bot_data.get("strategy", settings.get("strategy", "random"))
    strategy_name = get_strategy_name(strategy_key)

    daily_count = get_bot_daily_action_count(group_id, bot_id)
    daily_limit = settings.get("daily_action_limit", 20)
    action_cooldown = settings.get("action_cooldown", 600)
    action_prob = settings.get("action_probability", 0.15)

    lines = [
        "🤖 BOT 陪玩状态",
        "━━━━━━━━━━━━━━",
        f"状态：✅ 已开启",
        f"名称：{bot_data.get('nickname', '未知')}",
        f"策略：{strategy_name}",
        f"等级：{bot_data.get('level', 1)}",
        f"身价：{bot_data.get('value', 100)} 金币",
        f"资产：{bot_data.get('currency', 0)} 金币",
        f"持有群友：{len(bot_data.get('slave', []))} 人",
        f"今日行动：{daily_count}/{daily_limit} 次",
        f"行动概率：{int(action_prob * 100)}%",
        f"行动冷却：{action_cooldown // 60} 分钟",
        f"主动挑战：{'✅ 允许' if settings.get('allow_attack') else '❌ 关闭'}",
        f"购买群友：{'✅ 允许' if settings.get('allow_buy_from_players') else '❌ 关闭'}",
        f"消息模式：{settings.get('message_mode', 'simple')}",
        "━━━━━━━━━━━━━━",
        "💡 /召唤陪玩 手动触发 | /陪玩设置 调整参数",
    ]

    await bot_status_cmd.finish("\n".join(lines))


# ========== 召唤陪玩 ==========

@bot_summon_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await bot_summon_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id

    if not is_bot_play_enabled(group_id):
        await bot_summon_cmd.finish("❌ 本群 BOT 陪玩未开启，群管理员可发送 /开启陪玩 开启")

    bot_ids = await list_group_bots(group_id)
    if not bot_ids:
        await bot_summon_cmd.finish("⚠️ BOT 不存在，请先 /开启陪玩")

    bot_id = bot_ids[0]

    # 检查召唤冷却
    if not is_bot_summon_cooled(group_id, bot_id):
        await bot_summon_cmd.finish("⏳ BOT 召唤冷却中，请稍后再试")

    result = await summon_bot_action(bot, group_id, bot_id)
    if result:
        await bot_summon_cmd.finish(result)
    else:
        await bot_summon_cmd.finish("🤖 BOT 正在忙，稍后再试吧")


# ========== 陪玩设置 ==========

@bot_settings_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await bot_settings_cmd.finish("该指令仅群聊可用")

    if not _is_admin_or_superuser(event):
        await bot_settings_cmd.finish("❌ 仅群管理员/SUPERUSER 可调整 BOT 设置")

    group_id = event.group_id
    text = args.extract_plain_text().strip()
    settings = get_bot_group_settings(group_id)

    # 如果没有参数，显示当前设置和帮助
    if not text:
        lines = [
            "⚙️ BOT 陪玩设置",
            "━━━━━━━━━━━━━━",
            f"行动概率：{int(settings.get('action_probability', 0.15) * 100)}%",
            f"行动冷却：{settings.get('action_cooldown', 600) // 60} 分钟",
            f"每日上限：{settings.get('daily_action_limit', 20)} 次",
            f"召唤冷却：{settings.get('summon_cooldown', 1800) // 60} 分钟",
            f"主动挑战：{'开启' if settings.get('allow_attack') else '关闭'}",
            f"购买群友：{'开启' if settings.get('allow_buy_from_players') else '关闭'}",
            f"消息模式：{settings.get('message_mode', 'simple')}",
            f"BOT策略：{get_strategy_name(settings.get('strategy', 'random'))}",
            "━━━━━━━━━━━━━━",
            "修改方式：/陪玩设置 参数名 值",
            "",
            "可设置参数：",
            "  概率 [0-100] - 行动触发概率(%)",
            "  冷却 [1-60] - 行动冷却(分钟)",
            "  上限 [1-100] - 每日最大行动次数",
            "  召唤 [1-60] - 召唤冷却(分钟)",
            "  挑战 开/关 - 是否允许主动挑战",
            "  购买 开/关 - 是否允许购买群友",
            "  消息 简洁/详细 - 消息显示模式",
            "  策略 保守/资本/好战/记仇/随机",
        ]
        await bot_settings_cmd.finish("\n".join(lines))
        return

    # 解析参数
    parts = text.split(maxsplit=1)
    if len(parts) < 1:
        await bot_settings_cmd.finish("参数格式错误，请发送 /陪玩设置 查看帮助")

    param = parts[0].lower()
    value = parts[1] if len(parts) > 1 else ""

    # 参数映射
    if param in ("概率", "prob", "probability"):
        try:
            v = int(value)
            if v < 0 or v > 100:
                await bot_settings_cmd.finish("概率范围: 0-100")
            set_bot_group_setting(group_id, "action_probability", v / 100)
            await bot_settings_cmd.finish(f"✅ BOT 行动概率已设置为 {v}%")
        except ValueError:
            await bot_settings_cmd.finish("请输入数字，例如: /陪玩设置 概率 15")

    elif param in ("冷却", "cd", "cooldown"):
        try:
            v = int(value)
            if v < 1 or v > 60:
                await bot_settings_cmd.finish("冷却范围: 1-60 分钟")
            set_bot_group_setting(group_id, "action_cooldown", v * 60)
            await bot_settings_cmd.finish(f"✅ BOT 行动冷却已设置为 {v} 分钟")
        except ValueError:
            await bot_settings_cmd.finish("请输入数字，例如: /陪玩设置 冷却 10")

    elif param in ("上限", "limit", "daily"):
        try:
            v = int(value)
            if v < 1 or v > 100:
                await bot_settings_cmd.finish("上限范围: 1-100")
            set_bot_group_setting(group_id, "daily_action_limit", v)
            await bot_settings_cmd.finish(f"✅ BOT 每日行动上限已设置为 {v} 次")
        except ValueError:
            await bot_settings_cmd.finish("请输入数字，例如: /陪玩设置 上限 20")

    elif param in ("召唤", "summon"):
        try:
            v = int(value)
            if v < 1 or v > 60:
                await bot_settings_cmd.finish("召唤冷却范围: 1-60 分钟")
            set_bot_group_setting(group_id, "summon_cooldown", v * 60)
            await bot_settings_cmd.finish(f"✅ BOT 召唤冷却已设置为 {v} 分钟")
        except ValueError:
            await bot_settings_cmd.finish("请输入数字，例如: /陪玩设置 召唤 30")

    elif param in ("挑战", "attack", "duel"):
        if value in ("开", "开启", "true", "1", "on"):
            set_bot_group_setting(group_id, "allow_attack", True)
            await bot_settings_cmd.finish("✅ BOT 主动挑战已开启")
        elif value in ("关", "关闭", "false", "0", "off"):
            set_bot_group_setting(group_id, "allow_attack", False)
            await bot_settings_cmd.finish("✅ BOT 主动挑战已关闭")
        else:
            await bot_settings_cmd.finish("请输入 开 或 关")

    elif param in ("购买", "buy"):
        if value in ("开", "开启", "true", "1", "on"):
            set_bot_group_setting(group_id, "allow_buy_from_players", True)
            await bot_settings_cmd.finish("✅ BOT 购买群友已开启")
        elif value in ("关", "关闭", "false", "0", "off"):
            set_bot_group_setting(group_id, "allow_buy_from_players", False)
            await bot_settings_cmd.finish("✅ BOT 购买群友已关闭")
        else:
            await bot_settings_cmd.finish("请输入 开 或 关")

    elif param in ("消息", "message", "mode"):
        if value in ("简洁", "简单", "simple"):
            set_bot_group_setting(group_id, "message_mode", "simple")
            await bot_settings_cmd.finish("✅ BOT 消息模式已设为 简洁")
        elif value in ("详细", "detail", "verbose"):
            set_bot_group_setting(group_id, "message_mode", "detail")
            await bot_settings_cmd.finish("✅ BOT 消息模式已设为 详细")
        else:
            await bot_settings_cmd.finish("请输入 简洁 或 详细")

    elif param in ("策略", "strategy", "type"):
        strategy_map = {
            "保守": "conservative", "conservative": "conservative",
            "资本": "capitalist", "capitalist": "capitalist",
            "好战": "aggressive", "aggressive": "aggressive",
            "记仇": "vengeful", "vengeful": "vengeful",
            "随机": "random", "random": "random",
        }
        skey = strategy_map.get(value)
        if not skey:
            await bot_settings_cmd.finish("策略可选: 保守/资本/好战/记仇/随机")
        set_bot_group_setting(group_id, "strategy", skey)
        # 同时更新 BOT 数据中的策略
        bot_ids = await list_group_bots(group_id)
        if bot_ids:
            bot_data = await ensure_bot(group_id, bot_ids[0])
            bot_data["strategy"] = skey
            await save_bot(group_id, bot_ids[0], bot_data)
        await bot_settings_cmd.finish(f"✅ BOT 策略已设为 {get_strategy_name(skey)}")

    else:
        await bot_settings_cmd.finish(f"未知参数: {param}\n发送 /陪玩设置 查看帮助")


# ========== 重置陪玩 ==========

@bot_reset_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await bot_reset_cmd.finish("该指令仅群聊可用")

    if not _is_admin_or_superuser(event):
        await bot_reset_cmd.finish("❌ 仅群管理员/SUPERUSER 可重置 BOT 陪玩")

    group_id = event.group_id
    text = args.extract_plain_text().strip()

    # 如果有"确认"才执行
    if text != "确认":
        await bot_reset_cmd.finish(
            "⚠️ 重置将清空本群 BOT 的所有数据（金币、奴隶、等级等）\n"
            "数据不可恢复！\n"
            "如果确定，请发送: /重置陪玩 确认"
        )

    # 删除所有 BOT 数据
    bot_ids = await list_group_bots(group_id)
    for bid in bot_ids:
        await delete_bot(group_id, bid)

    # 重新创建
    bot_id = generate_bot_id(group_id, 0)
    settings = get_bot_group_settings(group_id)
    strategy = settings.get("strategy", "random")
    if strategy == "random":
        from .bot_strategy import random_strategy
        strategy = random_strategy()
    bot_data = await ensure_bot(group_id, bot_id, strategy=strategy)

    # 重置开关状态
    set_bot_play_enabled(group_id, False)

    await bot_reset_cmd.finish(
        f"✅ 本群 BOT 陪玩数据已重置！\n"
        f"🤖 新 BOT：{bot_data.get('nickname', '未知')}\n"
        f"🎯 策略：{get_strategy_name(strategy)}\n"
        f"💰 初始资产：{bot_data.get('currency', 0)} 金币\n"
        f"发送 /开启陪玩 重新开启"
    )
