"""群级数据存储（随机事件、赛季统计等）"""
import json
import random
import asyncio
from pathlib import Path
from typing import Dict, Optional, List
from nonebot import logger
from nonebot_plugin_localstore import get_plugin_data_dir

from .config import ext_config
from .utils import get_today_str, get_current_season_str

GROUP_DATA_DIR: Optional[Path] = None
_group_locks: Dict[str, asyncio.Lock] = {}


def _ensure_dir():
    global GROUP_DATA_DIR
    if GROUP_DATA_DIR is None:
        GROUP_DATA_DIR = Path(get_plugin_data_dir()) / "slave_market" / "group_data"
        GROUP_DATA_DIR.mkdir(parents=True, exist_ok=True)


def _group_path(group_id: int) -> Path:
    _ensure_dir()
    return GROUP_DATA_DIR / f"{group_id}.json"


def _get_lock(group_id: int) -> asyncio.Lock:
    key = str(group_id)
    if key not in _group_locks:
        _group_locks[key] = asyncio.Lock()
    return _group_locks[key]


async def load_group_data(group_id: int) -> Dict:
    """加载群数据"""
    path = _group_path(group_id)
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[SlaveMarket] 读取群数据失败: {path} - {e}")
        return {}


async def save_group_data(group_id: int, data: Dict):
    """保存群数据"""
    path = _group_path(group_id)
    lock = _get_lock(group_id)
    async with lock:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


async def ensure_group_data(group_id: int) -> Dict:
    """确保群数据存在"""
    data = await load_group_data(group_id)
    changed = False

    # 随机事件
    if ext_config.randomEvent.enabled:
        today = get_today_str()
        if data.get("eventDate") != today:
            data["eventDate"] = today
            events = ext_config.randomEvent.events
            weights = [e.get("weight", 1) for e in events]
            chosen = random.choices(events, weights=weights, k=1)[0]
            data["todayEvent"] = {
                "id": chosen["id"],
                "name": chosen["name"],
                "description": chosen["description"],
                "effect": chosen.get("effect", {}),
            }
            changed = True
    else:
        data["todayEvent"] = None
        data["eventDate"] = get_today_str()

    # 赛季统计
    if ext_config.season.enabled:
        season_key = get_current_season_str()
        if data.get("currentSeason") != season_key:
            # 赛季切换，结算旧赛季
            old_season = data.get("currentSeason", "")
            if old_season:
                old_stats = data.get("seasonStats", {})
                data.setdefault("seasonHistory", {})[old_season] = old_stats
            data["currentSeason"] = season_key
            data["seasonStats"] = {}
            changed = True
    else:
        data["currentSeason"] = get_current_season_str()

    if changed:
        await save_group_data(group_id, data)

    return data


async def get_today_event(group_id: int) -> Optional[Dict]:
    """获取今天的群事件"""
    if not ext_config.randomEvent.enabled:
        return None
    data = await ensure_group_data(group_id)
    return data.get("todayEvent")


async def record_season_stat(group_id: int, user_id: int, stat_type: str, amount: int = 1):
    """记录赛季统计"""
    if not ext_config.season.enabled:
        return
    data = await ensure_group_data(group_id)
    season_stats = data.setdefault("seasonStats", {})
    user_stats = season_stats.setdefault(str(user_id), {
        "currencyGrowth": 0,
        "duelWins": 0,
        "trainCount": 0,
        "purchaseCount": 0,
        "valueGrowth": 0,
        "taskCompleted": 0,
    })
    if stat_type in user_stats:
        user_stats[stat_type] += amount
    await save_group_data(group_id, data)


async def get_season_ranking(group_id: int) -> List[Dict]:
    """获取赛季排行榜"""
    if not ext_config.season.enabled:
        return []
    data = await ensure_group_data(group_id)
    season_stats = data.get("seasonStats", {})
    items = []
    for uid, stats in season_stats.items():
        score = (
            stats.get("currencyGrowth", 0) * 0.3 +
            stats.get("duelWins", 0) * 50 +
            stats.get("trainCount", 0) * 10 +
            stats.get("purchaseCount", 0) * 20 +
            stats.get("valueGrowth", 0) * 0.5 +
            stats.get("taskCompleted", 0) * 30
        )
        items.append({
            "user_id": int(uid),
            "score": int(score),
            "stats": stats,
        })
    items.sort(key=lambda x: x["score"], reverse=True)
    return items


async def get_season_history(group_id: int) -> Dict:
    """获取历史赛季记录"""
    data = await load_group_data(group_id)
    return data.get("seasonHistory", {})


async def clear_season_stats(group_id: int):
    """清空当前赛季统计（结算后）"""
    data = await load_group_data(group_id)
    if "seasonStats" in data:
        del data["seasonStats"]
    await save_group_data(group_id, data)
