# 迁移说明

## 从 nonebot-plugin-slave-market 迁移

本项目原名为 `nonebot-plugin-slave-market`，包名为 `nonebot_plugin_slave_market`。

### 包名变更

| 项目 | 旧名称 | 新名称 |
|------|--------|--------|
| PyPI 项目名 | `nonebot-plugin-slave-market` | `nonebot-plugin-group-market` |
| Python 包名 | `nonebot_plugin_slave_market` | `nonebot_plugin_group_market` |

### 数据兼容

- **用户数据完全兼容**：数据存储目录保持 `data/slave_market/`，不会丢失任何历史数据。
- **配置兼容**：旧的 `.env` 配置键（如 `slavemarket__work__cooldown`）仍然有效。
- **命令兼容**：所有旧命令（如 `#奴隶帮助`、`#打工` 等）完全保留。

### 安装迁移

```bash
# 卸载旧包
pip uninstall nonebot-plugin-slave-market

# 安装新包
pip install nonebot-plugin-group-market
```

然后在 `pyproject.toml` 中更新：

```toml
[tool.nonebot]
plugins = ["nonebot_plugin_group_market"]
```

### 旧包兼容导入（开发者）

如果你是基于旧包名开发的其他插件，可以通过以下方式兼容：

```python
# 新方式（推荐）
from nonebot_plugin_group_market import plugin_config

# 旧方式仍然可用（通过 shim 兼容）
try:
    from nonebot_plugin_group_market import plugin_config
except ImportError:
    from nonebot_plugin_slave_market import plugin_config
```
