# nonebot-plugin-slave-market

群友市场 / 奴隶市场 - NoneBot2 群聊文字游戏插件

从 Yunzai-Bot V3 插件 [Slave-Market](https://gitee.com/Tloml-Starry/Slave-Market) 移植而来。

## 功能

- 💰 打工赚取金币
- 🧑‍🌾 购买/放生群友作为奴隶
- ⚔️ 训练、决斗奴隶
- 🏆 排位赛系统
- 🏦 银行系统（存款/取款/升级/利息/转账）
- 📊 排行榜
- 🔄 每周自动重置

## 安装

```bash
pip install nonebot-plugin-slave-market
```

## 使用

在群聊中发送以下指令：

| 指令 | 说明 |
|------|------|
| #奴隶帮助 | 查看帮助 |
| #打工 / #工作 | 打工赚取金币 |
| #购买群友 @用户 | 购买奴隶 |
| #我的奴隶 | 查看奴隶信息 |
| #训练 @用户 | 训练奴隶 |
| #一键训练 | 训练所有奴隶 |
| #决斗 @用户1 @用户2 | 奴隶决斗 |
| #排位赛 | 查看排位信息 |
| #参加排位赛 @用户 | 参加排位 |
| #存款 数量 | 银行存款 |
| #取款 数量 | 银行取款 |
| #升级信用 | 升级银行等级 |
| #银行信息 | 查看银行 |
| #领取利息 | 领取利息 |
| #转账 数量 @用户 | 转账 |
| #奴隶市场 / #排行榜 | 排行榜 |
| #回购自己 | 从主人处回购 |
| #抢劫 @用户 | 抢劫金币 |

## 配置

在 `.env` 文件中：

```env
slavemarket__work__cooldown=3600
slavemarket__purchase__cooldown=3600
slavemarket__bank__initialLimit=1000
slavemarket__weeklyReset__enabled=true
```

## License

Mulan PSL v2
