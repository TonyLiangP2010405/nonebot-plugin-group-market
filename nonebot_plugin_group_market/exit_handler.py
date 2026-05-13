"""退群删档处理"""
from nonebot import on_notice, logger
from nonebot.adapters.onebot.v11 import GroupDecreaseNoticeEvent

from .storage import delete_player


from nonebot.rule import Rule

async def is_group_decrease(event: GroupDecreaseNoticeEvent) -> bool:
    return event.sub_type in ("leave", "kick")

exit_notice = on_notice(rule=Rule(is_group_decrease), priority=5)

@exit_notice.handle()
async def handle_group_decrease(event: GroupDecreaseNoticeEvent):
    if event.sub_type not in ("leave", "kick"):
        return

    user_id = event.user_id
    group_id = event.group_id

    try:
        await delete_player(group_id, user_id)
        logger.info(f"[SlaveMarket] 群{group_id} 用户{user_id} 退群/被踢，已删除存档")
    except Exception as e:
        logger.error(f"[SlaveMarket] 退群删档失败: {e}")
