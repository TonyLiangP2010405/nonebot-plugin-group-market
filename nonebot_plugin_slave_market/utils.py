"""通用工具函数"""
import datetime
from typing import Optional
from nonebot import logger
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.permission import SUPERUSER

from .config import plugin_config


def format_currency(value: float) -> float:
    """格式化货币为两位小数"""
    return round(float(value), 2)


def check_permission(event: GroupMessageEvent) -> bool:
    """检查用户是否有权限跳过冷却"""
    if SUPERUSER(event):
        return True
    if str(event.user_id) in plugin_config.ignoreCDUsers:
        return True
    return False


async def get_member_nickname(bot: Bot, group_id: int, user_id: int) -> str:
    """获取群成员昵称，失败时返回用户ID字符串"""
    try:
        info = await bot.get_group_member_info(group_id=group_id, user_id=user_id, no_cache=True)
        return info.get("card") or info.get("nickname") or str(user_id)
    except Exception as e:
        logger.warning(f"[SlaveMarket] 获取群成员信息失败: {group_id}/{user_id} - {e}")
        return str(user_id)


def get_week_number(date: Optional[datetime.datetime] = None) -> int:
    """获取ISO周数"""
    if date is None:
        date = datetime.datetime.now()
    return date.isocalendar()[1]
