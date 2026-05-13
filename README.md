<div align="center">

# ✨ 群友市场 ✨

<a href="https://v2.nonebot.dev/store">
  <img src="https://raw.githubusercontent.com/A-kirami/nonebot-plugin-template/resources/NoneBotPlugin.svg" width="300" height="120" alt="NoneBotPluginText">
</a>

[![pypi](https://img.shields.io/pypi/v/nonebot-plugin-group-market.svg)](https://pypi.python.org/pypi/nonebot-plugin-group-market)
[![python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![license](https://img.shields.io/badge/license-MulanPSL--2.0-green.svg)](./LICENSE)

</div>

适用于 **QQ 群聊** 的 NoneBot2 群友市场经济小游戏，包含打工、购买群友、训练、决斗、银行、排行榜、每日任务、等级、成就、防刷屏等玩法。

> 从 Yunzai-Bot V3 插件 [Slave-Market](https://gitee.com/Tloml-Starry/Slave-Market) 移植并大幅扩展而来。

---

## 📦 安装

### 使用 nb-cli 安装（推荐）

在 nonebot2 项目的根目录下打开命令行，输入：

```bash
nb plugin install nonebot-plugin-group-market
```

### 使用包管理器安装

```bash
pip install nonebot-plugin-group-market
```

然后在 `pyproject.toml` 的 `[tool.nonebot]` 部分追加：

```toml
plugins = ["nonebot_plugin_group_market"]
```

---

## 🎮 功能

### 核心玩法
- 💰 **打工** — 赚取金币
- 🧑‍🌾 **购买群友** — 将群友收为"奴隶"（游戏内称呼，可自定义）
- ⚔️ **训练** — 提升奴隶身价
- ⚔️ **决斗** — 奴隶之间决斗
- 🏆 **排位赛** — 段位系统（青铜→钻石）
- 🏦 **银行** — 存款/取款/升级/利息/转账
- 📊 **排行榜** — 金币榜/身价榜

### 扩展玩法 (v0.2.0+)
- ✅ **签到系统** — 连续签到奖励，7/30天里程碑
- ⭐ **等级经验** — 50级上限，打工/训练/决斗获经验
- 🏅 **成就系统** — 20+ 成就可解锁
- 📋 **每日任务** — 每天3个随机任务
- 📊 **个人信息面板** — 综合数据一览
- 🛒 **道具商店** — 6种道具可购买/使用/赠送
- 📢 **随机事件** — 每天一个群事件影响玩法
- 👑 **称号系统** — 8个称号，部分带属性加成
- 🎯 **悬赏系统** — 发布/领取/取消悬赏
- 🏆 **赛季系统** — 周/月赛季排名与奖励

### 防刷屏保护 (v0.3.0+)
- ⏳ **多层冷却** — 用户级+群全局冷却
- 🛡️ **洪水保护** — 60秒内命令过多自动锁定
- 🔇 **安静模式** — 冷却期间重复触发静默处理
- 📉 **查询限流** — 排行榜/信息面板等也有冷却

---

## 📝 使用说明

在群聊中发送以下指令（默认以 `#` 为前缀）：

### 经济玩法

| 指令 | 说明 |
|------|------|
| `#打工` | 赚取金币（冷却20分钟） |
| `#购买群友 @用户` | 购买群友（冷却30分钟） |
| `#我的奴隶` | 查看自己的奴隶 |
| `#放生奴隶 @用户` | 放生奴隶 |
| `#训练 @用户` | 训练奴隶（冷却45分钟） |
| `#决斗 @用户1 @用户2` | 奴隶决斗（冷却30分钟） |
| `#排位赛` | 查看排位信息 |
| `#参加排位赛 @用户` | 参加排位（冷却30分钟） |

### 银行系统

| 指令 | 说明 |
|------|------|
| `#存款 数量` | 银行存款 |
| `#取款 数量` | 银行取款 |
| `#升级信用` | 升级银行等级 |
| `#银行信息` | 查看银行详情 |
| `#领取利息` | 领取银行利息 |
| `#转账 数量 @用户` | 向他人转账 |

### 扩展玩法

| 指令 | 说明 |
|------|------|
| `#签到` / `#打卡` | 每日签到 |
| `#我的等级` | 查看等级经验 |
| `#我的成就` | 查看成就 |
| `#每日任务` | 查看今日任务 |
| `#领取任务奖励` | 领取任务奖励 |
| `#我的信息` | 个人信息面板 |
| `#商店` | 道具商店 |
| `#购买道具 道具名` | 购买道具 |
| `#今日事件` | 查看今日群事件 |
| `#我的称号` | 查看称号 |
| `#悬赏列表` | 查看悬赏 |
| `#赛季信息` | 赛季信息 |
| `#赛季排行` | 赛季排名 |

### 管理命令

| 指令 | 权限 | 说明 |
|------|------|------|
| `#游戏冷却状态` | 任何人 | 查看当前群防刷屏状态 |
| `#开启安静模式` | 管理员 | 冷却重复触发静默 |
| `#关闭安静模式` | 管理员 | 恢复提示 |
| `#开启防刷屏` | 管理员 | 启用防刷屏 |
| `#关闭防刷屏` | 管理员 | 禁用防刷屏 |

> 完整命令列表请发送 `#奴隶帮助` 或 `#群友市场帮助` 查看。

---

## ⚙️ 配置

在 `.env` 文件中添加：

```env
# 打工冷却（秒）
slavemarket__work__cooldown=1200

# 购买冷却（秒）
slavemarket__purchase__cooldown=1800

# 银行初始限额
slavemarket__bank__initialLimit=1000

# 每周重置开关
slavemarket__weeklyReset__enabled=true

# 防刷屏总开关
slavemarket__antiSpam__enabled=true

# 安静模式开关
slavemarket__antiSpam__quietMode__enabled=true

# 洪水保护：统计窗口（秒）
slavemarket__antiSpam__groupFloodProtection__windowSeconds=60

# 洪水保护：窗口内最大命令数
slavemarket__antiSpam__groupFloodProtection__maxCommands=20

# 洪水保护：锁定持续时间（秒）
slavemarket__antiSpam__groupFloodProtection__lockSeconds=300
```

> 所有配置均有默认值，零配置即可运行。详细配置项见源码 `config.py`。

---

## 📋 更新日志

见 [CHANGELOG.md](./CHANGELOG.md)

---

## 📄 许可证

本项目使用 [木兰宽松许可证，第2版](./LICENSE) 开源。

---

*若从旧版 `nonebot-plugin-slave-market` 迁移，旧数据完全兼容，详见 [PORTING_NOTES.md](./PORTING_NOTES.md)。*
