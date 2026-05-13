"""扩展模块通用工具"""
import random
import datetime
from typing import Dict, Optional, List
from nonebot import logger

from .config import ext_config


def get_today_str() -> str:
    """获取今天的日期字符串 YYYY-MM-DD"""
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_current_week_str() -> str:
    """获取当前周标识 YYYY-WW"""
    now = datetime.datetime.now()
    return f"{now.year}-W{now.isocalendar()[1]:02d}"


def get_current_month_str() -> str:
    """获取当前月标识 YYYY-MM"""
    return datetime.datetime.now().strftime("%Y-%m")


def get_current_season_str() -> str:
    cfg = ext_config.season
    if cfg.mode == "monthly":
        return get_current_month_str()
    return get_current_week_str()


def get_level_threshold(level: int) -> int:
    """计算升到下一级所需经验"""
    cfg = ext_config.level
    if level >= cfg.maxLevel:
        return 999999999
    return int(cfg.baseExp * (cfg.expGrowth ** (level - 1)))


def add_exp(data: Dict, amount: int) -> tuple:
    """给玩家增加经验，返回 (是否升级, 新等级, 升级前等级)"""
    if not ext_config.level.enabled:
        return False, data.get("level", 1), data.get("level", 1)

    old_level = data.get("level", 1)
    data["exp"] = data.get("exp", 0) + amount

    while True:
        threshold = get_level_threshold(data["level"])
        if data["exp"] >= threshold and data["level"] < ext_config.level.maxLevel:
            data["exp"] -= threshold
            data["level"] = data.get("level", 1) + 1
        else:
            break

    return data["level"] > old_level, data["level"], old_level


def get_level_bonus(data: Dict, bonus_type: str) -> float:
    """获取等级加成倍数"""
    if not ext_config.level.enabled:
        return 1.0
    level = data.get("level", 1)
    cfg = ext_config.level
    if bonus_type == "work_income":
        return 1.0 + level * cfg.workIncomeBonusPerLevel
    if bonus_type == "bank_limit":
        return 1.0 + level * cfg.bankLimitBonusPerLevel
    if bonus_type == "train_success":
        return level * cfg.trainSuccessBonusPerLevel
    return 1.0


def get_random_event_effect(group_event: Optional[Dict], effect_type: str) -> float:
    """获取当前群随机事件对某玩法的加成"""
    if not group_event:
        return 0.0
    return group_event.get("effect", {}).get(effect_type, 0.0)


def get_work_income_multiplier(data: Dict, group_event: Optional[Dict] = None) -> float:
    """计算打工收益总倍率"""
    mult = 1.0
    # 等级加成
    mult *= get_level_bonus(data, "work_income")
    # 随机事件
    if group_event:
        mult += get_random_event_effect(group_event, "workIncome")
    # 道具加成
    if data.get("inventory", {}).get("work_boost", 0) > 0:
        mult += 0.5
    return mult


def get_train_success_bonus(data: Dict, group_event: Optional[Dict] = None) -> float:
    """训练成功率额外加成"""
    bonus = get_level_bonus(data, "train_success")
    if group_event:
        bonus += get_random_event_effect(group_event, "trainSuccess")
    return bonus


def get_arena_reward_multiplier(data: Dict, group_event: Optional[Dict] = None) -> float:
    """决斗奖励倍率"""
    mult = 1.0
    if group_event:
        mult += get_random_event_effect(group_event, "arenaReward")
    return mult


def consume_item(data: Dict, item_id: str, count: int = 1) -> bool:
    """消耗道具，返回是否成功"""
    inv = data.setdefault("inventory", {})
    if inv.get(item_id, 0) < count:
        return False
    inv[item_id] -= count
    if inv[item_id] <= 0:
        del inv[item_id]
    return True


def give_item(data: Dict, item_id: str, count: int = 1):
    """给予道具"""
    inv = data.setdefault("inventory", {})
    inv[item_id] = inv.get(item_id, 0) + count


def get_item_name(item_id: str) -> str:
    """获取道具名称"""
    for item in ext_config.shop.items:
        if item.get("id") == item_id:
            return item.get("name", item_id)
    return item_id


def get_item_info(item_id: str) -> Optional[Dict]:
    """获取道具配置"""
    for item in ext_config.shop.items:
        if item.get("id") == item_id:
            return item
    return None


