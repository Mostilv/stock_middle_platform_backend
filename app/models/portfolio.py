from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from bson import ObjectId


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# 持仓明细
class Position(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    quantity: int = Field(..., description="持仓数量")
    avg_cost: float = Field(..., description="平均成本")
    current_price: float = Field(..., description="当前价格")
    market_value: float = Field(..., description="市值")
    weight: float = Field(..., description="权重")
    pnl: float = Field(..., description="盈亏")
    pnl_ratio: float = Field(..., description="盈亏比例")


# 调仓记录
class PortfolioAdjustment(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    strategy_id: str = Field(..., description="策略ID")
    strategy_name: str = Field(..., description="策略名称")
    user_id: int = Field(..., description="用户ID")
    adjustment_date: datetime = Field(..., description="调仓日期")
    adjustment_type: str = Field(..., description="调仓类型：rebalance/stock_pick/risk_control")
    
    # 调仓前持仓
    before_positions: List[Position] = Field(default_factory=list, description="调仓前持仓")
    before_total_value: float = Field(..., description="调仓前总市值")
    before_cash: float = Field(..., description="调仓前现金")
    
    # 调仓后持仓
    after_positions: List[Position] = Field(default_factory=list, description="调仓后持仓")
    after_total_value: float = Field(..., description="调仓后总市值")
    after_cash: float = Field(..., description="调仓后现金")
    
    # 调仓操作
    buy_orders: List[Dict[str, Any]] = Field(default_factory=list, description="买入订单")
    sell_orders: List[Dict[str, Any]] = Field(default_factory=list, description="卖出订单")
    
    # 调仓原因和备注
    reason: str = Field(..., description="调仓原因")
    notes: Optional[str] = Field(None, description="备注")
    
    # 风控信息
    risk_metrics: Dict[str, Any] = Field(default_factory=dict, description="风控指标")
    
    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


# 调仓记录创建模型
class PortfolioAdjustmentCreate(BaseModel):
    strategy_id: str
    strategy_name: str
    user_id: int
    adjustment_date: datetime
    adjustment_type: str
    before_positions: List[Position]
    before_total_value: float
    before_cash: float
    after_positions: List[Position]
    after_total_value: float
    after_cash: float
    buy_orders: List[Dict[str, Any]] = []
    sell_orders: List[Dict[str, Any]] = []
    reason: str
    notes: Optional[str] = None
    risk_metrics: Dict[str, Any] = {}


# 调仓记录更新模型
class PortfolioAdjustmentUpdate(BaseModel):
    notes: Optional[str] = None
    risk_metrics: Optional[Dict[str, Any]] = None


# 调仓记录响应模型
class PortfolioAdjustmentResponse(BaseModel):
    id: str
    strategy_id: str
    strategy_name: str
    user_id: int
    adjustment_date: datetime
    adjustment_type: str
    before_positions: List[Position]
    before_total_value: float
    before_cash: float
    after_positions: List[Position]
    after_total_value: float
    after_cash: float
    buy_orders: List[Dict[str, Any]]
    sell_orders: List[Dict[str, Any]]
    reason: str
    notes: Optional[str]
    risk_metrics: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


# 持仓快照
class PortfolioSnapshot(BaseModel):
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    strategy_id: str = Field(..., description="策略ID")
    user_id: int = Field(..., description="用户ID")
    snapshot_date: datetime = Field(..., description="快照日期")
    positions: List[Position] = Field(default_factory=list, description="持仓明细")
    total_value: float = Field(..., description="总市值")
    cash: float = Field(..., description="现金")
    total_assets: float = Field(..., description="总资产")
    daily_pnl: float = Field(..., description="日盈亏")
    daily_pnl_ratio: float = Field(..., description="日盈亏比例")
    created_at: datetime = Field(default_factory=datetime.now)
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
