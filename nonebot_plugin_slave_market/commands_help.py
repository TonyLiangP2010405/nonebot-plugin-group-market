"""帮助指令"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

help_cmd = on_command("奴隶帮助", aliases={"nl帮助", "群友帮助", "奴隶菜单", "nl菜单"}, priority=5, block=True)

HELP_TEXT = """📖 群友市场帮助
━━━━━━━━━━━━━━
💰 经济:
  #打工 - 赚取金币
  #购买群友 @用户 - 购买奴隶
  #我的奴隶 - 查看奴隶
  #放生奴隶 @用户 - 放生奴隶

⚔️ 竞技:
  #训练 @用户 - 训练奴隶
  #一键训练 - 训练所有奴隶
  #决斗 @用户1 @用户2 - 奴隶决斗
  #排位赛 - 查看排位信息
  #参加排位赛 @用户 - 参加排位

🏦 银行:
  #存款 数量 - 银行存款
  #一键存款 - 存入所有金币
  #取款 数量 - 银行取款
  #升级信用 - 升级银行等级
  #一键升级信用 - 自动升级
  #银行信息 - 查看银行
  #领取利息 - 领取利息
  #转账 数量 @用户 - 转账

📊 其他:
  #奴隶市场 / #排行榜 - 排行榜
  #回购自己 - 从主人处回购
  #抢劫 @用户 - 抢劫金币
  #奴隶重置状态 - 重置状态
  #上周排行榜 - 上周排行
  #奴隶重置帮助 - 重置帮助
━━━━━━━━━━━━━━"""

@help_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    if not isinstance(event, GroupMessageEvent):
        await help_cmd.finish("该游戏只能在群内使用")
    await help_cmd.finish(HELP_TEXT)
