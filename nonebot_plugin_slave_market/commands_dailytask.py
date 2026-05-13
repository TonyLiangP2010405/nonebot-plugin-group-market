"""每日任务系统"""
import time
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.params import CommandArg

from .storage import ensure_player, save_player
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.utils import get_today_str, add_exp, generate_daily_tasks

daily_task_cmd = on_command("每日任务", aliases={"任务", "我的任务"}, priority=5, block=True)
claim_task_reward_cmd = on_command("领取任务奖励", aliases={"领取每日奖励"}, priority=5, block=True)
refresh_task_cmd = on_command("刷新任务", priority=5, block=True)


async def ensure_daily_tasks(data: dict):
    """确保每日任务已生成"""
    today = get_today_str()
    if data.get("dailyTaskDate") != today:
        data["dailyTasks"] = generate_daily_tasks()
        data["dailyTaskDate"] = today
        data["dailyTaskProgress"] = {}


@daily_task_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await daily_task_cmd.finish("该指令仅群聊可用")

    if not ext_config.dailyTask.enabled:
        await daily_task_cmd.finish("每日任务系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)
    await ensure_daily_tasks(data)

    tasks = data.get("dailyTasks", [])
    if not tasks:
        await daily_task_cmd.finish("今天没有任务，试试 #刷新任务")

    lines = [f"📋 {nickname} 的每日任务"]
    completed_count = 0
    for i, task in enumerate(tasks, 1):
        status = "✅" if task.get("completed") else "⬜"
        if task.get("completed"):
            completed_count += 1
        lines.append(
            f"{status} {i}. {task['desc']} "
            f"({task['progress']}/{task['target']}) "
            f"奖励: {task['rewardCurrency']}金币 + {task['rewardExp']}经验"
        )

    lines.append(f"\n进度: {completed_count}/{len(tasks)}")
    lines.append("提示: 完成任务后输入 #领取任务奖励")

    await save_player(group_id, user_id, data)
    await daily_task_cmd.finish("\n".join(lines))


@claim_task_reward_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await claim_task_reward_cmd.finish("该指令仅群聊可用")

    if not ext_config.dailyTask.enabled:
        await claim_task_reward_cmd.finish("每日任务系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)
    await ensure_daily_tasks(data)

    tasks = data.get("dailyTasks", [])
    total_gold = 0
    total_exp = 0
    any_claimed = False

    for task in tasks:
        if task.get("completed") and not task.get("rewarded"):
            total_gold += task["rewardCurrency"]
            total_exp += task["rewardExp"]
            task["rewarded"] = True
            any_claimed = True

    if not any_claimed:
        await claim_task_reward_cmd.finish("没有可领取的任务奖励，请先完成任务。")

    data["currency"] = data.get("currency", 0) + total_gold
    data["totalTasksCompleted"] = data.get("totalTasksCompleted", 0) + sum(1 for t in tasks if t.get("rewarded"))
    leveled_up, new_level, old_level = add_exp(data, total_exp)

    await save_player(group_id, user_id, data)

    level_text = f"\n🆙 等级提升！{old_level} → {new_level}" if leveled_up else ""
    await claim_task_reward_cmd.finish(
        f"✅ {nickname} 领取任务奖励成功！\n"
        f"💰 金币 +{total_gold}\n"
        f"⭐ 经验 +{total_exp}{level_text}"
    )


@refresh_task_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await refresh_task_cmd.finish("该指令仅群聊可用")

    if not ext_config.dailyTask.enabled:
        await refresh_task_cmd.finish("每日任务系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    cfg = ext_config.dailyTask
    if data.get("currency", 0) < cfg.refreshCost:
        await refresh_task_cmd.finish(f"💰 金币不足！刷新任务需要 {cfg.refreshCost} 金币")

    # 检查是否有免费刷新券
    if data.get("inventory", {}).get("task_refresh", 0) > 0:
        from .extension.utils import consume_item
        consume_item(data, "task_refresh")
    else:
        data["currency"] -= cfg.refreshCost

    data["dailyTasks"] = generate_daily_tasks()
    data["dailyTaskDate"] = get_today_str()
    data["dailyTaskProgress"] = {}

    await save_player(group_id, user_id, data)
    await refresh_task_cmd.finish("🔄 任务已刷新！输入 #每日任务 查看新任务。")
