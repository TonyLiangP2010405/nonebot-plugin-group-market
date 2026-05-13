"""配置模块"""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from nonebot import get_plugin_config


class BuyBackConfig(BaseModel):
    cooldown: int = Field(default=86400, description="回购冷却时间（秒）")
    maxTimes: int = Field(default=3, description="最大回购次数")
    taxRate: float = Field(default=0.05, description="回购税率")


class RobConfig(BaseModel):
    cooldown: int = Field(default=600, description="抢劫冷却时间（秒）")
    successRate: float = Field(default=0.3, description="抢劫成功率")
    penalty: float = Field(default=0.1, description="抢劫失败惩罚")


class WorkConfig(BaseModel):
    cooldown: int = Field(default=3600, description="打工冷却时间（秒）")
    slaveownerCooldown: int = Field(default=60, description="奴隶主冷却时间（秒）")


class PurchaseConfig(BaseModel):
    cooldown: int = Field(default=3600, description="购买冷却时间（秒）")


class BankConfig(BaseModel):
    initialLimit: int = Field(default=1000, description="初始银行限额")
    initialLevel: int = Field(default=1, description="初始等级")
    upgradePriceMulti: float = Field(default=1.2, description="升级价格倍数")
    limitIncreaseMulti: float = Field(default=1.25, description="限额增长倍数")
    initialUpgradePrice: int = Field(default=100, description="初始升级价格")
    interestRate: float = Field(default=0.01, description="每小时利息率")
    maxInterestTime: int = Field(default=24, description="最大计息时间（小时）")


class TrainingConfig(BaseModel):
    cooldown: int = Field(default=7200, description="训练冷却时间（秒）")
    successRate: float = Field(default=0.7, description="训练成功率")
    costRate: float = Field(default=0.1, description="训练费用比例")
    valueIncreaseRate: float = Field(default=0.2, description="训练成功身价提升比例")


class ArenaConfig(BaseModel):
    cooldown: int = Field(default=7200, description="竞技冷却时间（秒）")
    entryFee: int = Field(default=50, description="参赛费用")
    rewardRate: float = Field(default=0.2, description="获胜奖励比例")
    valueBonus: float = Field(default=0.1, description="获胜者价值提升比例")


class RankingConfig(BaseModel):
    cooldown: int = Field(default=3600, description="排位赛冷却时间（秒）")
    baseReward: int = Field(default=10, description="基础奖励金币")
    winBonus: float = Field(default=0.2, description="胜利额外奖励比例")
    tierBonus: Dict[str, float] = Field(default_factory=lambda: {
        "青铜": 1,
        "白银": 1.2,
        "黄金": 1.5,
        "铂金": 2,
        "钻石": 3
    })


class TransferConfig(BaseModel):
    feeRate: float = Field(default=0.1, description="手续费率")
    minAmount: int = Field(default=100, description="最低转账金额")


class WeeklyResetPreserveConfig(BaseModel):
    nickname: bool = Field(default=True, description="是否保留昵称")
    basicValue: int = Field(default=100, description="重置后的基础身价")


class WeeklyResetTimeConfig(BaseModel):
    day: int = Field(default=1, description="重置日期（1=周一）")
    hour: int = Field(default=0, description="重置小时")
    minute: int = Field(default=0, description="重置分钟")


class WeeklyResetConfig(BaseModel):
    enabled: bool = Field(default=True, description="是否启用每周重置")
    resetTime: WeeklyResetTimeConfig = Field(default_factory=WeeklyResetTimeConfig)
    preserveData: WeeklyResetPreserveConfig = Field(default_factory=WeeklyResetPreserveConfig)


class SlaveMarketConfig(BaseModel):
    """插件主配置"""
    buyBack: BuyBackConfig = Field(default_factory=BuyBackConfig)
    rob: RobConfig = Field(default_factory=RobConfig)
    work: WorkConfig = Field(default_factory=WorkConfig)
    purchase: PurchaseConfig = Field(default_factory=PurchaseConfig)
    bank: BankConfig = Field(default_factory=BankConfig)
    training: TrainingConfig = Field(default_factory=TrainingConfig)
    arena: ArenaConfig = Field(default_factory=ArenaConfig)
    ranking: RankingConfig = Field(default_factory=RankingConfig)
    transfer: TransferConfig = Field(default_factory=TransferConfig)
    weeklyReset: WeeklyResetConfig = Field(default_factory=WeeklyResetConfig)
    ignoreCDUsers: List[str] = Field(default_factory=list, description="忽略冷却的用户ID列表")


plugin_config = get_plugin_config(SlaveMarketConfig)

# 兼容 NoneBot 商店审核的 Config 别名
Config = SlaveMarketConfig
