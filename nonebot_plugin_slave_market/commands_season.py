"""赛季系统"""
import time
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

from .storage import ensure_player, load_player, save_player, list_group_players
from .utils import get_member_nickname
from .extension.config import ext_config
from .extension.group_storage import (
    ensure_group_data, get_season_ranking, get_season_history,
    get_current_season_str, record_season_stat
)
from .extension.utils import add_exp
from .extension.anti_spam import check_cooldown

season_info_cmd = on_command("赛季信息", aliases={"赛季", "当前赛季"}, priority=5, block=True)
season_rank_cmd = on_command("赛季排行", aliases={"赛季排名", "赛季排行榜"}, priority=5, block=True)
season_reward_cmd = on_command("赛季奖励", priority=5, block=True)
season_history_cmd = on_command("历史赛季", priority=5, block=True)


@season_info_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await season_info_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "season_info")
    if not allowed:
        if msg:
            await season_info_cmd.finish(msg)
        return

    if not ext_config.season.enabled:
        await season_info_cmd.finish("赛季系统已关闭")

    group_id = event.group_id
    gdata = await ensure_group_data(group_id)
    season_key = gdata.get("currentSeason", get_current_season_str())

    await season_info_cmd.finish(
        f"🏆 赛季信息\n"
        f"━━━━━━━━━━━━━━\n"
        f"📅 当前赛季: {season_key}\n"
        f"📊 统计内容: 金币增长、决斗胜场、训练次数、购买次数、身价增长、任务完成\n"
        f"💡 使用 #赛季排行 查看排名\n"
        f"━━━━━━━━━━━━━━"
    )


@season_rank_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await season_rank_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "season_rank")
    if not allowed:
        if msg:
            await season_rank_cmd.finish(msg)
        return

    if not ext_config.season.enabled:
        await season_rank_cmd.finish("赛季系统已关闭")

    group_id = event.group_id
    ranking = await get_season_ranking(group_id)

    if not ranking:
        await season_rank_cmd.finish("暂无赛季数据，先多玩游戏吧！")

    lines = ["🏆 赛季排行榜"]
    for i, item in enumerate(ranking[:15], 1):
        name = await get_member_nickname(bot, group_id, item["user_id"])
        stats = item["stats"]
        lines.append(
            f"{i}. {name} - {item['score']}分\n"
            f"   💰+{stats.get('currencyGrowth',0)} ⚔️{stats.get('duelWins',0)} 🏋️{stats.get('trainCount',0)}"
        )

    await season_rank_cmd.finish("\n".join(lines))


@season_reward_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await season_reward_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "season_reward")
    if not allowed:
        if msg:
            await season_reward_cmd.finish(msg)
        return

    if not ext_config.season.enabled:
        await season_reward_cmd.finish("赛季系统已关闭")

    group_id = event.group_id
    user_id = event.user_id
    nickname = await get_member_nickname(bot, group_id, user_id)
    data = await ensure_player(group_id, user_id, nickname)

    ranking = await get_season_ranking(group_id)
    my_rank = None
    for i, item in enumerate(ranking, 1):
        if item["user_id"] == user_id:
            my_rank = i
            break

    if my_rank is None:
        await season_reward_cmd.finish("你本赛季还没有数据，多玩几个回合再来吧！")

    cfg = ext_config.season
    # 基础奖励
    reward_currency = cfg.rewardCurrency
    reward_exp = cfg.rewardExp

    # 排名加成
    if my_rank <= len(cfg.top3Bonus):
        reward_currency += cfg.top3Bonus[my_rank - 1]
        reward_exp += cfg.top3Bonus[my_rank - 1] // 2

    # 检查是否已领取
    claimed_key = f"season_reward_{gdata.get('currentSeason', '')}"
    if claimed_key in data.get("claimedRewards", []):
        await season_reward_cmd.finish("⏳ 本赛季奖励已领取")

    data["currency"] = data.get("currency", 0) + reward_currency
    leveled_up, new_level, old_level = add_exp(data, reward_exp)
    data.setdefault("claimedRewards", []).append(claimed_key)
    await save_player(group_id, user_id, data)

    level_text = f"\n🆙 等级提升！{old_level} → {new_level}" if leveled_up else ""
    await season_reward_cmd.finish(
        f"🎉 {nickname} 领取赛季奖励！\n"
        f"━━━━━━━━━━━━━━\n"
        f"🏆 赛季排名: 第{my_rank}名\n"
        f"💰 金币 +{reward_currency}\n"
        f"⭐ 经验 +{reward_exp}{level_text}\n"
        f"━━━━━━━━━━━━━━"
    )


@season_history_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await season_history_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "season_history")
    if not allowed:
        if msg:
            await season_history_cmd.finish(msg)
        return

    if not ext_config.season.enabled:
        await season_history_cmd.finish("赛季系统已关闭")

    group_id = event.group_id
    history = await get_season_history(group_id)

    if not history:
        await season_history_cmd.finish("暂无历史赛季记录")

    lines = ["📜 历史赛季记录"]
    for season_key, stats in list(history.items())[-5:]:
        lines.append(f"\n📅 {season_key}:")
        # 找最高分
        best = None
        best_score = -1
        for uid, s in stats.items():
            score = (
                s.get("currencyGrowth", 0) * 0.3 +
                s.get("duelWins", 0) * 50 +
                s.get("trainCount", 0) * 10 +
                s.get("purchaseCount", 0) * 20 +
                s.get("valueGrowth", 0) * 0.5 +
                s.get("taskCompleted", 0) * 30
            )
            if score > best_score:
                best_score = score
                best = (uid, s)
        if best:
            name = await get_member_nickname(bot, group_id, int(best[0]))
            lines.append(f"  冠军: {name} ({int(best_score)}分)")

    await season_history_cmd.finish("\n".join(lines))
