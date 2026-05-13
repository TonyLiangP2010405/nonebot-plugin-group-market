"""防刷屏核心模块
管理用户冷却、群全局冷却、洪水保护、安静模式、提示限流
"""
import time
from typing import Dict, Optional, Tuple
from nonebot import logger
from nonebot.adapters.onebot.v11 import GroupMessageEvent
from nonebot.permission import SUPERUSER

from .config import ext_config

# ========== 内存状态 ==========
# 用户冷却: {(group_id, user_id, cmd_key): expire_timestamp}
_user_cooldowns: Dict[tuple, float] = {}

# 群全局最后命令时间: {group_id: timestamp}
_group_last_cmd: Dict[int, float] = {}

# 群洪水保护状态: {group_id: {"count": int, "window_start": float, "locked_until": float}}
_group_flood: Dict[int, dict] = {}

# 最后冷却提示时间: {(group_id, user_id, cmd_key): timestamp}
_last_cooldown_reply: Dict[tuple, float] = {}

# 安静模式: {group_id: bool}
_quiet_mode: Dict[int, bool] = {}

# 防刷屏总开关: {group_id: bool} (默认True)
_anti_spam_enabled: Dict[int, bool] = {}

# 群自定义冷却覆盖: {group_id: {cmd_key: seconds}}
_group_cmd_cooldowns: Dict[int, dict] = {}


# ========== 命令分类与默认冷却 ==========
COMMAND_CATEGORIES = {
    "work": {"cat": "behavior_high", "user_cd": 1200, "group_cd": 3, "reply_interval": 60},
    "train": {"cat": "behavior_high", "user_cd": 2700, "group_cd": 3, "reply_interval": 60},
    "duel": {"cat": "behavior_high", "user_cd": 1800, "group_cd": 5, "reply_interval": 60, "target_protection": 900},
    "ranking_join": {"cat": "behavior_high", "user_cd": 1800, "group_cd": 5, "reply_interval": 60},
    "purchase": {"cat": "behavior_high", "user_cd": 1800, "group_cd": 5, "reply_interval": 60, "target_protection": 1800},
    "signin": {"cat": "behavior_high", "user_cd": 86400, "group_cd": 2, "reply_interval": 300},
    "claim_task_reward": {"cat": "behavior_high", "user_cd": 86400, "group_cd": 2, "reply_interval": 300},
    "refresh_task": {"cat": "behavior_high", "user_cd": 21600, "group_cd": 3, "reply_interval": 300},
    # 中频行为类 (如果有的话)
    "arena": {"cat": "behavior_mid", "user_cd": 1800, "group_cd": 5, "reply_interval": 60},
    # 查询类
    "profile": {"cat": "query", "user_cd": 60, "group_cd": 2, "reply_interval": 60},
    "level": {"cat": "query", "user_cd": 60, "group_cd": 2, "reply_interval": 60},
    "achievement": {"cat": "query", "user_cd": 90, "group_cd": 2, "reply_interval": 90},
    "my_items": {"cat": "query", "user_cd": 60, "group_cd": 2, "reply_interval": 60},
    "shop": {"cat": "query", "user_cd": 120, "group_cd": 3, "reply_interval": 120},
    "ranking": {"cat": "query", "user_cd": 180, "group_cd": 10, "reply_interval": 120},
    "event": {"cat": "query", "user_cd": 120, "group_cd": 10, "reply_interval": 120},
    "signin_rank": {"cat": "query", "user_cd": 180, "group_cd": 10, "reply_interval": 120},
    "level_rank": {"cat": "query", "user_cd": 180, "group_cd": 10, "reply_interval": 120},
    "achievement_rank": {"cat": "query", "user_cd": 180, "group_cd": 10, "reply_interval": 120},
    "bounty_list": {"cat": "query", "user_cd": 120, "group_cd": 5, "reply_interval": 120},
    "season_info": {"cat": "query", "user_cd": 120, "group_cd": 5, "reply_interval": 120},
    "season_rank": {"cat": "query", "user_cd": 180, "group_cd": 10, "reply_interval": 120},
    "season_history": {"cat": "query", "user_cd": 180, "group_cd": 10, "reply_interval": 120},
    # 管理类 (不受普通冷却限制)
    "admin": {"cat": "admin", "user_cd": 0, "group_cd": 0, "reply_interval": 0},
    # 其他低频/无冷却
    "help": {"cat": "low", "user_cd": 0, "group_cd": 2, "reply_interval": 30},
    "myslave": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "release": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "buyback": {"cat": "low", "user_cd": 0, "group_cd": 2, "reply_interval": 30},
    "rob": {"cat": "low", "user_cd": 600, "group_cd": 3, "reply_interval": 60},
    "bank_info": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "deposit": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "withdraw": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "upgrade": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "interest": {"cat": "low", "user_cd": 300, "group_cd": 2, "reply_interval": 60},
    "transfer": {"cat": "low", "user_cd": 60, "group_cd": 3, "reply_interval": 60},
    "rankings": {"cat": "low", "user_cd": 60, "group_cd": 5, "reply_interval": 60},
    "reset_status": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "last_week": {"cat": "low", "user_cd": 60, "group_cd": 5, "reply_interval": 60},
    "daily_task": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "title": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "equip_title": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "view_profile": {"cat": "query", "user_cd": 60, "group_cd": 2, "reply_interval": 60},
    "today_event": {"cat": "query", "user_cd": 120, "group_cd": 10, "reply_interval": 120},
    "bounty_post": {"cat": "low", "user_cd": 60, "group_cd": 3, "reply_interval": 60},
    "bounty_claim": {"cat": "low", "user_cd": 60, "group_cd": 3, "reply_interval": 60},
    "bounty_cancel": {"cat": "low", "user_cd": 60, "group_cd": 3, "reply_interval": 60},
    "buy_item": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "use_item": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "gift_item": {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30},
    "season_reward": {"cat": "low", "user_cd": 86400, "group_cd": 2, "reply_interval": 300},
}


