"""更新指令"""
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent

update_cmd = on_command("奴隶更新", priority=5, block=True)

@update_cmd.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await update_cmd.finish(
        "📦 群友市场插件更新\n"
        "━━━━━━━━━━━━━━\n"
        "请使用以下命令更新:\n"
        "  pip install -U nonebot-plugin-slave-market\n\n"
        "或从 GitHub 拉取最新代码:\n"
        "  git pull\n"
        "━━━━━━━━━━━━━━"
    )
