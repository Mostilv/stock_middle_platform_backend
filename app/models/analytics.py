from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class IndustryMetricPoint(BaseModel):
    date: datetime = Field(..., description="指标对应的交易日（UTC）")
    momentum: Optional[float] = Field(None, description="行业动量指标值")
    width: Optional[float] = Field(None, description="行业宽度指标值")


class IndustryMetricSeries(BaseModel):
    symbol: str = Field(..., description="行业标识，例如 INDUSTRY:801010")
    code: str = Field(..., description="行业代码")
    name: str = Field(..., description="行业中文名称")
    points: List[IndustryMetricPoint] = Field(
        default_factory=list, description="时间序列数据"
    )


class IndustryMetricResponse(BaseModel):
    indicator: str = Field(..., description="指标标识")
    target: str = Field(..., description="数据源目标别名")
    start: datetime = Field(..., description="返回数据的起始时间（UTC）")
    end: datetime = Field(..., description="返回数据的结束时间（UTC）")
    dates: List[str] = Field(default_factory=list, description="去重后的日期标签")
    series: List[IndustryMetricSeries] = Field(
        default_factory=list, description="行业序列集合"
    )
