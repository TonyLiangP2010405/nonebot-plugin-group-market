"""数据存储层 - 异步 JSON 文件读写，群隔离，文件锁"""
import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Optional, List
from nonebot import logger
from nonebot_plugin_localstore import get_plugin_data_dir

DATA_DIR = None
PLAYER_DIR = None
HISTORY_DIR = None
TRACKING_FILE = None

_locks: Dict[str, asyncio.Lock] = {}


def _ensure_dirs():
    global DATA_DIR, PLAYER_DIR, HISTORY_DIR, TRACKING_FILE
    if DATA_DIR is None:
        DATA_DIR = Path(get_plugin_data_dir()) / "slave_market"
        PLAYER_DIR = DATA_DIR / "player"
        HISTORY_DIR = DATA_DIR / "ranking_history"
        TRACKING_FILE = DATA_DIR / "weekly_reset_tracking.json"


def _get_lock(path: str) -> asyncio.Lock:
    if path not in _locks:
        _locks[path] = asyncio.Lock()
    return _locks[path]


def _player_path(group_id: int, user_id: int) -> Path:
    _ensure_dirs()
    return PLAYER_DIR / str(group_id) / f"{user_id}.json"


async def init_storage():
    """初始化存储目录"""
    _ensure_dirs()
    PLAYER_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    logger.info("[SlaveMarket] 存储目录初始化完成")


async def load_player(group_id: int, user_id: int) -> Optional[Dict]:
    """加载玩家数据"""
    path = _player_path(group_id, user_id)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[SlaveMarket] 读取玩家数据失败: {path} - {e}")
        return None


async def save_player(group_id: int, user_id: int, data: Dict):
    """保存玩家数据（带文件锁）"""
    path = _player_path(group_id, user_id)
    lock = _get_lock(str(path))

    async with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


async def player_exists(group_id: int, user_id: int) -> bool:
    return _player_path(group_id, user_id).exists()


async def group_exists(group_id: int) -> bool:
    _ensure_dirs()
    return (PLAYER_DIR / str(group_id)).exists()


async def create_group(group_id: int):
    _ensure_dirs()
    (PLAYER_DIR / str(group_id)).mkdir(parents=True, exist_ok=True)


async def delete_player(group_id: int, user_id: int):
    """删除玩家数据（先备份）"""
    path = _player_path(group_id, user_id)
    if not path.exists():
        return

    try:
        backup_dir = PLAYER_DIR / str(group_id) / "backup"
        backup_dir.mkdir(parents=True, exist_ok=True)
        import datetime
        ts = datetime.datetime.now().isoformat().replace(":", "-").replace(".", "-")
        backup_path = backup_dir / f"{user_id}_{ts}.json"

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        with open(backup_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        path.unlink()
        logger.info(f"[SlaveMarket] 删除存档并备份: 群{group_id} 用户{user_id}")
    except Exception as e:
        logger.error(f"[SlaveMarket] 删除存档失败: {e}")


async def list_group_players(group_id: int) -> List[int]:
    """列出群内所有玩家ID"""
    _ensure_dirs()
    group_dir = PLAYER_DIR / str(group_id)
    if not group_dir.exists():
        return []
    ids = []
    for f in group_dir.iterdir():
        if f.is_file() and f.suffix == ".json" and f.stem.isdigit():
            ids.append(int(f.stem))
    return ids


async def list_groups() -> List[int]:
    """列出所有有数据的群"""
    _ensure_dirs()
    if not PLAYER_DIR.exists():
        return []
    gids = []
    for d in PLAYER_DIR.iterdir():
        if d.is_dir() and d.name.isdigit():
            gids.append(int(d.name))
    return gids


async def ensure_player(group_id: int, user_id: int, nickname: str = "") -> Dict:
    """确保玩家数据存在，不存在则初始化"""
    if not await group_exists(group_id):
        await create_group(group_id)

    data = await load_player(group_id, user_id)
    if data is None:
        data = {
            "currency": 0,
            "slave": [],
            "value": 100,
            "lastWorkingTime": 0,
            "master": "",
            "nickname": nickname,
            "lastPurchaseTime": 0,
            "lastTrainedTime": 0,
            "lastBattleTime": 0,
            "lastRankingTime": 0,
            "lastRobTime": 0,
            "buyBackTimes": 0,
            "lastBuyBackTime": 0,
            "bank": {
                "balance": 0,
                "level": 1,
                "limit": 1000,
                "upgradePrice": 100,
                "lastInterestTime": 0
            },
            "ranking": {"score": 1000, "tier": "青铜", "matches": 0},
            "weeklyResets": 0,
            "lastResetTime": 0,
            "lastResetWeek": 0
        }
        await save_player(group_id, user_id, data)
    elif nickname and data.get("nickname") != nickname:
        data["nickname"] = nickname
        await save_player(group_id, user_id, data)

    return data


# ========== 每周重置追踪 ==========

def load_weekly_reset_tracking() -> Dict:
    _ensure_dirs()
    if not TRACKING_FILE.exists():
        return {"lastResetWeek": 0, "lastResetTime": 0, "resetCount": 0}
    try:
        with open(TRACKING_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"lastResetWeek": 0, "lastResetTime": 0, "resetCount": 0}


def save_weekly_reset_tracking(data: Dict):
    _ensure_dirs()
    TRACKING_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(TRACKING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ========== 排行榜历史 ==========

def save_ranking_history(group_id: int, data: Dict) -> Optional[Path]:
    _ensure_dirs()
    try:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        import datetime
        now = datetime.datetime.now()
        week = get_week_number(now)
        year = now.year
        filename = f"{group_id}_{year}_week{week}.json"
        filepath = HISTORY_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return filepath
    except Exception as e:
        logger.error(f"[SlaveMarket] 保存排行榜历史失败: {e}")
        return None


def get_last_week_ranking_history(group_id: int) -> Optional[Dict]:
    try:
        import datetime
        now = datetime.datetime.now()
        current_week = get_week_number(now)
        current_year = now.year

        last_week = current_week - 1
        last_year = current_year
        if last_week < 1:
            last_year = current_year - 1
            last_week = get_week_number(datetime.datetime(last_year, 12, 31))

        filename = f"{group_id}_{last_year}_week{last_week}.json"
        filepath = HISTORY_DIR / filename
        if not filepath.exists():
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[SlaveMarket] 读取上周排行榜失败: {e}")
        return None


def get_week_number(date) -> int:
    """ISO 周数"""
    d = date.date() if hasattr(date, "date") else date
    return d.isocalendar()[1]
