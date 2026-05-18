"""
NoneBot2 群友市场插件
License: Mulan PSL v2
"""
from nonebot import require, logger, get_driver
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_apscheduler")

from .config import plugin_config, Config
from .storage import init_storage
from .weekly_reset_task import start_weekly_reset_scheduler

__plugin_meta__ = PluginMetadata(
    name="群友市场",
    description="适用于 QQ 群聊的群友市场经济小游戏，包含打工、购买群友、训练、决斗、银行、排行榜、每日任务、等级、成就、防刷屏等玩法。",
    usage=(
        "发送 /群友市场帮助 或 /奴隶帮助 查看完整玩法说明。\n"
        "核心命令: /打工 /购买群友 /训练 /决斗 /排位赛 /银行 /签到 /每日任务 /商店"
    ),
    type="application",
    homepage="https://github.com/TonyLiangP2010405/nonebot-plugin-group-market",
    config=Config,
    supported_adapters={"~onebot.v11"},
)

# 导入扩展配置（确保先加载）
from . import extension

# 导入 BOT 陪玩模块（确保存储和命令加载）
from . import bot_storage
from . import bot_strategy
from . import bot_actions
from . import bot_commands

# 导入所有指令模块（触发注册）
from . import commands

driver = get_driver()

@driver.on_bot_connect
async def on_bot_connect():
    logger.info("[GroupMarket] 群友市场插件加载中...")
    await init_storage()
    # 确保扩展群数据目录存在
    from .extension.group_storage import _ensure_dir
    _ensure_dir()
    start_weekly_reset_scheduler()
    logger.info("[GroupMarket] 插件已就绪！")
