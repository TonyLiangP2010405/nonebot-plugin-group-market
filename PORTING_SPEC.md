# Slave-Market 迁移规格文档

## 原项目信息
- **仓库**: https://gitee.com/Tloml-Starry/Slave-Market
- **名称**: 奴隶市场 / 群友市场
- **原框架**: Yunzai-Bot V3
- **目标框架**: NoneBot2 + nonebot-adapter-onebot v11
- **许可证**: Mulan PSL v2

## 原项目文件树

```
Slave-Market/
├── .gitignore
├── LICENSE
├── README.md
├── UPDATE.bat
├── index.js                 # 插件入口，配置管理，插件加载
├── guoba.support.js         # Guoba 配置支持
├── apps/                    # 指令模块
│   ├── help.js              # 帮助指令 (/奴隶帮助 / /nl帮助)
│   ├── work.js              # 打工指令 (/打工 / /一键打工)
│   ├── purchaseSlaves.js    # 购买奴隶 (/购买群友 / /购买奴隶)
│   ├── mySlave.js           # 我的奴隶 (/我的奴隶 / /我的群友)
│   ├── trainSlave.js        # 训练奴隶 (/训练 / /一键训练)
│   ├── slaveArena.js        # 决斗 (/决斗)
│   ├── slaveRanking.js      # 排位赛 (/排位赛 / /参加排位赛)
│   ├── bank.js              # 银行 (/存款 / /取款 / /升级信用 / /银行信息 / /领取利息 / /转账 / /一键存款 / /一键升级信用)
│   ├── rankings.js          # 排行榜 (/奴隶市场 / /排行榜)
│   ├── releaseSlave.js      # 放生奴隶 (/放生奴隶)
│   ├── BuyBackSelf.js       # 回购自己 (/回购自己)
│   ├── Rob.js               # 抢劫 (/抢劫)
│   ├── slaveList.js         # 奴隶列表渲染
│   ├── weeklyReset.js       # 每周重置 (/奴隶重置状态 / /手动奴隶重置 / /奴隶重置帮助 / /上周排行榜)
│   ├── backup.js            # 备份管理
│   ├── exitDeleteArchive.js # 退群删档
│   └── update.js            # 插件更新 (/奴隶更新)
├── function/
│   └── function.js          # 工具函数：数据读写、排行榜、重置逻辑
└── resources/
    ├── psc.png
    ├── data/
    │   └── workCopywriting.json   # 打工文案
    └── html/
        ├── help/
        │   ├── index.html
        │   └── index.css
        ├── rankings/
        │   └── index.html
        ├── slaveList/
        │   └── index.html
        ├── training/
        │   ├── index.html
        │   └── training.css
        └── work/
            └── index.html
```

## 指令清单 (完整)

