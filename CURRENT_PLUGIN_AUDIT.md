# CURRENT_PLUGIN_AUDIT.md - 当前插件审计

## 项目基本信息

- **名称**: nonebot-plugin-slave-market
- **版本**: 0.1.0
- **路径**: `C:\Users\tghrt\Documents\nonebot-plugin-slave-market\`
- **GitHub**: https://github.com/TonyLiangP2010405/nonebot-plugin-slave-market
- **PyPI**: https://pypi.org/project/nonebot-plugin-slave-market/0.1.0/

## 文件结构

```
nonebot_plugin_slave_market/
  __init__.py          - 插件入口，加载配置、存储、定时任务
  config.py            - Pydantic 配置模型（12个配置类）
  storage.py           - JSON 文件存储，群隔离，文件锁
  utils.py             - 通用工具（昵称获取、权限检查、周数计算）
  commands.py          - 指令入口，导入所有子模块触发注册
  commands_help.py     - /奴隶帮助
  commands_work.py     - /打工 / /一键打工
  commands_purchase.py - /购买群友
  commands_slave.py    - /我的奴隶 / /放生奴隶
  commands_train.py    - /训练 / /一键训练
  commands_arena.py    - /决斗
  commands_ranking.py  - /排位赛 / /参加排位赛
  commands_rankings.py - /奴隶市场 / /排行榜
  commands_bank.py     - /存款 /取款 /升级信用 /银行信息 /领取利息 /转账
  commands_rob.py      - /抢劫
  commands_buyback.py  - /回购自己
  commands_weekly.py   - /奴隶重置状态 /手动奴隶重置 /奴隶重置帮助 /上周排行榜
  commands_update.py   - (空壳/更新指令)
  exit_handler.py      - (空壳/退出处理)
  weekly_reset_task.py - 每周重置定时任务
```

## 数据模型

### 玩家数据结构 (storage.py ensure_player)

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
  "bank": {"balance": 0, "level": 1, "limit": 1000, "upgradePrice": 100, "lastInterestTime": 0},
  "ranking": {"score": 1000, "tier": "青铜", "matches": 0},
  "weeklyResets": 0,
  "lastResetTime": 0,
  "lastResetWeek": 0
}
```

## 配置模型

| 配置类 | 字段 |
|--------|------|
| BuyBackConfig | cooldown, maxTimes, taxRate |
| RobConfig | cooldown, successRate, penalty |
| WorkConfig | cooldown, slaveownerCooldown |
| PurchaseConfig | cooldown |
| BankConfig | initialLimit, initialLevel, upgradePriceMulti, limitIncreaseMulti, initialUpgradePrice, interestRate, maxInterestTime |
| TrainingConfig | cooldown, successRate, costRate, valueIncreaseRate |
| ArenaConfig | cooldown, entryFee, rewardRate, valueBonus |
| RankingConfig | cooldown, baseReward, winBonus, tierBonus |
| TransferConfig | feeRate, minAmount |
| WeeklyResetPreserveConfig | nickname, basicValue |
| WeeklyResetTimeConfig | day, hour, minute |
| WeeklyResetConfig | enabled, resetTime, preserveData |
| SlaveMarketConfig | 聚合所有配置 + ignoreCDUsers |

## 已有指令清单

| 指令 | 别名 | 文件 |
|------|------|------|
| /奴隶帮助 | nl帮助, 群友帮助, 奴隶菜单, nl菜单 | commands_help.py |
| /打工 | 工作, 一键打工 | commands_work.py |
| /购买群友 | 购买奴隶 | commands_purchase.py |
| /我的奴隶 | 我的群友 | commands_slave.py |
| /放生奴隶 | - | commands_slave.py |
| /训练 | 一键训练 | commands_train.py |
| /决斗 | - | commands_arena.py |
| /排位赛 | - | commands_ranking.py |
| /参加排位赛 | 参加排位 | commands_ranking.py |
| /存款 | 一键存款 | commands_bank.py |
| /取款 | - | commands_bank.py |
| /升级信用 | 一键升级信用 | commands_bank.py |
| /银行信息 | - | commands_bank.py |
| /领取利息 | - | commands_bank.py |
| /转账 | - | commands_bank.py |
| /奴隶市场 | 排行榜 | commands_rankings.py |
| /回购自己 | - | commands_buyback.py |
| /抢劫 | rob | commands_rob.py |
| /奴隶重置状态 | - | commands_weekly.py |
| /手动奴隶重置 | - | commands_weekly.py |
| /奴隶重置帮助 | - | commands_weekly.py |
| /上周排行榜 | - | commands_weekly.py |

## 每周重置逻辑

- 自动重置：cron 定时，周X HH:MM
- 重置内容：金币归零、清空奴隶关系、身价重置、银行重置、排位重置
- 保留：昵称（可选）、基础身价（可配置）
- 历史保存：保存上周排行榜到 ranking_history/

## 关键注意事项

1. **数据兼容性**: 所有旧玩家缺少扩展字段，需要自动补全
2. **群隔离**: 所有数据按 group_id / user_id 分目录存储
3. **文件锁**: storage.py 使用 asyncio.Lock 字典做文件级锁
4. **冷却检查**: check_permission 让 SUPERUSER 和 ignoreCDUsers 跳过冷却
5. **每周重置**: 会清空大部分数据（但已有周数/重置次数统计）
