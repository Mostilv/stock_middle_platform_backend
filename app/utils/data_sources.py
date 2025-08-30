import baostock as bs
import akshare as ak
import pandas as pd
from typing import Optional, Dict, Any
from app.config import settings


class DataSourceManager:
    """数据源管理器"""
    
    def __init__(self):
        self.bs_logged_in = False
    
    def login_baostock(self) -> bool:
        """登录baostock"""
        if not self.bs_logged_in:
            lg = bs.login(settings.baostock_user, settings.baostock_password)
            if lg.error_code == '0':
                self.bs_logged_in = True
                return True
            return False
        return True
    
    def logout_baostock(self):
        """登出baostock"""
        if self.bs_logged_in:
            bs.logout()
            self.bs_logged_in = False
    
    def get_stock_list_bs(self) -> Optional[pd.DataFrame]:
        """获取股票列表（baostock）"""
        if not self.login_baostock():
            return None
        
        rs = bs.query_stock_basic()
        if rs.error_code != '0':
            return None
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        return pd.DataFrame(data_list, columns=rs.fields)
    
    def get_stock_data_bs(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取股票数据（baostock）"""
        if not self.login_baostock():
            return None
        
        rs = bs.query_history_k_data_plus(code,
            "date,code,open,high,low,close,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM",
            start_date=start_date, end_date=end_date,
            frequency="d", adjustflag="3")
        
        if rs.error_code != '0':
            return None
        
        data_list = []
        while (rs.error_code == '0') & rs.next():
            data_list.append(rs.get_row_data())
        
        return pd.DataFrame(data_list, columns=rs.fields)
    
    def get_stock_list_ak(self) -> Optional[pd.DataFrame]:
        """获取股票列表（akshare）"""
        try:
            return ak.stock_info_a_code_name()
        except Exception as e:
            print(f"获取股票列表失败: {e}")
            return None
    
    def get_stock_data_ak(self, code: str, start_date: str, end_date: str) -> Optional[pd.DataFrame]:
        """获取股票数据（akshare）"""
        try:
            return ak.stock_zh_a_hist(symbol=code, start_date=start_date, end_date=end_date, adjust="qfq")
        except Exception as e:
            print(f"获取股票数据失败: {e}")
            return None
    
    def get_stock_realtime_ak(self, code: str) -> Optional[Dict[str, Any]]:
        """获取股票实时数据（akshare）"""
        try:
            data = ak.stock_zh_a_spot_em()
            stock_data = data[data['代码'] == code]
            if not stock_data.empty:
                return stock_data.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"获取实时数据失败: {e}")
            return None
    
    def get_index_data_ak(self, index_code: str) -> Optional[pd.DataFrame]:
        """获取指数数据（akshare）"""
        try:
            return ak.stock_zh_index_daily(symbol=index_code)
        except Exception as e:
            print(f"获取指数数据失败: {e}")
            return None


# 全局数据源管理器实例
data_source_manager = DataSourceManager()
