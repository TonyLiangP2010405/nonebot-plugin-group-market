# 发布检查清单

## NoneBot 商店审核要求

- [x] 插件包名符合规范（`nonebot-plugin-xxx`）
- [x] Python 包名符合规范（`nonebot_plugin_xxx`）
- [x] `__plugin_meta__` 已定义
- [x] `__plugin_meta__.config` 指向 Config 类
- [x] `__plugin_meta__.type` 为 `"application"`
- [x] `__plugin_meta__.supported_adapters` 已指定
- [x] 使用 `get_plugin_config()` 读取配置
- [x] 零配置可加载（所有配置有默认值）
- [x] 不依赖旧式 bot.py
- [x] 不阻塞 NoneBot 启动
- [x] 资源文件正确打包
- [x] 测试文件不会被运行时加载

## PyPI 发布要求

- [x] `pyproject.toml` 符合 PEP 621
- [x] `license` 字段正确
- [x] `readme` 字段正确
- [x] `requires-python` 已指定
- [x] `[project.entry-points."nonebot.plugin"]` 已配置
- [x] `[tool.nonebot]` 已配置
- [x] `.github/workflows/publish.yml` 已配置
- [x] `PYPI_API_TOKEN` Secret 已配置
- [x] 可构建 wheel
- [x] 可构建 sdist

## GitHub 仓库要求

- [x] LICENSE 文件存在
- [x] README.md 存在
- [x] .gitignore 存在
- [x] GitHub Actions 工作流存在

## 质量检查

- [x] py_compile 语法检查通过
- [x] 所有导入路径正确
- [x] 无 TODO / pass / 伪代码
- [x] 旧数据兼容
- [x] 旧命令兼容
- [x] 文档完整
