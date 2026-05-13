"""扩展玩法配置"""
from typing import List, Dict
from pydantic import BaseModel, Field
from nonebot import get_plugin_config


class SignInConfig(BaseModel):
    enabled: bool = Field(default=True, description="签到系统开关")
    baseReward: int = Field(default=50, description="基础签到奖励金币")
    continuousBonus: int = Field(default=10, description="连续签到每日递增金币")
    maxContinuousBonus: int = Field(default=200, description="连续签到奖励上限")
    milestone7: Dict[str, int] = Field(default_factory=lambda: {"currency": 200, "exp": 100})
    milestone30: Dict[str, int] = Field(default_factory=lambda: {"currency": 1000, "exp": 500})
    rewardExp: int = Field(default=20, description="签到经验奖励")


class LevelConfig(BaseModel):
    enabled: bool = Field(default=True, description="等级经验系统开关")
    baseExp: int = Field(default=100, description="升到2级所需基础经验")
    expGrowth: float = Field(default=1.3, description="每级经验增长倍数")
    maxLevel: int = Field(default=50, description="等级上限")
    workExp: int = Field(default=10, description="打工获得经验")
    trainExp: int = Field(default=15, description="训练获得经验")
    arenaExp: int = Field(default=20, description="决斗获得经验")
    rankingExp: int = Field(default=25, description="排位赛获得经验")
    purchaseExp: int = Field(default=5, description="购买获得经验")
    taskExpMultiplier: float = Field(default=1.0, description="任务经验倍率")
    workIncomeBonusPerLevel: float = Field(default=0.02, description="每级打工收益加成")
    bankLimitBonusPerLevel: float = Field(default=0.02, description="每级银行限额加成")
    trainSuccessBonusPerLevel: float = Field(default=0.005, description="每级训练成功率加成")


class AchievementConfig(BaseModel):
    enabled: bool = Field(default=True, description="成就系统开关")
    rewardCurrency: int = Field(default=100, description="普通成就奖励金币")
    rewardExp: int = Field(default=50, description="普通成就奖励经验")


class DailyTaskConfig(BaseModel):
    enabled: bool = Field(default=True, description="每日任务系统开关")
    taskCount: int = Field(default=3, description="每天任务数量")
    refreshHour: int = Field(default=0, description="每日刷新小时")
    rewardCurrencyRange: List[int] = Field(default_factory=lambda: [30, 80])
    rewardExpRange: List[int] = Field(default_factory=lambda: [20, 50])
    refreshCost: int = Field(default=50, description="手动刷新费用")


class ShopConfig(BaseModel):
    enabled: bool = Field(default=True, description="商店系统开关")
    items: List[Dict] = Field(default_factory=lambda: [
        {"id": "work_boost", "name": "打工加成卡", "price": 100, "description": "下次打工收益+50%", "maxStack": 5, "usable": True},
        {"id": "train_protect", "name": "训练保护券", "price": 150, "description": "训练失败不掉身价", "maxStack": 3, "usable": True},
        {"id": "arena_shield", "name": "决斗保护盾", "price": 200, "description": "一次决斗失败减少惩罚", "maxStack": 3, "usable": True},
        {"id": "bank_expand", "name": "银行扩容券", "price": 300, "description": "银行限额+500", "maxStack": 5, "usable": True},
        {"id": "task_refresh", "name": "任务刷新券", "price": 80, "description": "免费刷新一次每日任务", "maxStack": 5, "usable": True},
        {"id": "random_box", "name": "随机宝箱", "price": 120, "description": "随机获得金币/经验/道具", "maxStack": 10, "usable": True},
    ])