def _get_cmd_config(cmd_key: str) -> dict:
    """获取命令配置，支持群自定义覆盖"""
    return COMMAND_CATEGORIES.get(cmd_key, {"cat": "low", "user_cd": 30, "group_cd": 2, "reply_interval": 30})


def _get_user_cd(group_id: int, cmd_key: str) -> int:
    """获取用户冷却时间（支持群覆盖）"""
    base = _get_cmd_config(cmd_key).get("user_cd", 0)
    override = _group_cmd_cooldowns.get(group_id, {}).get(cmd_key)
    if override is not None:
        return override
    return base


def _get_group_cd(group_id: int, cmd_key: str) -> int:
    """获取群全局冷却时间"""
    base = _get_cmd_config(cmd_key).get("group_cd", 2)
    return base


def _get_reply_interval(group_id: int, cmd_key: str) -> int:
    """获取冷却提示间隔"""
    base = _get_cmd_config(cmd_key).get("reply_interval", 60)
    return base


# ========== 核心检查函数 ==========

def is_spam_protection_enabled(group_id: int) -> bool:
    """检查某群防刷屏是否启用"""
    return _anti_spam_enabled.get(group_id, True)


def is_quiet_mode(group_id: int) -> bool:
    """检查某群是否安静模式"""
    return _quiet_mode.get(group_id, False)


def set_quiet_mode(group_id: int, enabled: bool):
    """设置安静模式"""
    _quiet_mode[group_id] = enabled


def set_anti_spam_enabled(group_id: int, enabled: bool):
    """设置防刷屏开关"""
    _anti_spam_enabled[group_id] = enabled


def set_group_cmd_cooldown(group_id: int, cmd_key: str, seconds: int):
    """设置群自定义命令冷却"""
    if group_id not in _group_cmd_cooldowns:
        _group_cmd_cooldowns[group_id] = {}
    _group_cmd_cooldowns[group_id][cmd_key] = seconds


def clear_group_cmd_cooldown(group_id: int, cmd_key: str):
    """清除群自定义命令冷却"""
    if group_id in _group_cmd_cooldowns and cmd_key in _group_cmd_cooldowns[group_id]:
        del _group_cmd_cooldowns[group_id][cmd_key]


