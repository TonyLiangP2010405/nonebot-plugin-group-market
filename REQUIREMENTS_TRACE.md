# REQUIREMENTS_TRACE.md - 需求追踪

## 文档要求

| 要求 | 状态 | 说明 |
|------|------|------|
| 不允许重写整个插件 | ✅ | 仅新增文件和少量修改 |
| 不允许破坏已有功能 | ✅ | 原有命令逻辑不变，仅增加追踪钩子 |
| 不允许改掉已有命令原始逻辑 | ✅ | 仅增加经验/任务/赛季统计 |
| 新功能必须模块化开发 | ✅ | 10个模块，每个独立文件 |
| 新功能必须有配置开关 | ✅ | extension/config.py 每个模块有 enabled |
| 新功能必须兼容旧数据 | ✅ | storage.py _migrate_player_data |
| 新数据字段必须支持自动初始化 | ✅ | ensure_player + 迁移函数 |
| 数据结构变更必须写迁移逻辑 | ✅ | _migrate_player_data |
| 新增命令必须写入 README 和 COMMAND_MATRIX | ✅ | 已更新 |
| 新增功能必须写入 REQUIREMENTS_TRACE | ✅ | 本文档 |
| 每开发一个模块更新 TASK_STATE | ✅ | 已更新 |
| 不允许出现 TODO/pass/伪代码 | ✅ | 全部实现 |
| 必须保证 NoneBot2 正常加载 | ✅ | py_compile 通过 |

## 模块实现状态

| 模块 | 文件 | 命令 | 数据持久化 | 配置开关 | 测试 |
|------|------|------|-----------|---------|------|
| 签到系统 | commands_signin.py | ✅ | ✅ | ✅ | 语法通过 |
| 等级经验 | commands_level.py | ✅ | ✅ | ✅ | 语法通过 |
| 成就系统 | commands_achievement.py | ✅ | ✅ | ✅ | 语法通过 |
| 每日任务 | commands_dailytask.py | ✅ | ✅ | ✅ | 语法通过 |
| 个人信息 | commands_profile.py | ✅ | ✅ | ✅ | 语法通过 |
| 道具商店 | commands_shop.py | ✅ | ✅ | ✅ | 语法通过 |
| 随机事件 | commands_randomevent.py | ✅ | ✅ | ✅ | 语法通过 |
| 称号系统 | commands_title.py | ✅ | ✅ | ✅ | 语法通过 |
| 悬赏系统 | commands_bounty.py | ✅ | ✅ | ✅ | 语法通过 |
| 赛季系统 | commands_season.py | ✅ | ✅ | ✅ | 语法通过 |

## 已有命令增强

| 命令 | 经验追踪 | 任务进度 | 赛季统计 |
|------|---------|---------|---------|
| #打工 | ✅ | ✅ | ✅ |
| #购买群友 | ✅ | ✅ | ✅ |
| #训练 | ✅ | ✅ | ✅ |
| #决斗 | ✅ | ✅ | ✅ |
| #参加排位赛 | ✅ | ✅ | ✅ |
