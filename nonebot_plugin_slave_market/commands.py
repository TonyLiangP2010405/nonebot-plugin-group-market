"""指令入口 - 导入所有子模块触发注册"""
from nonebot import on_command, logger
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, GroupMessageEvent, MessageSegment
from nonebot.params import CommandArg
from nonebot.permission import SUPERUSER

# 基础帮助
from .commands_help import help_cmd
from .commands_work import work_cmd
from .commands_purchase import purchase_cmd
from .commands_slave import myslave_cmd, release_cmd
from .commands_buyback import buyback_cmd
from .commands_rob import rob_cmd
from .commands_train import train_cmd
from .commands_arena import arena_cmd
from .commands_ranking import ranking_info_cmd, ranking_join_cmd
from .commands_bank import deposit_cmd, withdraw_cmd, upgrade_cmd, bank_info_cmd, interest_cmd, transfer_cmd
from .commands_rankings import rankings_cmd
from .commands_weekly import reset_status_cmd, manual_reset_cmd, reset_help_cmd, last_week_cmd
from .commands_update import update_cmd
from .exit_handler import exit_notice

# 扩展玩法模块
from .commands_signin import signin_cmd, signin_rank_cmd
from .commands_level import level_cmd, level_rank_cmd
from .commands_achievement import achievement_cmd, achievement_rank_cmd
from .commands_dailytask import daily_task_cmd, claim_task_reward_cmd, refresh_task_cmd
from .commands_profile import profile_cmd, view_profile_cmd
from .commands_shop import shop_cmd, buy_item_cmd, my_items_cmd, use_item_cmd, gift_item_cmd
from .commands_randomevent import today_event_cmd
from .commands_title import title_cmd, equip_title_cmd
from .commands_bounty import bounty_post_cmd, bounty_list_cmd, bounty_claim_cmd, bounty_cancel_cmd
from .commands_season import season_info_cmd, season_rank_cmd, season_reward_cmd, season_history_cmd

logger.info("[SlaveMarket] 指令模块已注册")
