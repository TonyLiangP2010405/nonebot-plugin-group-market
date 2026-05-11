"""
NoneBot2 群友市场插件
从 Yunzai-Bot Slave-Market 移植
License: Mulan PSL v2
"""
from nonebot import require, logger, get_driver
from nonebot.plugin import PluginMetadata

require("nonebot_plugin_apscheduler")

from .config import plugin_config
from .storage import init_storage
from .weekly_reset_task import start_weekly_reset_scheduler

__plugin_meta__ = PluginMetadata(
    name="群友市场",
    description="群聊文字游戏插件：购买群友、打工、训练、决斗、排位赛、银行",
    usage=(
        "#奴隶帮助 / #nl帮助 - 查看帮助\n"
        "#打工 - 赚取金币\n"
        "#购买群友 @用户 - 购买奴隶\n"
        "#我的奴隶 - 查看自己的奴隶\n"
        "#训练 @用户 - 训练奴隶\n"
        "#决斗 @用户1 @用户2 - 奴隶决斗\n"
        "#排位赛 - 查看排位信息\n"
        "#参加排位赛 @用户 - 参加排位\n"
        "#存款 数量 - 银行存款\n"
        "#取款 数量 - 银行取款\n"
        "#银行信息 - 查看银行\n"
        "#奴隶市场 - 排行榜\n"
        "#奴隶重置状态 - 查看重置状态"
    ),
    type="application",
    homepage="https://github.com/TonyLiangP2010405/nonebot-plugin-slave-market",
    config=None,
    supported_adapters={"~onebot.v11"},
)

# 导入所有指令模块（触发注册）
from . import commands

driver = get_driver()

@driver.on_bot_connect
async def on_bot_connect():
    logger.info("[SlaveMarket] 群友市场插件加载中...")
    await init_storage()
    start_weekly_reset_scheduler()
    logger.info("[SlaveMarket] 插件已就绪！")
