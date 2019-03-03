import time

import MySQLdb as mdb
import numpy as np
import pandas as pd


# cur = self.conn.cursor()



class DataManager():
    '''
    General Data Interface for localhost MySQL Database
    ---------------------------------------------------
    '''
    FACTOR_DICT = {}

    def __init__(self, asset_type='stock'):
        if asset_type in ['stock', 's']:
            database = 'stock'
        elif asset_type in ['option', 'o']:
            database = 'option'
        self.conn = mdb.connect(
            host='localhost', port=3306, 
            user='root', passwd='2451121687', 
            db=database, charset='utf8')
        self.data = [None]

    def __repr__(self, ):
        if len(self.data)==1:
            return "<Empty DataManager>"
        print("Data Collected:")
        for d in range(len(self.data)-1):
            print(d+1, "data length:", len(self.data[d+1]))
        return "<DataManager: {} groups of data collected>".format(len(self.data)-1)

    def clear(self):
        self.data = [None]
    
    def __del__(self):
        self.conn.close()
        del self.conn
        del self.data
        del self

    def execute(self, sql_command):
        data = pd.read_sql(sql_command, self.conn)
        self.data.append(data)
        del data

    def stock_close_day(self, index, start_date, end_date, freq, adjust=-1):
        columns = "trade_date, close, adj_factor"
        table = "daily"
        SQL_code = "ts_code="+"\'"+index + "\'"
        SQL_date = "trade_date between \'"+start_date.strip('-')+"\' and \'" + end_date.strip('-') + "\'"
        SQL = "select {} from {} where {} and {}".format(columns, table, SQL_code, SQL_date)
        
        # print(SQL)
        data = pd.read_sql(SQL, self.conn)
        if len(data.values) == 0:
            print(index, '无相关数据，请检查该时间段内股票是否还未上市，或已退市')
            return -1

        if adjust == 1:  # 后复权
            data['close'] *= data['adj_factor']
        elif adjust == -1:  # 前复权
            maxFactor = data['adj_factor'].max()
            data['close'] *= data['adj_factor'] / maxFactor

        # SQL_price += "AND S_DQ_TRADESTATUS = '交易'"
        data.drop(columns=['adj_factor'], inplace=True)
        data.rename(columns={"trade_date": 'date'}, inplace=True)
        data = data.astype({'date': 'datetime64'})
        data.set_index('date', inplace=True)
        data = data.resample(freq).last().dropna()

        self.data.append(data)
        return data

    def muti_stock_close_day(self, index, start_date, end_date, freq='1D', adjust=-1):
        '''
        index : Iterable objects for stock symbols  
        adjust : 
        - -1: 前复权
        - 0: 不复权
        - 1: 后复权  
        一般回测使用前复权，日内使用不复权
        '''
        len_index = len(index)
        muti_close = pd.DataFrame()

        for i in range(len_index):
            symbol = index[i]
            df = self.stock_close_day(
                symbol, start_date, end_date, freq, adjust=adjust)
            df.columns = [symbol]
            muti_close = muti_close.join(df, how='outer')
            print('\r'+symbol +
                  " close data loaded... ({:.2%})".format((i+1)/len_index), end='')
        print()

        self.data.append(muti_close)
        return muti_close

    def stock_close_factors(self, index, start_date, end_date, factor_list:list):
        columns = ("ts_code, trade_date, close"+", {}"*len(factor_list))#.format(*factor_list)        
        table = "daily"
        SQL_code = "ts_code="+"\'"+index + "\'"
        SQL_date = "trade_date between \'"+start_date.strip('-')+"\' and \'" + end_date.strip('-') + "\'"
        SQL = "select {} from {} where {} and {}".format(columns, table, SQL_code, SQL_date)

        data = pd.read_sql(SQL, self.conn)
        if len(data.values) == 0:
            print(index, '无相关数据，请检查该时间段内股票是否还未上市，或已退市')
            return -1
        return

    def etf_close_day(self, start_date, end_date, freq='D'):
        columns = 'trade_date, close'
        table = '50etf'
        date = "trade_date between \'"+start_date+"\' and \'" + end_date + "\'"
        SQL = "select {} from {} where {}".format(columns, table, date)
        # print(SQL)
        data = pd.read_sql(SQL, self.conn)
        data.rename(columns={"trade_date": 'date'}, inplace=True)
        data = data.astype({'date': 'datetime64'})
        data.set_index('date', inplace=True)
        data = data.resample(freq).last().dropna()
        
        self.data.append(data)
        return data

    def etf_close_min(self, start_date, end_date, freq='5min'):
        columns = 'ddate, sclose'
        table = '50etf_min'
        date = "ddate between \'"+start_date+"\' and \'" + end_date + "\'"
        SQL = "select {} from {} where {}".format(columns, table, date)
        # print(SQL)
        data = pd.read_sql(SQL, self.conn)
        data.rename(columns={"ddate": 'date', 'sclose':'close'}, inplace=True)
        data.set_index('date', inplace=True)
        # 左开右闭区间，最终标签取右区间边界
        data = data.resample(freq, label='right', closed='right').last().dropna()

        self.data.append(data)
        return data

    def etf_option_min(self, code, datetime):
        
        return
    
    def etf_option_day(self, code=None, date=None):
        # code和date必须至少有其一
        if code is None and date is None:
            raise ValueError("At least one argument must be given.")
        elif code is None and date is not None:
            data = self._get_option_by_date(date)
        elif code is not None and date is None:
            data = self._get_option_by_code(code)
        else:
            

        return

    def select_option(self, datetime, underlyingPrice, 
                    exLevel, exType, timeToExpire):
        strike_list = [i*5/100 for i in range(1,60)] + \
            [i*0.1+3 for i in range(20)]                    # 构建一个所有行权价的列表
        strike_list = np.array(strike_list)
        at_the_money = strike_list - underlyingPrice        # 实值虚值程度
        spot_loc = np.abs(at_the_money).argmin()            # 找出'行权价'中和标的价格最接近的

        aim_strike_loc = spot_loc + (exLevel if exType=='C' else -exLevel)

        data = self._get_option_by_date(datetime)



        self.data.append(data)

        return
    def _get_option_by_date(self, date):
        '''
        返回某一天所有的期权
        '''
        columns = "a.ts_code,trade_date,pre_settle,pre_close,open,high,\
            low,close,settle,vol,amount,oi,call_put,exercise_price,maturity_date"
        table = "`50etf_option_daily` a JOIN `50etf_option_info` b on a.ts_code = b.ts_code"
        SQL_date = "trade_date = \'"+date.strip('-')+"\'"
        SQL = "select {} from {} where {}".format(columns, table, SQL_date)
        
        data = pd.read_sql(SQL, self.conn)
        if len(data.values) == 0:
            print(date, '无相关数据，请检查是否为交易时段')
            return -1

        data['trade_day'] = data['maturity_date'] - data['trade_date']
        data['ptmday']=data['trade_day'].apply(lambda x:x.days)
        self.data.append(data)
        return data

    def _get_option_by_code(self, code):
        '''
        返回某一种期权的全部日频记录
        '''
        columns = "a.ts_code,trade_date,pre_settle,pre_close,open,high,\
            low,close,settle,vol,amount,oi,call_put,exercise_price,maturity_date"
        table = "`50etf_option_daily` a JOIN `50etf_option_info` b on a.ts_code = b.ts_code"
        SQL_code = "ts_code="+"\'"+code + "\'"
        SQL = "select {} from {} where {}".format(columns, table, SQL_code)
        
        data = pd.read_sql(SQL, self.conn)
        if len(data.values) == 0:
            print(code, '无相关数据')
            return -1
        # 距离到期的天数
        data['ptmday'] = (data['maturity_date'] - data['trade_date']).apply(lambda x:x.days)
        data.set_index('trade_date')
        self.data.append(data)
        return data

    def _get_option_info(self,):
        return