from typing import List, Optional
from fastapi import APIRouter, Query, HTTPException, status
from app.utils.data_sources import data_source_manager
import pandas as pd

router = APIRouter(prefix="/indicators", tags=["指标展示"])


@router.get("/stocks")
async def get_stock_list(
    source: str = Query("akshare", description="数据源: akshare 或 baostock")
):
    """获取股票列表（无需认证）"""
    try:
        if source == "baostock":
            data = data_source_manager.get_stock_list_bs()
        else:
            data = data_source_manager.get_stock_list_ak()
        
        if data is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="获取股票列表失败"
            )
        
        # 转换为字典格式
        if isinstance(data, pd.DataFrame):
            return {"data": data.to_dict('records'), "total": len(data)}
        return {"data": data, "total": len(data) if data else 0}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取股票列表失败: {str(e)}"
        )


@router.get("/stocks/{stock_code}")
async def get_stock_data(
    stock_code: str,
    start_date: str = Query(..., description="开始日期 (YYYY-MM-DD)"),
    end_date: str = Query(..., description="结束日期 (YYYY-MM-DD)"),
    source: str = Query("akshare", description="数据源: akshare 或 baostock")
):
    """获取股票历史数据（无需认证）"""
    try:
        if source == "baostock":
            data = data_source_manager.get_stock_data_bs(stock_code, start_date, end_date)
        else:
            data = data_source_manager.get_stock_data_ak(stock_code, start_date, end_date)
        
        if data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="股票数据不存在"
            )
        
        return {"data": data.to_dict('records'), "total": len(data)}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取股票数据失败: {str(e)}"
        )


@router.get("/stocks/{stock_code}/realtime")
async def get_stock_realtime(
    stock_code: str
):
    """获取股票实时数据（无需认证）"""
    try:
        data = data_source_manager.get_stock_realtime_ak(stock_code)
        
        if data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="股票实时数据不存在"
            )
        
        return {"data": data}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取股票实时数据失败: {str(e)}"
        )


@router.get("/indices/{index_code}")
async def get_index_data(
    index_code: str,
    start_date: Optional[str] = Query(None, description="开始日期 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="结束日期 (YYYY-MM-DD)")
):
    """获取指数数据（无需认证）"""
    try:
        data = data_source_manager.get_index_data_ak(index_code)
        
        if data is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指数数据不存在"
            )
        
        # 如果指定了日期范围，进行过滤
        if start_date and end_date:
            data = data[(data.index >= start_date) & (data.index <= end_date)]
        
        return {"data": data.to_dict('records'), "total": len(data)}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取指数数据失败: {str(e)}"
        )


@router.get("/market/overview")
async def get_market_overview():
    """获取市场概览（无需认证）"""
    try:
        # 获取主要指数数据
        indices = {
            "sh000001": "上证指数",
            "sz399001": "深证成指",
            "sz399006": "创业板指"
        }
        
        market_data = {}
        for code, name in indices.items():
            try:
                data = data_source_manager.get_index_data_ak(code)
                if data is not None and not data.empty:
                    latest = data.iloc[-1]
                    market_data[code] = {
                        "name": name,
                        "code": code,
                        "latest_price": latest.get('close', 0),
                        "change": latest.get('change', 0),
                        "change_pct": latest.get('pct_chg', 0),
                        "volume": latest.get('volume', 0),
                        "amount": latest.get('amount', 0)
                    }
            except Exception as e:
                print(f"获取指数 {code} 数据失败: {e}")
                continue
        
        return {"data": market_data}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取市场概览失败: {str(e)}"
        )
