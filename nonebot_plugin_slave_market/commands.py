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

logger.info("[SlaveMarket] 指令模块已注册")