class RandomEventConfig(BaseModel):
    enabled: bool = Field(default=True, description="随机事件系统开关")
    refreshHour: int = Field(default=0, description="事件刷新小时")
    events: List[Dict] = Field(default_factory=lambda: [
        {"id": "work_boom", "name": "打工热潮", "description": "今天打工收益+20%", "effect": {"workIncome": 0.2}, "weight": 10},
        {"id": "interest_up", "name": "银行加息", "description": "今天银行利息+10%", "effect": {"bankInterest": 0.1}, "weight": 8},
        {"id": "train_boost", "name": "训练吉日", "description": "今天训练成功率+5%", "effect": {"trainSuccess": 0.05}, "weight": 8},
        {"id": "arena_double", "name": "竞技场狂欢", "description": "今天决斗奖励翻倍", "effect": {"arenaReward": 1.0}, "weight": 5},
        {"id": "market_tax_cut", "name": "市场减税", "description": "今天购买税率降低", "effect": {"purchaseTaxCut": 0.05}, "weight": 7},
        {"id": "inflation", "name": "通货膨胀", "description": "今天购买价格上涨20%", "effect": {"purchaseCost": 0.2}, "weight": 6},
        {"id": "market_slump", "name": "市场萧条", "description": "今天打工收益下降10%", "effect": {"workIncome": -0.1}, "weight": 6},
    ])


class TitleConfig(BaseModel):
    enabled: bool = Field(default=True, description="称号系统开关")
    titles: List[Dict] = Field(default_factory=lambda: [
        {"id": "novice", "name": "初入江湖", "source": "默认", "workBonus": 0.0, "rare": False},
        {"id": "rich", "name": "腰缠万贯", "source": "银行存款达10000", "workBonus": 0.02, "rare": False},
        {"id": "duelist", "name": "决斗之王", "source": "累计决斗胜利10次", "workBonus": 0.03, "rare": False},
        {"id": "collector", "name": "奴隶收藏家", "source": "同时拥有5名奴隶", "workBonus": 0.02, "rare": False},
        {"id": "master", "name": "一代宗师", "source": "等级达到20级", "workBonus": 0.05, "rare": True},
        {"id": "legend", "name": "传说", "source": "等级达到50级", "workBonus": 0.08, "rare": True},
        {"id": "early_bird", "name": "早起的鸟儿", "source": "连续签到7天", "workBonus": 0.02, "rare": False},
        {"id": "dedication", "name": "持之以恒", "source": "连续签到30天", "workBonus": 0.04, "rare": True},
    ])


class BountyConfig(BaseModel):
    enabled: bool = Field(default=True, description="悬赏系统开关")
    minAmount: int = Field(default=100, description="最低悬赏金额")
    feeRate: float = Field(default=0.1, description="发布手续费率")
    cancelRefundRate: float = Field(default=0.8, description="取消返还比例")
    maxPerTarget: int = Field(default=5, description="同一目标最大悬赏数")


class SeasonConfig(BaseModel):
    enabled: bool = Field(default=True, description="赛季系统开关")
    mode: str = Field(default="weekly", description="赛季模式 weekly/monthly")
    rewardCurrency: int = Field(default=500, description="基础赛季奖励金币")
    rewardExp: int = Field(default=200, description="基础赛季奖励经验")
    top3Bonus: List[int] = Field(default_factory=lambda: [1000, 600, 300])


class ProfileConfig(BaseModel):
    enabled: bool = Field(default=True, description="个人信息面板开关")


class GameplayExtensionConfig(BaseModel):
    """扩展玩法总配置"""
    signIn: SignInConfig = Field(default_factory=SignInConfig)
    level: LevelConfig = Field(default_factory=LevelConfig)
    achievement: AchievementConfig = Field(default_factory=AchievementConfig)
    dailyTask: DailyTaskConfig = Field(default_factory=DailyTaskConfig)
    shop: ShopConfig = Field(default_factory=ShopConfig)
    randomEvent: RandomEventConfig = Field(default_factory=RandomEventConfig)
    title: TitleConfig = Field(default_factory=TitleConfig)
    bounty: BountyConfig = Field(default_factory=BountyConfig)
    season: SeasonConfig = Field(default_factory=SeasonConfig)
    profile: ProfileConfig = Field(default_factory=ProfileConfig)


ext_config = get_plugin_config(GameplayExtensionConfig)
