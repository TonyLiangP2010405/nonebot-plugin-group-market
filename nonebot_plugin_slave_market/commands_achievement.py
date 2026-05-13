"""成就系统"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .storage import ensure_player, load_player, save_player, list_group_players
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.utils import check_achievement_unlock, apply_achievement_rewards

achievement_cmd = on_command("我的成就", aliases={"成就", "成就列表"}, priority=5, block=True)
achievement_rank_cmd = on_command("成就排行", priority=5, block=True)

# 成就定义
ACHIEVEMENTS_DEF = {
    "first_work": {"name": "初次打工", "desc": "第一次打工", "check": lambda d: d.get("workCount", 0) >= 1},
    "work_10": {"name": "勤劳小蜜蜂", "desc": "累计打工10次", "check": lambda d: d.get("workCount", 0) >= 10},
    "work_50": {"name": "打工皇帝", "desc": "累计打工50次", "check": lambda d: d.get("workCount", 0) >= 50},
    "work_100": {"name": "永动机", "desc": "累计打工100次", "check": lambda d: d.get("workCount", 0) >= 100},
    "first_purchase": {"name": "初次购买", "desc": "第一次购买群友", "check": lambda d: d.get("purchaseCount", 0) >= 1},
    "purchase_10": {"name": "收藏家", "desc": "累计购买10次", "check": lambda d: d.get("purchaseCount", 0) >= 10},
    "first_master": {"name": "成为主人", "desc": "第一次拥有奴隶", "check": lambda d: len(d.get("slave", [])) >= 1},
    "first_bought": {"name": "被买下", "desc": "第一次被购买", "check": lambda d: bool(d.get("master", ""))},
    "train_10": {"name": "训练大师", "desc": "累计训练成功10次", "check": lambda d: d.get("trainSuccessCount", 0) >= 10},
    "arena_win_10": {"name": "决斗王者", "desc": "累计决斗胜利10次", "check": lambda d: d.get("duelStats", {}).get("wins", 0) >= 10},
    "bank_10000": {"name": "理财达人", "desc": "银行存款达到10000", "check": lambda d: d.get("bank", {}).get("balance", 0) >= 10000},
    "value_1000": {"name": "身价过千", "desc": "身价达到1000", "check": lambda d: d.get("value", 100) >= 1000},
    "value_5000": {"name": "身价过万", "desc": "身价达到5000", "check": lambda d: d.get("value", 100) >= 5000},
    "signin_7": {"name": "早起鸟儿", "desc": "连续签到7天", "check": lambda d: d.get("continuousSignInDays", 0) >= 7},
    "signin_30": {"name": "持之以恒", "desc": "连续签到30天", "check": lambda d: d.get("continuousSignInDays", 0) >= 30},
    "level_10": {"name": "初露锋芒", "desc": "等级达到10级", "check": lambda d: d.get("level", 1) >= 10},
    "level_20": {"name": "一代宗师", "desc": "等级达到20级", "check": lambda d: d.get("level", 1) >= 20},
    "level_50": {"name": "传说", "desc": "等级达到50级", "check": lambda d: d.get("level", 1) >= 50},
    "slave_5": {"name": "奴隶收藏家", "desc": "同时拥有5名奴隶", "check": lambda d: len(d.get("slave", [])) >= 5},
    "task_50": {"name": "任务达人", "desc": "累计完成50个每日任务", "check": lambda d: d.get("totalTasksCompleted", 0) >= 50},
}


def check_all_achievements(data: dict) -> list:
    """检查所有成就，返回新解锁的成就ID列表"""
    newly = []
    for ach_id, ach_def in ACHIEVEMENTS_DEF.items():
        if check_achievement_unlock(data, ach_id, ach_def["check"]):
            newly.append(ach_id)
    return newly


@achievement_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await achievement_cmd.finish("该指令仅群聊可用")

    if not ext_config.achievement.enabled:
        await achievement_cmd.finish("成就系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    # 检查新成就
    newly = check_all_achievements(data)
    if newly:
        apply_achievement_rewards(data)
        await save_player(group_id, user_id, data)

    achieved = set(data.get("achievements", []))

    lines = [f"🏅 {nickname} 的成就"]
    if newly:
        lines.append(f"🎉 新解锁 {len(newly)} 个成就！")

    unlocked = []
    locked = []
    for ach_id, ach_def in ACHIEVEMENTS_DEF.items():
        status = "✅" if ach_id in achieved else "❌"
        line = f"{status} {ach_def['name']} - {ach_def['desc']}"
        if ach_id in achieved:
            unlocked.append(line)
        else:
            locked.append(line)

    lines.append(f"\n已解锁 ({len(unlocked)}/{len(ACHIEVEMENTS_DEF)}):")
    lines.extend(unlocked[:10])
    if len(unlocked) > 10:
        lines.append(f"... 还有 {len(unlocked) - 10} 个")

    if locked:
        lines.append(f"\n未解锁:")
        lines.extend(locked[:5])

    await achievement_cmd.finish("\n".join(lines))


@achievement_rank_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await achievement_rank_cmd.finish("该指令仅群聊可用")

    if not ext_config.achievement.enabled:
        await achievement_rank_cmd.finish("成就系统已关闭")

    group_id = event.group_id
    players = await list_group_players(group_id)

    items = []
    for pid in players:
        pdata = await load_player(group_id, pid)
        if pdata:
            count = len(pdata.get("achievements", []))
            items.append({
                "name": await get_member_nickname(bot, group_id, pid),
                "count": count,
            })

    if not items:
        await achievement_rank_cmd.finish("暂无成就数据")

    items.sort(key=lambda x: x["count"], reverse=True)

    lines = ["🏅 成就排行榜"]
    for i, item in enumerate(items[:15], 1):
        lines.append(f"{i}. {item['name']} - {item['count']} 个成就")

    await achievement_rank_cmd.finish("\n".join(lines))