| 触发词 | 别名/正则 | 权限 | 范围 | 功能 |
|--------|----------|------|------|------|
| `/奴隶帮助` / `/nl帮助` / `/群友帮助` | `[#/]?(奴隶\|nl\|群友)(帮助\|菜单)` | 全员 | 群聊 | 显示帮助图片 |
| `/打工` / `/工作` | `[#/](一键)?(打工\|工作)$` | 全员 | 群聊 | 打工赚取金币 |
| `/购买群友` / `/购买奴隶` | `[#/]购买(群友\|奴隶)(\d+)?` | 全员 | 群聊 | 购买目标为奴隶 |
| `/我的奴隶` / `/我的群友` | `[#/]我的(奴隶\|群友)$` | 全员 | 群聊 | 查看自己的奴隶 |
| `/训练` | `[#/]训练\s*(\d+)?$` | 全员 | 群聊 | 训练指定奴隶 |
| `/一键训练` | `[#/]一键训练$` | 全员 | 群聊 | 一键训练所有奴隶 |
| `/决斗` | `[#/]决斗\s*(\d+)\s*(\d+)$` | 全员 | 群聊 | 让两个奴隶决斗 |
| `/排位赛` | `[#/]排位赛$` | 全员 | 群聊 | 查看排位赛信息 |
| `/参加排位赛` | `[#/]参加排位赛\s*(\d+)$` | 全员 | 群聊 | 参加排位赛 |
| `/存款` | `[#/]存款\s*(\d+)$` | 全员 | 群聊 | 存款到银行 |
| `/一键存款` | `[#/]一键存款\s*(\d+)$` | 全员 | 群聊 | 一键存入所有金币 |
| `/取款` | `[#/]取款\s*(\d+)$` | 全员 | 群聊 | 从银行取款 |
| `/升级信用` | `[#/]升级信用$` | 全员 | 群聊 | 升级银行信用等级 |
| `/一键升级信用` | `[#/]一键升级信用$` | 全员 | 群聊 | 自动连续升级信用 |
| `/银行信息` | `[#/]银行信息$` | 全员 | 群聊 | 查看银行信息 |
| `/领取利息` | `[#/]领取利息$` | 全员 | 群聊 | 领取银行利息 |
| `/转账` | `[#/]转账\s*(\d+)$` | 全员 | 群聊 | 转账给@用户 |
| `/奴隶市场` / `/排行榜` | (rankings.js) | 全员 | 群聊 | 查看排行榜图片 |
| `/放生奴隶` | (releaseSlave.js) | 全员 | 群聊 | 放生奴隶 |
| `/回购自己` | (BuyBackSelf.js) | 全员 | 群聊 | 回购自己 |
| `/抢劫` | (Rob.js) | 全员 | 群聊 | 抢劫 |
| `/奴隶重置状态` | `[#/]奴隶重置状态$` | 全员 | 群聊 | 查看重置状态 |
| `/手动奴隶重置` | `[#/]手动奴隶重置$` | 管理员 | 群聊 | 手动执行每周重置 |
| `/奴隶重置帮助` | `[#/]奴隶重置帮助$` | 全员 | 群聊 | 重置帮助 |
| `/上周排行榜` | `[#/]上周排行榜$` | 全员 | 群聊 | 查看上周排行榜 |
| `/奴隶更新` | `[#/]奴隶更新$` | 全员 | 群聊 | 更新插件 |

## 玩家数据结构

```json
{
    "currency": 0,
    "slave": [],
    "value": 100,
    "lastWorkingTime": 0,
    "master": "",
    "nickname": "",
    "lastPurchaseTime": 0,
    "lastTrainedTime": 0,
    "lastBattleTime": 0,
    "lastRankingTime": 0,
    "lastRobTime": 0,
    "buyBackTimes": 0,
    "lastBuyBackTime": 0,
    "battleStats": {"wins": 0, "losses": 0},
    "bank": {
        "balance": 0,
        "level": 1,
        "limit": 1000,
        "upgradePrice": 100,
        "lastInterestTime": 0
    },
    "ranking": {"score": 1000, "tier": "青铜", "matches": 0},
    "weeklyResets": 0,
    "lastResetTime": 0,
    "lastResetWeek": 0
}
```

