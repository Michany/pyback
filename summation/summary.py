import pandas as pd
from ..core.backtest import Record, BackTest
from .plot import _autocorrelation_graph, _generate_profit_curve


class Summary():
    def __init__(self, backtest: BackTest):

        self._data_dict = backtest.info
        self.timeIndex = self._data_dict['timeIndex']
        self.assetCapacity = self._data_dict['assetCapacity']
        self.totalCapital = self._data_dict['totalCapital'][1:]
        self.cash = self._data_dict['cash'][1:]
        self.balance = self._data_dict['balance'].reshape(
            (-1, self.assetCapacity))[1:]
        self.share = self._data_dict['share'].reshape(
            (-1, self.assetCapacity))[1:]
        self.position = self._data_dict['position'].reshape(
            (-1, self.assetCapacity))[1:]
        self.pnl = self._data_dict['pnl'].reshape(
            (-1, self.assetCapacity))[1:]
        self.sum_pnl = self.pnl.sum(axis=1)
        self.sum_pct = self.pnl.sum(axis=1)/self.totalCapital
        self.netValue = self.totalCapital / self.totalCapital[0]

        # 数据频率（以天为单位）的获取、计算; 也可以手动指定
        if self.timeIndex.freq is None:
            self._frequency = (self.timeIndex[1]-self.timeIndex[0]).days
            pass
        else:
            self._frequency = self.timeIndex.freq.delta.days
        if self._frequency >= 1:    # 日频及以下：用每年252个交易日来算
            self._T = 252/self.frequency
        else:                       # 分钟频及以上：用每年252/4天有效交易时间
            self._T = 42/self.frequency

        del self._data_dict

    @property
    def frequency(self):
        return self._frequency

    @frequency.setter
    def frequency(self, str_freq: str):
        freq = pd.tseries.frequencies.to_offset(str_freq)
        freq = freq.delta.days
        self._frequency = freq
        if self._frequency >= 1:    # 日频及以下：用每年252个交易日来算
            self._T = 252/self.frequency
        else:                       # 分钟频及以上：用每年252/4天有效交易时间
            self._T = 42/self.frequency

    @property
    def yearlyReturn(self):
        return self.sum_pct.mean()*self._T

    @property
    def yearlyReturnStd(self):
        return self.sum_pct.std()*self._T**0.5

    @property
    def maxDrawdown(self):
        '''
        计算内容：最大回撤比例，累计收益率  
        计算方式：单利  
        返回结果：最大回撤率，开始日期，结束日期，总收益率，年化收益，年化回撤  
        '''
        t = pd.DataFrame(self.netValue, columns=['NAV'], index=self.timeIndex)
        t['Date/Time'] = t.index.copy()
        t['Year'] = t.index.year
        return self._max_drawdown(t)

    @property
    def maxDrawdownYearly(self):
        t = pd.DataFrame(self.netValue, columns=['NAV'], index=self.timeIndex)
        t['Date/Time'] = t.index.copy()
        t['Year'] = t.index.year
        yearly_drawdown = dict()
        t_group = t.groupby('Year')
        for year in t_group.groups:
            t_year = t_group.get_group(year)
            yearly_drawdown[year] = self._max_drawdown(t_year)
        return yearly_drawdown

    def _max_drawdown(self, t):
        '''
        return max_draw_down, start_date, end_date
        '''
        max_draw_down, temp_max_value = 0, t['NAV'].iloc[0]
        start_date, end_date, current_start_date = 0, 0, 0
        continous = False  # 是否连续

        for i in t.index:
            if temp_max_value < t['NAV'][i]:
                current_start_date = t['Date/Time'][i]
                temp_max_value = max(temp_max_value, t['NAV'][i])
                continous = False
            else:
                if max_draw_down > t['NAV'][i]/temp_max_value-1:
                    if not continous:
                        continous = True
                    max_draw_down = t['NAV'][i]/temp_max_value-1
                else:
                    if continous:
                        continous = False
                        start_date = current_start_date
                        end_date = t['Date/Time'][i]

        return max_draw_down, start_date, end_date

    @property
    def sharpe(self):

        return self.yearlyReturn/self.yearlyReturnStd

    @property
    def info(self):
        print("[annualReturn]  年化收益\t{:.2%}".format(self.yearlyReturn))
        print("[st.deviation]  标准差\t{:.2%}".format(self.yearlyReturnStd))
        print("[sharpe raito]  夏普比率\t{:.2f}".format(self.sharpe))
        print("[max drawdown]  最大回撤\t{:.2%}".format(self.maxDrawdown[0]))

    def to_frame(self, columns=None):
        totalCapital = pd.DataFrame(self.totalCapital)
        cash = pd.DataFrame(self.cash)
        balance = pd.DataFrame(self.balance)
        share = pd.DataFrame(self.share)
        position = pd.DataFrame(self.position)
        pnl = pd.DataFrame(self.pnl)
        sum_pnl = pd.DataFrame(self.sum_pnl)
        sum_pct = pd.DataFrame(self.sum_pct)
        nav = pd.DataFrame(self.netValue)

        if columns is None:
            columns = range(1, self.assetCapacity+1)
            
        for df in [totalCapital, cash, balance, share, position, pnl, sum_pnl, sum_pct, nav]:
            df.index = self.timeIndex
        for df in [balance, share, position, pnl]:
            df.columns = columns
        return totalCapital, cash, balance, share, position, pnl, sum_pnl, sum_pct, nav

    def plot(self, kind='nav+pnl', fig_size=None):
        '''
        Parameters
        ----------
        kind : 绘图类型
            'nav+pnl' : 上方净值曲线，下方盈亏  
            'ac' : 自相关系数（平稳性检验）  
        '''
        if kind == 'nav+pnl':
            if fig_size is None:
                fig_size = (15, 10)
            self.profit_curve_with_pnl(fig_size=fig_size)
        elif kind == 'ac':
            if fig_size is None:
                fig_size = (8, 6)
            self.autocorelation_graph(fig_size=fig_size)

    def profit_curve_with_pnl(self, fig_size):
        _generate_profit_curve(self.timeIndex, self.netValue, self.sum_pnl, fig_size)

    def autocorelation_graph(self, fig_size):
        _autocorrelation_graph(self.timeIndex, self.netValue, fig_size)