def check_cooldown(event: GroupMessageEvent, cmd_key: str) -> Tuple[bool, Optional[str]]:
    """
    检查是否可以执行命令
    返回: (是否允许, 提示消息或None)
    """
    group_id = event.group_id
    user_id = event.user_id

    # 管理员不受普通限制
    if SUPERUSER(event):
        _record_cmd(group_id)
        return True, None

    # 检查防刷屏总开关
    if not is_spam_protection_enabled(group_id):
        return True, None

    # 检查群洪水保护锁
    locked_until = _group_flood.get(group_id, {}).get("locked_until", 0)
    if locked_until > time.time():
        # 保护模式只允许查询类和管理类
        cfg = _get_cmd_config(cmd_key)
        if cfg["cat"] not in ("query", "admin"):
            if is_quiet_mode(group_id):
                return False, None
            # 提示一次
            key = (group_id, user_id, "__flood_lock__")
            last = _last_cooldown_reply.get(key, 0)
            if time.time() - last < 60:
                return False, None
            _last_cooldown_reply[key] = time.time()
            remaining = int(locked_until - time.time())
            return False, f"⛔ 本群游戏指令过于频繁，已进入保护模式（还剩 {remaining // 60} 分钟）"

    # 更新洪水计数
    _update_flood_count(group_id)

    # 检查群全局冷却
    gcfg = _get_cmd_config(cmd_key)
    group_cd = _get_group_cd(group_id, cmd_key)
    if group_cd > 0:
        last_group_cmd = _group_last_cmd.get(group_id, 0)
        elapsed = time.time() - last_group_cmd
        if elapsed < group_cd:
            # 群全局冷却中，静默处理
            return False, None

    # 检查用户冷却
    user_cd = _get_user_cd(group_id, cmd_key)
    if user_cd > 0:
        key = (group_id, user_id, cmd_key)
        expire = _user_cooldowns.get(key, 0)
        if expire > time.time():
            remaining = int(expire - time.time())
            # 检查是否需要提示
            reply_interval = _get_reply_interval(group_id, cmd_key)
            reply_key = (group_id, user_id, cmd_key)
            last_reply = _last_cooldown_reply.get(reply_key, 0)

            if is_quiet_mode(group_id):
                # 安静模式：第一次冷却提示，之后静默
                if time.time() - last_reply < reply_interval:
                    return False, None

            # 非安静模式或首次提示
            _last_cooldown_reply[reply_key] = time.time()
            mins = remaining // 60
            secs = remaining % 60
            time_str = f"{mins}分{secs}秒" if mins > 0 else f"{secs}秒"
            return False, f"⏳ 你还在冷却中，剩余 {time_str}。冷却期间不会重复提醒。"

    # 检查目标保护（购买、决斗等）
    target_protection = gcfg.get("target_protection", 0)
    if target_protection > 0 and hasattr(event, "message"):
        # 尝试从消息中提取目标用户
        target_id = None
        for seg in event.message:
            if seg.type == "at" and seg.data.get("qq") and seg.data["qq"] != "all":
                target_id = int(seg.data["qq"])
                break
        if target_id and target_id != user_id:
            t_key = (group_id, target_id, f"__target_{cmd_key}__")
            t_expire = _user_cooldowns.get(t_key, 0)
            if t_expire > time.time():
                remaining = int(t_expire - time.time())
                reply_key = (group_id, user_id, f"target_{cmd_key}")
                last_reply = _last_cooldown_reply.get(reply_key, 0)
                if time.time() - last_reply < 60:
                    return False, None
                _last_cooldown_reply[reply_key] = time.time()
                mins = remaining // 60
                return False, f"⏳ 该目标还在保护中，剩余 {mins} 分钟"

    # 记录命令
    _record_cmd(group_id, user_id, cmd_key, target_protection)
    return True, None


