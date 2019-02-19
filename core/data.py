import time

import MySQLdb as mdb
import pandas as pd


# cur = self.conn.cursor()

FACTOR_DICT = {}


class DataManager():
    '''
    General Data Interface for localhost MySQL Database
    ---------------------------------------------------
    '''

    def __init__(self, asset_type='stock'):
        if asset_type in ['stock', 's']:
            database = 'stock'
        elif asset_type in ['option', 'o']:
            database = 'option'
        self.conn = mdb.connect(
            host='localhost', port=3306, 
            user='root', passwd='2451121687', 
            db=database, charset='utf8')
        self.data = None

    def __repr__(self, ):
        return self.data

    def execute(self, sql_command):
        data = pd.read_sql(sql_command, self.conn)
        self.data = data
        del data

    def get_close_day(self, index, start_date, end_date, freq, adjust=-1):

        start_date = start_date.strip('-')
        end_date = end_date.strip('-')
        SQL_code = "ts_code="+"\'"+index + "\'"
        SQL_date = "trade_date between \'"+start_date+"\' and \'" + end_date + "\'"
        SQL = "select trade_date, close, adj_factor from daily where " + \
            SQL_code+' and '+SQL_date
        print(SQL)
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

        return data

    def get_muti_close_day(self, index, start_date, end_date, freq='1D', adjust=-1):
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
            df = self.get_close_day(
                symbol, start_date, end_date, freq, adjust=adjust)
            df.columns = [symbol]
            muti_close = muti_close.join(df, how='outer')
            print('\r'+symbol +
                  " close data loaded... ({:.2%})".format((i+1)/len_index), end='')
        print()

        self.data = muti_close
        return muti_close

    def get_close_factors(self, index, start_date, end_date, factor_list):
        start_date = start_date.strip('-')
        end_date = end_date.strip('-')
        SQL_code = "ts_code="+"\'"+index + "\'"
        SQL_date = "trade_date between \'"+start_date+"\' and \'" + end_date + "\'"

        # factor_list = str(factor_list)
        SQL = ("Select ts_code, trade_date, close" +
               ", {}"*len(factor_list)).format(*factor_list)
        SQL += "where " + SQL_code + SQL_date
        data = pd.read_sql(SQL, self.conn)
        if len(data.values) == 0:
            print(index, '无相关数据，请检查该时间段内股票是否还未上市，或已退市')
            return -1

        return
