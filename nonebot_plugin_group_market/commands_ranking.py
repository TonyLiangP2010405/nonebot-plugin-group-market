"""排位赛指令"""
import random
import time
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg

from .config import plugin_config
from .storage import load_player, save_player, list_group_players
from .utils import get_member_nickname, check_permission
from .extension.config import ext_config
from .extension.utils import give_exp_and_track
from .extension.group_storage import record_season_stat
from .extension.anti_spam import check_cooldown

ranking_info_cmd = on_command("排位赛", priority=5, block=True)
ranking_join_cmd = on_command("参加排位赛", aliases={"参加排位"}, priority=5, block=True)

OPPONENTS = [
    {"name": "街头混混", "power": 100, "reward": 10},
    {"name": "地下拳手", "power": 300, "reward": 30},
    {"name": "黑帮老大", "power": 600, "reward": 50},
    {"name": "武术冠军", "power": 1000, "reward": 80},
    {"name": "神秘高手", "power": 1500, "reward": 120},
    {"name": "格斗宗师", "power": 2000, "reward": 160},
    {"name": "传说斗士", "power": 3000, "reward": 220},
    {"name": "至尊王者", "power": 5000, "reward": 350},
]

EVENTS = [
    {"name": "状态神勇", "effect": "win_rate+20%", "weight": 1},
    {"name": "突然腹泻", "effect": "win_rate-20%", "weight": 1},
    {"name": "裁判偏袒", "effect": "win_rate+10%", "weight": 2},
    {"name": "观众干扰", "effect": "win_rate-10%", "weight": 2},
    {"name": "正常发挥", "effect": "none", "weight": 4},
]


def get_tier(score: int) -> str:
    if score < 1000:
        return "青铜"
    if score < 1400:
        return "白银"
    if score < 1800:
        return "黄金"
    if score < 2200:
        return "铂金"
    return "钻石"


@ranking_info_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await ranking_info_cmd.finish("该指令仅群聊可用")

    group_id = event.group_id
    players = await list_group_players(group_id)

    lines = ["🏆 排位赛排行榜"]
    items = []
    for pid in players:
        pdata = await load_player(group_id, pid)
        if pdata and pdata.get("ranking"):
            r = pdata["ranking"]
            pname = await get_member_nickname(bot, group_id, pid)
            items.append({
                "name": pname,
                "score": r.get("score", 1000),
                "tier": r.get("tier", "青铜"),
                "matches": r.get("matches", 0)
            })

    items.sort(key=lambda x: x["score"], reverse=True)
    for i, item in enumerate(items[:15], 1):
        lines.append(f"{i}. {item['name']} - {item['tier']} ({item['score']}分, {item['matches']}场)")

    await ranking_info_cmd.finish("\n".join(lines) if len(lines) > 1 else "暂无排位数据")


@ranking_join_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent, args=CommandArg()):
    if not isinstance(event, GroupMessageEvent):
        await ranking_join_cmd.finish("该指令仅群聊可用")

    allowed, msg = check_cooldown(event, "ranking_join")
    if not allowed:
        if msg:
            await ranking_join_cmd.finish(msg)
        return

    group_id = event.group_id
    user_id = event.user_id

    user_data = await load_player(group_id, user_id)
    if not user_data:
        await ranking_join_cmd.finish("你还没有参与游戏")

    # 解析 @ 目标奴隶
    target_id = None
    for seg in event.message:
        if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
            target_id = int(seg.data["qq"])
            break

    if target_id is None:
        text = args.extract_plain_text().strip()
        if text.isdigit():
            target_id = int(text)

    if target_id is None:
        await ranking_join_cmd.finish("请 @ 要参加排位赛的奴隶")

    if target_id not in user_data.get("slave", []):
        await ranking_join_cmd.finish("该用户不是你的奴隶")

    now = int(time.time())
    cfg = plugin_config.ranking

    if not check_permission(event):
        remaining = cfg.cooldown - (now - user_data.get("lastRankingTime", 0))
        if remaining > 0:
            h = remaining // 3600
            m = (remaining % 3600) // 60
            await ranking_join_cmd.finish(f"⏳ 排位赛冷却中...\n剩余: {h}小时{m}分钟")

    slave_data = await load_player(group_id, target_id)
    if not slave_data:
        await ranking_join_cmd.finish("奴隶数据不存在")

    sname = await get_member_nickname(bot, group_id, target_id)

    # 选择对手
    opp = random.choice(OPPONENTS)
    event_item = random.choice(EVENTS)

    # 基础胜率 50%
    win_rate = 0.5 + (slave_data["value"] - opp["power"]) / max(slave_data["value"] + opp["power"], 1) * 0.4
    win_rate = max(0.1, min(0.9, win_rate))

    if event_item["effect"] == "win_rate+20%":
        win_rate = min(0.95, win_rate + 0.2)
    elif event_item["effect"] == "win_rate-20%":
        win_rate = max(0.05, win_rate - 0.2)
    elif event_item["effect"] == "win_rate+10%":
        win_rate = min(0.95, win_rate + 0.1)
    elif event_item["effect"] == "win_rate-10%":
        win_rate = max(0.05, win_rate - 0.1)

    ranking = slave_data.setdefault("ranking", {"score": 1000, "tier": "青铜", "matches": 0})

    is_win = random.random() < win_rate
    if is_win:
        # 胜利
        tier_bonus = cfg.tierBonus.get(ranking["tier"], 1)
        reward = int(cfg.baseReward * tier_bonus + cfg.winBonus * slave_data["value"])
        score_change = random.randint(15, 35)
        ranking["score"] += score_change
        user_data["currency"] += reward
        result_text = f"🏆 胜利！\n击败: {opp['name']}\n事件: {event_item['name']}\n得分 +{score_change}\n金币 +{reward}"
    else:
        # 失败
        score_change = random.randint(10, 25)
        ranking["score"] = max(0, ranking["score"] - score_change)
        reward = 0
        result_text = f"😢 失败...\n对手: {opp['name']}\n事件: {event_item['name']}\n得分 -{score_change}"

    ranking["tier"] = get_tier(ranking["score"])
    ranking["matches"] = ranking.get("matches", 0) + 1
    user_data["lastRankingTime"] = now

    # 扩展追踪
    if ext_config.level.enabled:
        from .extension.utils import add_exp
        exp_gain = ext_config.level.rankingExp if is_win else ext_config.level.rankingExp // 2
        add_exp(user_data, exp_gain)
    give_exp_and_track(user_data, 0, "ranking_join")
    await record_season_stat(group_id, user_id, "currencyGrowth", reward)

    await save_player(group_id, target_id, slave_data)
    await save_player(group_id, user_id, user_data)

    reply = (
        f"⚔️ {sname} 的排位赛\n"
        f"{result_text}\n"
        f"📊 当前段位: {ranking['tier']} ({ranking['score']}分)"
    )

    # BOT 陪玩触发
    try:
        from .bot_actions import try_bot_auto_action
        bot_msg = await try_bot_auto_action(bot, group_id, user_id, "ranking_join")
        if bot_msg:
            reply += "\n\n" + bot_msg
    except Exception:
        pass

    await ranking_join_cmd.finish(reply)
