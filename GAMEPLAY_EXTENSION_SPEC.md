# GAMEPLAY_EXTENSION_SPEC.md - 玩法扩展设计文档

## 概述

在保持原有功能不变的前提下，为 `nonebot-plugin-slave-market` 增加10个扩展模块，提升长期可玩性。

## 模块列表

| 模块 | 文件 | 开关配置 | 命令 |
|------|------|---------|------|
| 签到系统 | commands_signin.py | `signIn.enabled` | #签到 #签到排行 |
| 等级经验 | commands_level.py | `level.enabled` | #我的等级 #等级排行 |
| 成就系统 | commands_achievement.py | `achievement.enabled` | #我的成就 #成就排行 |
| 每日任务 | commands_dailytask.py | `dailyTask.enabled` | #每日任务 #领取任务奖励 #刷新任务 |
| 个人信息 | commands_profile.py | `profile.enabled` | #我的信息 #查看信息 |
| 道具商店 | commands_shop.py | `shop.enabled` | #商店 #购买道具 #我的道具 #使用道具 #赠送道具 |
| 随机事件 | commands_randomevent.py | `randomEvent.enabled` | #今日事件 |
| 称号系统 | commands_title.py | `title.enabled` | #我的称号 #佩戴称号 |
| 悬赏系统 | commands_bounty.py | `bounty.enabled` | #悬赏列表 #发布悬赏 #领取悬赏 #取消悬赏 |
| 赛季系统 | commands_season.py | `season.enabled` | #赛季信息 #赛季排行 #赛季奖励 #历史赛季 |

## 新增数据结构

### 玩家数据扩展字段

```json
{
  "level": 1,
  "exp": 0,
  "titles": [],
  "equippedTitle": "",
  "achievements": [],
  "inventory": {},
  "dailyTasks": [],
  "dailyTaskDate": "",
  "dailyTaskProgress": {},
  "lastSignInDate": "",
  "continuousSignInDays": 0,
  "totalSignInDays": 0,
  "workCount": 0,
  "purchaseCount": 0,
  "trainSuccessCount": 0,
  "duelStats": {"wins": 0, "losses": 0, "total": 0},
  "totalTasksCompleted": 0,
  "claimedRewards": [],
  "profileStats": {}
}
```

### 群级数据 (group_data/{group_id}.json)

```json
{
  "eventDate": "2026-05-13",
  "todayEvent": {"id": "work_boom", "name": "打工热潮", ...},
  "currentSeason": "2026-W20",
  "seasonStats": {"user_id": {...}},
  "seasonHistory": {"2026-W19": {...}},
  "bounties": [{...}]
}
```

## 配置项

所有配置均通过 NoneBot2 的标准配置机制加载，默认启用。

详见 `nonebot_plugin_slave_market/extension/config.py`

## 数据兼容性

- 旧玩家数据自动迁移：`storage.py` 的 `_migrate_player_data()` 会在加载时补全缺失字段
- 每周重置保留扩展字段：`weekly_reset_task.py` 在重置时保留等级、成就、称号等长期数据
- 新字段均有默认值，不会导致旧数据报错
