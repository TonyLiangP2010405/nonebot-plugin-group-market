<div align="center">
  <a href="https://v2.nonebot.dev/store"><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/nbp_logo.png" width="180" height="180" alt="NoneBotPluginLogo"></a>
  <br>
  <p><img src="https://github.com/A-kirami/nonebot-plugin-template/blob/resources/NoneBotPlugin.svg" width="240" alt="NoneBotPluginText"></p>
</div>

<div align="center">

# nonebot-plugin-group-market

_✨ 适用于 QQ 群聊的群友市场经济小游戏 ✨_

<a href="./LICENSE">
    <img src="https://img.shields.io/github/license/TonyLiangP2010405/nonebot-plugin-group-market.svg" alt="license">
</a>
<a href="https://pypi.python.org/pypi/nonebot-plugin-group-market">
    <img src="https://img.shields.io/pypi/v/nonebot-plugin-group-market.svg" alt="pypi">
</a>
<img src="https://img.shields.io/badge/python-3.10+-blue.svg" alt="python">

</div>

适用于 **QQ 群聊** 的 NoneBot2 群友市场经济小游戏，包含打工、购买群友、训练、决斗、银行、排行榜、每日任务、等级、成就、防刷屏等玩法。

> 从 Yunzai-Bot V3 插件 [Slave-Market](https://gitee.com/Tloml-Starry/Slave-Market) 移植并大幅扩展而来。

> [!NOTE]
> 本仓库自带了一个发布工作流，你可以使用此工作流自动发布你的插件到 PyPI

<details>
<summary>配置发布工作流</summary>

1. 前往 https://pypi.org/manage/account/#api-tokens 并创建一个新的 API 令牌。创建成功后不要关闭页面，不然你将无法再次查看此令牌。
2. 在单独的浏览器选项卡或窗口中，打开 [Actions secrets and variables](./settings/secrets/actions) 页面。你也可以在 Settings - Secrets and variables - Actions 中找到此页面。
3. 点击 New repository secret 按钮，创建一个名为 `PYPI_API_TOKEN` 的新令牌，并从第一步复制粘贴令牌。

</details>

> [!IMPORTANT]
> 这个发布工作流需要 pyproject.toml 文件，并且只支持 [PEP 621](https://peps.python.org/pep-0621/) 标准的 pyproject.toml 文件

<details>
<summary>触发发布工作流</summary>
从本地推送任意 tag 即可触发。

创建 tag:

    git tag <tag_name>

推送本地所有 tag:

    git push origin --tags

</details>

## 📖 介绍

**群友市场** 是一个适用于 QQ 群聊的 NoneBot2 文字游戏插件。玩家可以在群内通过打工赚取金币，购买其他群友作为"奴隶"（游戏内称呼），训练、决斗奴隶，参与排位赛，使用银行系统存取金币赚取利息。

v0.2.0 新增了签到、等级、成就、每日任务、道具商店、随机事件、称号、悬赏、赛季等扩展玩法。

v0.3.0 新增了多层防刷屏系统，包括用户级冷却、群全局冷却、洪水保护、安静模式等，让游戏更适合长期运行。

## 💿 安装

<details open>
<summary>使用 nb-cli 安装</summary>
在 nonebot2 项目的根目录下打开命令行，输入以下指令即可安装

    nb plugin install nonebot-plugin-group-market

</details>

<details>
<summary>使用包管理器安装</summary>
在 nonebot2 项目的插件目录下，打开命令行，根据你使用的包管理器，输入相应的安装命令

<details>
<summary>pip</summary>

    pip install nonebot-plugin-group-market
</details>
<details>
<summary>pdm</summary>

    pdm add nonebot-plugin-group-market
</details>
<details>
<summary>poetry</summary>

    poetry add nonebot-plugin-group-market
</details>
<details>
<summary>conda</summary>

    conda install nonebot-plugin-group-market
</details>

打开 nonebot2 项目根目录下的 `pyproject.toml` 文件，在 `[tool.nonebot]` 部分追加写入

    plugins = ["nonebot_plugin_group_market"]

</details>

## ⚙️ 配置

在 nonebot2 项目的 `.env` 文件中添加下表中的配置

| 配置项 | 必填 | 默认值 | 说明 |
|:-----:|:----:|:----:|:----:|
| `slavemarket__work__cooldown` | 否 | `3600` | 打工冷却时间（秒） |
| `slavemarket__purchase__cooldown` | 否 | `3600` | 购买冷却时间（秒） |
| `slavemarket__training__cooldown` | 否 | `7200` | 训练冷却时间（秒） |
| `slavemarket__arena__cooldown` | 否 | `7200` | 决斗冷却时间（秒） |
| `slavemarket__bank__initialLimit` | 否 | `1000` | 银行初始存款限额 |
| `slavemarket__weeklyReset__enabled` | 否 | `true` | 是否启用每周重置 |
| `slavemarket__antiSpam__enabled` | 否 | `true` | 是否启用防刷屏 |
| `slavemarket__antiSpam__quietMode__enabled` | 否 | `true` | 是否启用安静模式 |
| `slavemarket__antiSpam__groupFloodProtection__windowSeconds` | 否 | `60` | 洪水保护统计窗口（秒） |
| `slavemarket__antiSpam__groupFloodProtection__maxCommands` | 否 | `20` | 窗口内最大命令数 |
| `slavemarket__antiSpam__groupFloodProtection__lockSeconds` | 否 | `300` | 洪水锁定持续时间（秒） |

> 所有配置均有默认值，零配置即可运行。

## 🎉 使用

### 指令表

| 指令 | 权限 | 需要@ | 范围 | 说明 |
|:-----:|:----:|:----:|:----:|:----:|
| #奴隶帮助 | 群员 | 否 | 群聊 | 查看帮助 |
| #打工 | 群员 | 否 | 群聊 | 赚取金币（冷却20分钟） |
| #购买群友 @用户 | 群员 | 是 | 群聊 | 购买群友（冷却30分钟） |
| #我的奴隶 | 群员 | 否 | 群聊 | 查看自己的奴隶 |
| #训练 @用户 | 群员 | 是 | 群聊 | 训练奴隶（冷却45分钟） |
| #决斗 @用户1 @用户2 | 群员 | 是 | 群聊 | 奴隶决斗（冷却30分钟） |
| #排位赛 | 群员 | 否 | 群聊 | 查看排位信息 |
| #参加排位赛 @用户 | 群员 | 是 | 群聊 | 参加排位（冷却30分钟） |
| #存款 数量 | 群员 | 否 | 群聊 | 银行存款 |
| #取款 数量 | 群员 | 否 | 群聊 | 银行取款 |
| #升级信用 | 群员 | 否 | 群聊 | 升级银行等级 |
| #银行信息 | 群员 | 否 | 群聊 | 查看银行 |
| #领取利息 | 群员 | 否 | 群聊 | 领取利息 |
| #转账 数量 @用户 | 群员 | 是 | 群聊 | 向他人转账 |
| #奴隶市场 | 群员 | 否 | 群聊 | 排行榜 |
| #回购自己 | 群员 | 否 | 群聊 | 从主人处回购 |
| #抢劫 @用户 | 群员 | 是 | 群聊 | 抢劫金币 |
| #签到 | 群员 | 否 | 群聊 | 每日签到 |
| #我的等级 | 群员 | 否 | 群聊 | 查看等级经验 |
| #我的成就 | 群员 | 否 | 群聊 | 查看成就 |
| #每日任务 | 群员 | 否 | 群聊 | 查看今日任务 |
| #领取任务奖励 | 群员 | 否 | 群聊 | 领取任务奖励 |
| #刷新任务 | 群员 | 否 | 群聊 | 刷新每日任务 |
| #我的信息 | 群员 | 否 | 群聊 | 个人信息面板 |
| #查看信息 @用户 | 群员 | 是 | 群聊 | 查看他人信息 |
| #商店 | 群员 | 否 | 群聊 | 道具商店 |
| #购买道具 道具名 | 群员 | 否 | 群聊 | 购买道具 |
| #我的道具 | 群员 | 否 | 群聊 | 查看背包 |
| #使用道具 道具名 | 群员 | 否 | 群聊 | 使用道具 |
| #赠送道具 @用户 道具名 | 群员 | 是 | 群聊 | 赠送道具 |
| #今日事件 | 群员 | 否 | 群聊 | 查看今日群事件 |
| #我的称号 | 群员 | 否 | 群聊 | 查看称号 |
| #佩戴称号 称号名 | 群员 | 否 | 群聊 | 佩戴称号 |
| #悬赏列表 | 群员 | 否 | 群聊 | 查看悬赏 |
| #发布悬赏 @用户 金额 | 群员 | 是 | 群聊 | 发布悬赏 |
| #领取悬赏 @用户 | 群员 | 是 | 群聊 | 领取悬赏 |
| #取消悬赏 ID | 群员 | 否 | 群聊 | 取消悬赏 |
| #赛季信息 | 群员 | 否 | 群聊 | 赛季信息 |
| #赛季排行 | 群员 | 否 | 群聊 | 赛季排名 |
| #赛季奖励 | 群员 | 否 | 群聊 | 领取赛季奖励 |
| #历史赛季 | 群员 | 否 | 群聊 | 历史赛季记录 |
| #游戏冷却状态 | 任何人 | 否 | 群聊 | 查看冷却状态 |
| #开启安静模式 | 管理员 | 否 | 群聊 | 开启安静模式 |
| #关闭安静模式 | 管理员 | 否 | 群聊 | 关闭安静模式 |
| #开启防刷屏 | 管理员 | 否 | 群聊 | 启用防刷屏 |
| #关闭防刷屏 | 管理员 | 否 | 群聊 | 禁用防刷屏 |

> 完整命令列表请发送 `#奴隶帮助` 或 `#群友市场帮助` 查看。

## 📋 更新日志

见 [CHANGELOG.md](./CHANGELOG.md)

## 📄 许可证

本项目使用 [木兰宽松许可证，第2版](./LICENSE) 开源。

---

*若从旧版 `nonebot-plugin-slave-market` 迁移，旧数据完全兼容，详见 [PORTING_NOTES.md](./PORTING_NOTES.md)。*