def _record_cmd(group_id: int, user_id: Optional[int] = None, cmd_key: Optional[str] = None, target_protection: int = 0):
    """记录命令执行，更新冷却和群最后时间"""
    now = time.time()
    _group_last_cmd[group_id] = now

    if user_id and cmd_key:
        user_cd = _get_user_cd(group_id, cmd_key)
        if user_cd > 0:
            _user_cooldowns[(group_id, user_id, cmd_key)] = now + user_cd

        # 目标保护
        if target_protection > 0 and hasattr(check_cooldown, "_last_target_id"):
            target_id = getattr(check_cooldown, "_last_target_id", None)
            if target_id:
                _user_cooldowns[(group_id, target_id, f"__target_{cmd_key}__")] = now + target_protection


def _update_flood_count(group_id: int):
    """更新洪水计数"""
    now = time.time()
    cfg = ext_config.antiSpam.groupFloodProtection
    window = cfg.windowSeconds
    max_cmds = cfg.maxCommands
    lock_duration = cfg.lockSeconds

    state = _group_flood.setdefault(group_id, {"count": 0, "window_start": now, "locked_until": 0})

    # 窗口过期重置
    if now - state["window_start"] > window:
        state["count"] = 0
        state["window_start"] = now

    state["count"] += 1

    # 触发洪水保护
    if state["count"] >= max_cmds and state["locked_until"] <= now:
        state["locked_until"] = now + lock_duration
        logger.warning(f"[AntiSpam] 群{group_id} 触发洪水保护，锁定 {lock_duration} 秒")


def get_flood_status(group_id: int) -> dict:
    """获取群的洪水保护状态"""
    state = _group_flood.get(group_id, {"count": 0, "window_start": 0, "locked_until": 0})
    now = time.time()
    locked = state.get("locked_until", 0) > now
    remaining = int(state["locked_until"] - now) if locked else 0
    return {
        "enabled": is_spam_protection_enabled(group_id),
        "quiet_mode": is_quiet_mode(group_id),
        "locked": locked,
        "lock_remaining": remaining,
        "recent_commands": state["count"],
        "window_seconds": ext_config.antiSpam.groupFloodProtection.windowSeconds,
        "max_commands": ext_config.antiSpam.groupFloodProtection.maxCommands,
    }


def format_flood_status(group_id: int) -> str:
    """格式化洪水状态为文本"""
    s = get_flood_status(group_id)
    lines = ["🛡️ 游戏冷却状态"]
    lines.append(f"━━━━━━━━━━━━━━")
    lines.append(f"防刷屏: {'✅ 开启' if s['enabled'] else '❌ 关闭'}")
    lines.append(f"安静模式: {'✅ 开启' if s['quiet_mode'] else '❌ 关闭'}")
    if s["locked"]:
        lines.append(f"⛔ 保护模式: 还剩 {s['lock_remaining'] // 60} 分钟")
    else:
        lines.append(f"📊 最近 {s['window_seconds']} 秒命令数: {s['recent_commands']}/{s['max_commands']}")
    lines.append(f"━━━━━━━━━━━━━━")
    return "\n".join(lines)


# ========== 提示合并工具 ==========

class ReplyCollector:
    """回复收集器，用于合并多个提示到一次回复"""

    def __init__(self):
        self._pending: Dict[tuple, list] = {}  # {(group_id, user_id): [messages]}

    def add(self, group_id: int, user_id: int, message: str):
        """添加一条待合并的提示"""
        key = (group_id, user_id)
        if key not in self._pending:
            self._pending[key] = []
        self._pending[key].append(message)

    def get_and_clear(self, group_id: int, user_id: int) -> list:
        """获取并清空某用户的待合并提示"""
        key = (group_id, user_id)
        msgs = self._pending.get(key, [])
        if key in self._pending:
            del self._pending[key]
        return msgs

    def has_pending(self, group_id: int, user_id: int) -> bool:
        """是否有待合并提示"""
        key = (group_id, user_id)
        return key in self._pending and len(self._pending[key]) > 0


reply_collector = ReplyCollector()


def collect_tip(group_id: int, user_id: int, message: str):
    """收集一条提示，用于后续合并"""
    reply_collector.add(group_id, user_id, message)


def flush_tips(group_id: int, user_id: int) -> Optional[str]:
    """获取合并后的提示文本，如果没有则返回None"""
    msgs = reply_collector.get_and_clear(group_id, user_id)
    if not msgs:
        return None
    return "\n".join(msgs)
