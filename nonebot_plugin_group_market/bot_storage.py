"""BOT 陪玩数据存储 - 每个群独立的 BOT 虚拟玩家数据"""
import asyncio
import json
import random
import time
from pathlib import Path
from typing import Dict, Optional, List, Any
from nonebot import logger
from nonebot_plugin_localstore import get_plugin_data_dir

from .config import plugin_config

BOT_DATA_DIR: Optional[Path] = None
_bot_locks: Dict[str, asyncio.Lock] = {}

# BOT ID 前缀，使用负数避免与真实 QQ 号冲突
BOT_ID_PREFIX = -900000000

_BOT_NAMES = [
    "市场老板娘", "黑心资本家", "机器人买家", "记仇型AI",
    "打工狂魔", "奴隶大亨", "金币猎手", "群友收割机",
    "资本巨鳄", "训练狂人", "决斗之王", "悬赏猎人",
]

_BOT_TITLES = [
    "初入江湖", "腰缠万贯", "决斗之王", "奴隶收藏家",
    "一代宗师", "传说", "早起的鸟儿", "持之以恒",
]


def _ensure_dir():
    global BOT_DATA_DIR
    if BOT_DATA_DIR is None:
        BOT_DATA_DIR = Path(get_plugin_data_dir()) / "slave_market" / "bot_players"
        BOT_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _bot_path(group_id: int, bot_id: int) -> Path:
    _ensure_dir()
    return BOT_DATA_DIR / str(group_id) / f"bot_{bot_id}.json"


def _group_bots_dir(group_id: int) -> Path:
    _ensure_dir()
    d = BOT_DATA_DIR / str(group_id)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _get_lock(path: str) -> asyncio.Lock:
    if path not in _bot_locks:
        _bot_locks[path] = asyncio.Lock()
    return _bot_locks[path]


def generate_bot_id(group_id: int, index: int = 0) -> int:
    """生成 BOT 虚拟用户 ID，确保不和真实 QQ 号冲突"""
    return BOT_ID_PREFIX - group_id * 100 - index


def _new_bot_data(group_id: int, bot_id: int, nickname: str = "", strategy: str = "random") -> Dict:
    """创建新 BOT 玩家数据"""
    name = nickname or random.choice(_BOT_NAMES)
    return {
        "bot_id": bot_id,
        "group_id": group_id,
        "nickname": name,
        "strategy": strategy,
        "currency": 500,
        "slave": [],
        "value": 100,
        "level": 1,
        "exp": 0,
        "titles": [random.choice(_BOT_TITLES)],
        "equippedTitle": "",
        "achievements": [],
        "inventory": {},
        "bank": {
            "balance": 0,
            "level": 1,
            "limit": 1000,
            "upgradePrice": 100,
            "lastInterestTime": 0,
        },
        "ranking": {"score": 1000, "tier": "青铜", "matches": 0},
        "duelStats": {"wins": 0, "losses": 0, "total": 0},
        "workCount": 0,
        "purchaseCount": 0,
        "trainSuccessCount": 0,
        "totalTasksCompleted": 0,
        "dailyActionCount": 0,
        "lastActionTime": 0,
        "lastWorkTime": 0,
        "lastPurchaseTime": 0,
        "lastTrainTime": 0,
        "lastBattleTime": 0,
        "lastRobTime": 0,
        "lastSignInDate": "",
        "continuousSignInDays": 0,
        "totalSignInDays": 0,
        "dailyTasks": [],
        "dailyTaskDate": "",
        "dailyTaskProgress": {},
        "profileStats": {},
        "claimedRewards": [],
        "buyBackTimes": 0,
        "lastBuyBackTime": 0,
        "weeklyResets": 0,
        "lastResetTime": 0,
        "lastResetWeek": 0,
        "created_at": int(time.time()),
    }


async def load_bot(group_id: int, bot_id: int) -> Optional[Dict]:
    """加载 BOT 数据"""
    path = _bot_path(group_id, bot_id)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[BotPlay] 读取 BOT 数据失败: {path} - {e}")
        return None


async def save_bot(group_id: int, bot_id: int, data: Dict):
    """保存 BOT 数据（带文件锁）"""
    path = _bot_path(group_id, bot_id)
    lock = _get_lock(str(path))
    async with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


async def bot_exists(group_id: int, bot_id: int) -> bool:
    return _bot_path(group_id, bot_id).exists()


async def ensure_bot(group_id: int, bot_id: int, nickname: str = "", strategy: str = "random") -> Dict:
    """确保 BOT 数据存在"""
    data = await load_bot(group_id, bot_id)
    if data is None:
        data = _new_bot_data(group_id, bot_id, nickname, strategy)
        await save_bot(group_id, bot_id, data)
    else:
        # 补充可能缺失的字段
        defaults = _new_bot_data(group_id, bot_id)
        changed = False
        for key, val in defaults.items():
            if key not in data:
                data[key] = val
                changed = True
        if changed:
            await save_bot(group_id, bot_id, data)
    return data


async def list_group_bots(group_id: int) -> List[int]:
    """列出群内所有 BOT ID"""
    _ensure_dir()
    group_dir = _group_bots_dir(group_id)
    if not group_dir.exists():
        return []
    ids = []
    for f in group_dir.iterdir():
        if f.is_file() and f.name.startswith("bot_") and f.suffix == ".json":
            try:
                bid = int(f.stem.replace("bot_", ""))
                ids.append(bid)
            except ValueError:
                pass
    return ids


