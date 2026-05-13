# PUBLISHING_AUDIT.md - 发布前审计

## 一、当前项目文件树

```
nonebot-plugin-slave-market/
├─ .github/
│  └─ workflows/
│     └─ pypi-publish.yml
├─ nonebot_plugin_slave_market/
│  ├─ __init__.py
│  ├─ __pycache__/
│  ├─ commands.py
│  ├─ commands_achievement.py
│  ├─ commands_admin.py
│  ├─ commands_arena.py
│  ├─ commands_bank.py
│  ├─ commands_buyback.py
│  ├─ commands_dailytask.py
│  ├─ commands_help.py
│  ├─ commands_level.py
│  ├─ commands_profile.py
│  ├─ commands_purchase.py
│  ├─ commands_randomevent.py
│  ├─ commands_ranking.py
│  ├─ commands_rankings.py
│  ├─ commands_rob.py
│  ├─ commands_season.py
│  ├─ commands_shop.py
│  ├─ commands_signin.py
│  ├─ commands_slave.py
│  ├─ commands_title.py
│  ├─ commands_train.py
│  ├─ commands_update.py
│  ├─ commands_weekly.py
│  ├─ commands_work.py
│  ├─ config.py
│  ├─ exit_handler.py
│  ├─ extension/
│  │  ├─ __init__.py
│  │  ├─ anti_spam.py
│  │  ├─ config.py
│  │  ├─ group_storage.py
│  │  └─ utils.py
│  ├─ storage.py
│  ├─ utils.py
│  ├─ weekly_reset_task.py
├─ dist/                    (构建产物，不应进 git)
├─ nonebot_plugin_slave_market.egg-info/   (构建产物，不应进 git)
├─ .gitignore
├─ LICENSE
├─ PORTING_SPEC.md
├─ pyproject.toml
├─ README.md
├─ test_syntax.py
├─ (其他文档)
```

## 二、当前插件包名

- **PyPI 项目名**: `nonebot-plugin-slave-market`
- **Python 包名**: `nonebot_plugin_slave_market`
- **入口点**: `nonebot_plugin_slave_market = "nonebot_plugin_slave_market"`
- **问题**: 名称包含敏感词 "slave"，不适合公开发布到 NoneBot 商店

## 三、当前 pyproject.toml 状态

| 检查项 | 状态 | 说明 |
|--------|------|------|
| PEP 621 标准 | ✅ | 使用 `[project]` 表 |
| requires-python | ✅ | `>=3.10` |
| license 字段 | ✅ | Mulan PSL v2 |
| readme 字段 | ✅ | README.md |
| authors 字段 | ✅ | Tony |
| keywords | ✅ | 存在 |
| classifiers | ✅ | 存在 |
| dependencies | ✅ | 完整 |
| [tool.nonebot] | ✅ | plugins 已配置 |
| [build-system] | ✅ | setuptools |
| entry-points | ✅ | 已配置 |
| **问题** | ⚠️ | 包名含 "slave"，homepage 指向旧仓库名 |

## 四、当前 README 状态

| 检查项 | 状态 | 说明 |
|--------|------|------|
| 插件名称 | ✅ | 存在 |
| 安装方式 | ⚠️ | 有 pip install，但无 nb-cli 安装说明 |
| 功能列表 | ✅ | 较完整 |
| 使用说明 | ✅ | 有命令列表 |
| 配置说明 | ⚠️ | 仅有简单示例，无完整配置表 |
| NoneBot 商店徽标 | ❌ | 无 |
| PyPI 徽标 | ❌ | 无 |
| Python 版本徽标 | ❌ | 无 |
| License 徽标 | ❌ | 无 |
| 效果图/截图 | ❌ | 无 |
| **问题** | ⚠️ | 风格不统一，缺少模板要求的徽章和格式 |

## 五、当前依赖列表

```
nonebot2>=2.2.0
nonebot-adapter-onebot>=2.0.0
nonebot-plugin-apscheduler>=0.5.0
nonebot-plugin-localstore>=0.7.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
PyYAML>=6.0
aiofiles>=23.0.0
typing-extensions>=4.0.0
```

全部符合 NoneBot2 生态，无不合理依赖。

## 六、当前 __plugin_meta__

```python
__plugin_meta__ = PluginMetadata(
    name="群友市场",
    description="群聊文字游戏插件：购买群友、打工、训练、决斗、排位赛、银行",
    usage="...",
    type="application",
    homepage="...",
    config=None,          # ❌ 应为 Config 类
    supported_adapters={"~onebot.v11"},
)
```

**问题**: `config=None`，NoneBot 商店审核要求 `config=Config`。

## 七、零配置加载检查

- 插件 `__init__.py` 不依赖 `.env` 中的必填配置项。
- `get_plugin_config()` 使用了默认值，零配置可加载。
- ✅ 符合要求。

## 八、本地文件存储

- 使用 `nonebot_plugin_localstore.get_plugin_data_dir()` 获取数据目录。
- 数据存储在 `data/slave_market/` 下。
- ✅ 符合 NoneBot 规范，不污染项目目录。

## 九、同步阻塞操作

- 存储层使用 `asyncio.Lock` + `aiofiles` 未使用（但 open 在 async 函数中用 `with open`）。
- 经检查，所有 `with open()` 调用都在 `async def` 函数内部，且通过锁保护。
- ⚠️ 虽然使用同步 IO，但受文件锁保护且数据量小，在群聊场景下可接受。
- 建议标注为 "轻量级同步 IO"。

## 十、GitHub Actions

- 已有 `.github/workflows/pypi-publish.yml`。
- 触发条件: `on.push.tags: v*`。
- 使用 `secrets.PYPI_API_TOKEN`。
- ✅ 基本可用，但命名和结构可优化为模板标准。

## 十一、PyPI 发布要求

| 检查项 | 状态 |
|--------|------|
| 可构建 wheel | ✅ |
| 可构建 sdist | ✅ |
| 有 LICENSE | ✅ |
| 有 README | ✅ |
| 有 classifiers | ✅ |
| **问题** | 包名需改为中性名称 |

## 十二、距离 NoneBot 商店审核还缺什么

| 缺失项 | 优先级 | 说明 |
|--------|--------|------|
| 包名改为中性名称 | 🔴 高 | "slave" 不适合公开 |
| `config=Config` | 🔴 高 | 商店审核要求 |
| README 按模板重写 | 🔴 高 | 徽章、nb-cli 安装、配置表 |
| CHANGELOG.md | 🟡 中 | 推荐有 |
| tests/ 目录 | 🟡 中 | 至少有一个基础测试 |
| .github/workflows/publish.yml | 🟡 中 | 命名对齐模板 |
| 项目根目录包结构 | 🟡 中 | 插件包应在顶层 |
| models.py | 🟢 低 | 可选，但推荐有数据模型定义 |
| resources/ | 🟢 低 | 可选 |

## 十三、审计结论

**当前插件功能完整、运行稳定，但发布前必须完成：**

1. 重命名为 `nonebot-plugin-group-market` / `nonebot_plugin_group_market`
2. 更新 `__plugin_meta__` 的 `config` 字段
3. 重写 README 为标准模板风格
4. 补充缺失的发布文档
5. 整理项目目录结构
