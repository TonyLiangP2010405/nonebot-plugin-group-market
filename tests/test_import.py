"""基础导入测试"""
import sys
from pathlib import Path

# 将项目根目录加入路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def test_package_import():
    """测试插件包能否被导入"""
    import nonebot_plugin_group_market
    assert nonebot_plugin_group_market is not None


def test_config_import():
    """测试配置模块能否被导入"""
    from nonebot_plugin_group_market.config import Config, SlaveMarketConfig
    assert Config is not None
    assert Config is SlaveMarketConfig


def test_storage_import():
    """测试存储模块能否被导入"""
    from nonebot_plugin_group_market.storage import ensure_player, save_player, load_player
    assert ensure_player is not None


def test_extension_import():
    """测试扩展模块能否被导入"""
    from nonebot_plugin_group_market.extension.config import ext_config
    from nonebot_plugin_group_market.extension.anti_spam import check_cooldown
    assert ext_config is not None
    assert check_cooldown is not None


def test_utils_import():
    """测试工具模块能否被导入"""
    from nonebot_plugin_group_market.utils import get_member_nickname, check_permission
    assert get_member_nickname is not None