def check_achievement_unlock(data: Dict, ach_id: str, condition: callable) -> bool:
    """检查并解锁成就，返回是否新解锁"""
    if not ext_config.achievement.enabled:
        return False
    achieved = data.setdefault("achievements", [])
    if ach_id in achieved:
        return False
    if condition(data):
        achieved.append(ach_id)
        return True
    return False


def apply_achievement_rewards(data: Dict):
    """应用成就奖励（通用金币+经验）"""
    cfg = ext_config.achievement
    data["currency"] = data.get("currency", 0) + cfg.rewardCurrency
    add_exp(data, cfg.rewardExp)


def generate_daily_tasks() -> List[Dict]:
    """生成每日任务列表"""
    cfg = ext_config.dailyTask
    all_task_types = [
        {"type": "work", "desc": "打工3次", "target": 3, "weight": 10},
        {"type": "train", "desc": "训练1次", "target": 1, "weight": 8},
        {"type": "arena", "desc": "发起决斗1次", "target": 1, "weight": 6},
        {"type": "purchase", "desc": "购买1名群友", "target": 1, "weight": 5},
        {"type": "bank_deposit", "desc": "银行存款1次", "target": 1, "weight": 7},
        {"type": "ranking_view", "desc": "查看排行榜1次", "target": 1, "weight": 4},
        {"type": "ranking_join", "desc": "完成一次排位赛", "target": 1, "weight": 5},
    ]
    selected = []
    weights = [t["weight"] for t in all_task_types]
    total = sum(weights)
    rands = random.choices(all_task_types, weights=weights, k=min(cfg.taskCount, len(all_task_types)))
    # 去重
    seen = set()
    for t in rands:
        if t["type"] not in seen:
            seen.add(t["type"])
            reward_currency = random.randint(cfg.rewardCurrencyRange[0], cfg.rewardCurrencyRange[1])
            reward_exp = random.randint(cfg.rewardExpRange[0], cfg.rewardExpRange[1])
            selected.append({
                "type": t["type"],
                "desc": t["desc"],
                "target": t["target"],
                "progress": 0,
                "completed": False,
                "rewardCurrency": reward_currency,
                "rewardExp": reward_exp,
            })
    return selected[:cfg.taskCount]


def random_box_reward() -> Dict:
    """随机宝箱奖励"""
    roll = random.random()
    if roll < 0.5:
        gold = random.randint(50, 150)
        return {"type": "currency", "amount": gold, "text": f"获得 {gold} 金币"}
    elif roll < 0.8:
        exp = random.randint(30, 80)
        return {"type": "exp", "amount": exp, "text": f"获得 {exp} 经验"}
    else:
        item_pool = ["work_boost", "train_protect", "arena_shield", "task_refresh"]
        item = random.choice(item_pool)
        return {"type": "item", "itemId": item, "amount": 1, "text": f"获得 {get_item_name(item)} x1"}


def get_title_info(title_id: str) -> Optional[Dict]:
    """获取称号配置"""
    for t in ext_config.title.titles:
        if t.get("id") == title_id:
            return t
    return None


def format_level_bar(exp: int, threshold: int, width: int = 10) -> str:
    """格式化经验条"""
    if threshold <= 0:
        return "▰" * width
    filled = min(width, int(exp / threshold * width))
    return "▰" * filled + "▱" * (width - filled)


def track_task_progress(data: dict, task_type: str, amount: int = 1):
    """更新每日任务进度"""
    if not ext_config.dailyTask.enabled:
        return
    from .utils import get_today_str
    today = get_today_str()
    if data.get("dailyTaskDate") != today:
        return
    tasks = data.get("dailyTasks", [])
    for task in tasks:
        if task["type"] == task_type and not task.get("completed"):
            task["progress"] = task.get("progress", 0) + amount
            if task["progress"] >= task["target"]:
                task["completed"] = True
            break


def give_exp_and_track(data: dict, exp_amount: int, task_type: str = "", task_amount: int = 1):
    """通用经验+任务进度追踪"""
    if exp_amount > 0:
        add_exp(data, exp_amount)
    if task_type:
        track_task_progress(data, task_type, task_amount)