## 配置项 (config/SlaveMarket_config.yaml)

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| buyBack.cooldown | int | 86400 | 回购冷却(秒) |
| buyBack.maxTimes | int | 3 | 最大回购次数 |
| buyBack.taxRate | float | 0.05 | 回购税率 |
| rob.cooldown | int | 600 | 抢劫冷却(秒) |
| rob.successRate | float | 0.3 | 抢劫成功率 |
| rob.penalty | float | 0.1 | 抢劫失败惩罚 |
| work.cooldown | int | 3600 | 打工冷却(秒) |
| work.slaveownerCooldown | int | 60 | 奴隶主冷却(秒) |
| purchase.cooldown | int | 3600 | 购买冷却(秒) |
| bank.initialLimit | int | 1000 | 银行初始限额 |
| bank.initialLevel | int | 1 | 银行初始等级 |
| bank.upgradePriceMulti | float | 1.2 | 升级价格倍数 |
| bank.limitIncreaseMulti | float | 1.25 | 限额增长倍数 |
| bank.initialUpgradePrice | int | 100 | 初始升级价格 |
| bank.interestRate | float | 0.01 | 每小时利息率 |
| bank.maxInterestTime | int | 24 | 最大计息时间(小时) |
| training.cooldown | int | 7200 | 训练冷却(秒) |
| training.successRate | float | 0.7 | 训练成功率 |
| training.costRate | float | 0.1 | 训练费用比例 |
| training.valueIncreaseRate | float | 0.2 | 训练成功身价提升比例 |
| arena.cooldown | int | 7200 | 竞技冷却(秒) |
| arena.entryFee | int | 50 | 参赛费用 |
| arena.rewardRate | float | 0.2 | 获胜奖励比例 |
| arena.valueBonus | float | 0.1 | 获胜者身价提升比例 |
| ranking.cooldown | int | 3600 | 排位赛冷却(秒) |
| ranking.baseReward | int | 10 | 基础奖励金币 |
| ranking.winBonus | float | 0.2 | 胜利额外奖励比例 |
| ranking.tierBonus | dict | {...} | 段位额外奖励 |
| transfer.feeRate | float | 0.1 | 转账手续费率 |
| transfer.minAmount | int | 100 | 最低转账金额 |
| weeklyReset.enabled | bool | true | 是否启用每周重置 |
| weeklyReset.resetTime.day | int | 1 | 重置日 (1=周一) |
| weeklyReset.resetTime.hour | int | 0 | 重置小时 |
| weeklyReset.resetTime.minute | int | 0 | 重置分钟 |
| weeklyReset.preserveData.nickname | bool | true | 保留昵称 |
| weeklyReset.preserveData.basicValue | int | 100 | 重置后基础身价 |
| ignoreCDUsers | list | [] | 忽略冷却的用户ID |

## Yunzai → NoneBot2 API 映射

| Yunzai API | NoneBot2 等价实现 |
|------------|-------------------|
| `e.reply([...])` | `await matcher.send()` / `await matcher.finish()` |
| `e.isGroup` | `isinstance(event, GroupMessageEvent)` |
| `e.user_id` | `event.user_id` |
| `e.group_id` | `event.group_id` |
| `e.sender.card / nickname` | 通过 `bot.get_group_member_info()` 获取 |
| `e.at` | 从消息中解析 `@` segment |
| `e.msg` | `event.get_plaintext()` |
| `segment.at(id)` | `MessageSegment.at(id)` |
| `segment.image(url)` | `MessageSegment.image(url)` |
| `Bot.pickGroup(gid).getMemberMap()` | `bot.get_group_member_list()` |
| `plugin` class | `on_command()` / `on_regex()` Matcher |
| `logger` | `from nonebot import logger` |
| `fs.readFileSync` | `aiofiles` 异步读写 |
| 定时任务 | `nonebot-plugin-apscheduler` |
| YAML 配置 | `pydantic-settings` + PyYAML |
| Puppeteer 截图 | `nonebot-plugin-htmlrender` 或 Pillow |

## 数据存储映射

| 原路径 | NoneBot 版路径 |
|--------|---------------|
| `plugins/Slave-Market/data/player/{group_id}/{user_id}.json` | `data/nonebot_plugin_slave_market/player/{group_id}/{user_id}.json` |
| `config/SlaveMarket_config.yaml` | `.env` 或插件配置目录 |
| `plugins/Slave-Market/resources/` | `data/nonebot_plugin_slave_market/resources/` |
| `data/Ts-GameData` | `data/nonebot_plugin_slave_market/` |

## 每周重置规则

1. 触发条件：每周一 00:00 (可配置)
2. 执行内容：
   - 备份所有玩家数据
   - 金币归零
   - 清空奴隶列表和主人关系
   - 身价重置为 `basicValue`
   - 清除所有冷却时间
   - 重置银行数据
   - 重置排位数据
   - 保存上周排行榜历史

## 段位规则

| 段位 | 分数范围 |
|------|----------|
| 青铜 | < 1000 |
| 白银 | 1000-1399 |
| 黄金 | 1400-1799 |
| 铂金 | 1800-2199 |
| 钻石 | ≥ 2200 |