async def delete_bot(group_id: int, bot_id: int):
    """删除 BOT 数据"""
    path = _bot_path(group_id, bot_id)
    if path.exists():
        try:
            path.unlink()
            logger.info(f"[BotPlay] 删除 BOT 数据: 群{group_id} BOT{bot_id}")
        except Exception as e:
            logger.error(f"[BotPlay] 删除 BOT 数据失败: {e}")


async def reset_bot(group_id: int, bot_id: int, nickname: str = "", strategy: str = "random") -> Dict:
    """重置 BOT 数据"""
    data = _new_bot_data(group_id, bot_id, nickname, strategy)
    await save_bot(group_id, bot_id, data)
    return data


# ========== 群 BOT 陪玩开关状态 ==========

_bot_enabled: Dict[int, bool] = {}


def is_bot_play_enabled(group_id: int) -> bool:
    """检查某群 BOT 陪玩是否开启"""
    return _bot_enabled.get(group_id, False)


def set_bot_play_enabled(group_id: int, enabled: bool):
    """设置群 BOT 陪玩开关"""
    _bot_enabled[group_id] = enabled
    logger.info(f"[BotPlay] 群{group_id} BOT陪玩 {'开启' if enabled else '关闭'}")


# ========== BOT 群设置 ==========

_bot_group_settings: Dict[int, Dict] = {}


def get_bot_group_settings(group_id: int) -> Dict:
    """获取群 BOT 设置"""
    if group_id not in _bot_group_settings:
        cfg = plugin_config.botPlay
        _bot_group_settings[group_id] = {
            "enabled": False,
            "action_probability": cfg.actionProbability,
            "action_cooldown": cfg.actionCooldown,
            "daily_action_limit": cfg.dailyActionLimit,
            "summon_cooldown": cfg.summonCooldown,
            "allow_attack": cfg.allowAttack,
            "allow_buy_from_players": cfg.allowBuyFromPlayers,
            "message_mode": cfg.messageMode,
            "max_per_group": cfg.maxPerGroup,
            "strategy": cfg.strategy,
        }
    return _bot_group_settings[group_id]


def set_bot_group_setting(group_id: int, key: str, value: Any):
    """设置群 BOT 配置项"""
    settings = get_bot_group_settings(group_id)
    settings[key] = value


# ========== BOT 今日行动计数 ==========

_bot_daily_counts: Dict[tuple, int] = {}  # {(group_id, bot_id): count}
_bot_daily_date: str = ""


def _get_today_str() -> str:
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d")


def get_bot_daily_action_count(group_id: int, bot_id: int) -> int:
    """获取 BOT 今日行动次数"""
    global _bot_daily_date
    today = _get_today_str()
    if _bot_daily_date != today:
        _bot_daily_counts.clear()
        _bot_daily_date = today
    return _bot_daily_counts.get((group_id, bot_id), 0)


def increment_bot_daily_action(group_id: int, bot_id: int):
    """增加 BOT 今日行动次数"""
    global _bot_daily_date
    today = _get_today_str()
    if _bot_daily_date != today:
        _bot_daily_counts.clear()
        _bot_daily_date = today
    key = (group_id, bot_id)
    _bot_daily_counts[key] = _bot_daily_counts.get(key, 0) + 1


def can_bot_act(group_id: int, bot_id: int) -> bool:
    """检查 BOT 是否还可以行动"""
    settings = get_bot_group_settings(group_id)
    daily_limit = settings.get("daily_action_limit", 20)
    return get_bot_daily_action_count(group_id, bot_id) < daily_limit


# ========== BOT 行动冷却 ==========

_bot_action_cooldowns: Dict[tuple, float] = {}


def is_bot_action_cooled(group_id: int, bot_id: int, cooldown_seconds: int = None) -> bool:
    """检查 BOT 行动冷却是否满足"""
    if cooldown_seconds is None:
        cooldown_seconds = get_bot_group_settings(group_id).get("action_cooldown", 600)
    key = (group_id, bot_id)
    last = _bot_action_cooldowns.get(key, 0)
    return (time.time() - last) >= cooldown_seconds


def record_bot_action(group_id: int, bot_id: int):
    """记录 BOT 行动时间"""
    _bot_action_cooldowns[(group_id, bot_id)] = time.time()
    increment_bot_daily_action(group_id, bot_id)


# ========== BOT 召唤冷却 ==========

_bot_summon_cooldowns: Dict[tuple, float] = {}


def is_bot_summon_cooled(group_id: int, bot_id: int, cooldown_seconds: int = None) -> bool:
    """检查 BOT 召唤冷却"""
    if cooldown_seconds is None:
        cooldown_seconds = get_bot_group_settings(group_id).get("summon_cooldown", 1800)
    key = (group_id, bot_id)
    last = _bot_summon_cooldowns.get(key, 0)
    return (time.time() - last) >= cooldown_seconds


def record_bot_summon(group_id: int, bot_id: int):
    """记录 BOT 召唤时间"""
    _bot_summon_cooldowns[(group_id, bot_id)] = time.time()
