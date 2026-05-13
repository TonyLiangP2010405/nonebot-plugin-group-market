"""数据模型定义

本文件仅用于文档化和类型提示，运行时实际使用字典存储。
所有字段在 storage.ensure_player() 中自动初始化。
"""
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class BankData(BaseModel):
    balance: int = 0
    level: int = 1
    limit: int = 1000
    upgradePrice: int = 100
    lastInterestTime: int = 0


class RankingData(BaseModel):
    score: int = 1000
    tier: str = "青铜"
    matches: int = 0


class DuelStats(BaseModel):
    wins: int = 0
    losses: int = 0
    total: int = 0


class PlayerData(BaseModel):
    """玩家数据模型（用于文档和 IDE 提示）"""
    currency: int = 0
    slave: List[int] = Field(default_factory=list)
    value: int = 100
    lastWorkingTime: int = 0
    master: str = ""
    nickname: str = ""
    lastPurchaseTime: int = 0
    lastTrainedTime: int = 0
    lastBattleTime: int = 0
    lastRankingTime: int = 0
    lastRobTime: int = 0
    buyBackTimes: int = 0
    lastBuyBackTime: int = 0
    bank: BankData = Field(default_factory=BankData)
    ranking: RankingData = Field(default_factory=RankingData)
    weeklyResets: int = 0
    lastResetTime: int = 0
    lastResetWeek: int = 0
    # 扩展字段
    level: int = 1
    exp: int = 0
    titles: List[str] = Field(default_factory=list)
    equippedTitle: str = ""
    achievements: List[str] = Field(default_factory=list)
    inventory: Dict[str, int] = Field(default_factory=dict)
    dailyTasks: List[Dict] = Field(default_factory=list)
    dailyTaskDate: str = ""
    dailyTaskProgress: Dict = Field(default_factory=dict)
    lastSignInDate: str = ""
    continuousSignInDays: int = 0
    totalSignInDays: int = 0
    workCount: int = 0
    purchaseCount: int = 0
    trainSuccessCount: int = 0
    duelStats: DuelStats = Field(default_factory=DuelStats)
    totalTasksCompleted: int = 0
    claimedRewards: List[str] = Field(default_factory=list)
    profileStats: Dict = Field(default_factory=dict)
