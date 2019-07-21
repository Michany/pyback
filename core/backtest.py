import time
import warnings

import numpy as np
import pandas as pd

from .func import vfillna, vstandardizeDealAmount, progress_pretty_print

COUNT = 0


class Record():
    '''
    Record - Class Basis
    --------------------
    A class containing a single row of record.
    '''

    def __init__(self, capital, assetCapacity=100):
        '''
        assetCapacity: 最大资产数目
        '''
        self.totalCapital = np.array([capital, ])
        self.cash = np.array([capital, ])
        self.assetCapacity = assetCapacity
        self.asset = pd.Series(index=range(self.assetCapacity))
        self.balance = np.zeros(shape=(self.assetCapacity))
        self.position = np.zeros(shape=(self.assetCapacity))
        self.share = np.zeros(shape=(self.assetCapacity))


class BackTest(Record):
    '''The core class for the whole backtest.

    Parameters
    ----------
    capital : initial capital of the backtest.  
        If the initial capital is too low, standardization process may cause
        unexpected outcomes.
    assetCapacity : number of the kinds of all available assets.
    timeIndex : the time-series-alike index for final results.
    batch : whether or not should pyback use batch method to accelerate the process.  
        The default value is `True` (Highly recommended), with `batch_size=250`.
    batch_size : the size of each batch. 
    compound : the length of the cycle that pyback use to compound interest.
        Meanings:
            0 : do not use compound returns.
            int > 0 : compound returns by every `compound` records.
        This value is 0 by default.

    Examples
    --------
    >>> test = pyback.BackTest(1e7, 300, price.index)
    '''

    def __init__(self, capital, assetCapacity, timeIndex=None, 
                 batch=True, batch_size=250, compound=0, **karg):
        '''
        输入参数timeIndex推荐使用pd.Series，因为自行创建的时间序列很可能包含了非交易时间段。
        '''
        super().__init__(capital, assetCapacity=assetCapacity)

        if timeIndex is None:
            print(
                "[Warning] No time index data available, please input it while running loops.")
            self.timeIndex = None
        elif isinstance(timeIndex, pd.DatetimeIndex):
            self.timeIndex = timeIndex
        elif isinstance(timeIndex, str):
            start, end, freq = timeIndex.split(':')
            self.timeIndex = pd.date_range(start=start, end=end, freq=freq)
        else:
            raise KeyError("Inappropriate time index input!")

        self.initialCapital = capital
        self.pnl = np.zeros(shape=(self.assetCapacity))
        self.subTest = []

        self.PARAMETERS = dict()
        self.PARAMETERS['batch'] = batch
        self.PARAMETERS['batch_size'] = batch_size
        if compound<0 or not isinstance(compound, int):
            raise ValueError("Compound cycle should be a positive integer.")
        self.PARAMETERS['compound'] = compound


    @property
    def info(self):
        return dict(timeIndex=self.timeIndex, assetCapacity=self.assetCapacity,
                    totalCapital=self.totalCapital, balance=self.balance,
                    share=self.share, position=self.position,
                    cash=self.cash, pnl=self.pnl, 
                    )

    def _addRecord(self, new_account: Record):

        self.position = np.append(self.position, new_account.position)
        self.share = np.append(self.share, new_account.share)
        self.balance[-self.assetCapacity:] = new_account.balance
        self.totalCapital[-1] = new_account.totalCapital
        self.cash = np.append(self.cash, new_account.cash)
        if (self.PARAMETERS['batch'] and len(self.totalCapital) >= self.PARAMETERS['batch_size']):
            self._batching()

    def _batching(self):
        # 加快拼接的速度
        # 把原有的记录保存
        self.subTest.append(self.info)
        # 将原有记录清空至只剩一条
        self.totalCapital = self.totalCapital[-1:]
        self.position = self.position[-self.assetCapacity:]
        self.share = self.share[-self.assetCapacity:]
        self.balance = self.balance[-self.assetCapacity:]
        self.cash = self.cash[-1:]
        self.pnl = self.pnl[-self.assetCapacity:]

    def _pack_batches(self):
        # 把self.subTest中的记录和现有记录拼合

        for batch_data in reversed(self.subTest):
            self.totalCapital = np.append(
                batch_data['totalCapital'][:-1], self.totalCapital)
            self.position = np.append(
                batch_data['position'][:-self.assetCapacity], self.position)
            self.share = np.append(
                batch_data['share'][:-self.assetCapacity], self.share)
            self.balance = np.append(
                batch_data['balance'][:-self.assetCapacity], self.balance)
            self.cash = np.append(
                batch_data['cash'][:-1], self.cash)
            self.pnl = np.append(
                batch_data['pnl'][:-self.assetCapacity], self.pnl)
        # del self.subTest

    def _inputExamination(self, to, price):

        if len(price) != self.assetCapacity:
            raise ValueError("Length not match! Required length is {}, \
                input length is {}".format(self.assetCapacity, len(price)))

        if abs(to.sum()) > 1+1e5:
            raise ValueError(
                "The sum of the total position can not exceed 100%")

        if len(to) != self.assetCapacity:
            raise ValueError("Length not match! Required length is {},\
                input length is {}".format(self.assetCapacity, len(to)))


    def _updateHoldings(self, new_price: np.ndarray):
        target = self.share[-self.assetCapacity:] * new_price
        self.pnl = np.append(self.pnl, target -
                             self.balance[-self.assetCapacity:])
        self.balance = np.append(self.balance, target)
        self.totalCapital = np.append(
            self.totalCapital, self.balance[-self.assetCapacity:].sum() + self.cash[-1])
        return

    def updateStatus(self, verbose=True):
        '''更新每一轮的状态/回测进度

        Examples
        --------
        >>> test.updateStatus()
        '''
        global COUNT, t0

        if COUNT == 0:
            t0 = time.time()

        COUNT += 1
        if self.PARAMETERS['compound']>0:
            self._compound_returns(COUNT)

        progress = COUNT/len(self.timeIndex)

        if verbose:
            progress_pretty_print(progress)

        # Not robust enough: if timeIndex < actual index then 
        # this will never be executed
        if progress >= 1:
            print("do final work")
            self._final_work()

    def _compound_returns(self, count):
        if count % self.PARAMETERS['compound'] == 0:
            self.initialCapital = self.totalCapital[-1]

    def _final_work(self):
        global COUNT, t0
        COUNT = 0
        self._pack_batches()
        print("\n[Time Elapsed] {:.2f}s".format(time.time()-t0))

    def __del__(self):
        global COUNT
        COUNT = 0
        del self


class StockBackTest(BackTest):
    '''The class for stock backtest
    '''

    def __init__(self, capital, assetCapacity, timeIndex=None, 
                 batch=True, batch_size=250, compound=0, **karg):
        super().__init__(capital=capital, assetCapacity=assetCapacity, timeIndex=timeIndex, 
                 batch=batch, batch_size=batch_size, compound=compound, **karg)

        self._factor = dict()


    @property
    def factors(self):
        return self._factor.keys()

    @factors.setter
    def factors(self, factor_data):
        key, value = factor_data
        self._factor[key] = value
    
    @factors.deleter
    def factors(self, key):
        del self._factor[key]

    def __getitem__(self, key):
        try:
            return self._factor[key]
        except:
            raise KeyError("Factor '%s' not found" % key)

    # def factor(self, factorName:str):
    #     return self._factor.get(factorName, None)

    def adjustPosition(self, to, price):
        '''Adjust the postion directly to a target.
        Often used when there are many kinds of assets (e.g. Index Enhancement)  
        直接将仓位调整到目标状态，用于资产数量较多时（例如做股票指数增强）。

        If the target postion is not 100% full, the rest capital will be 
        alocated to cash account.  
        如果仓位不满100%，则剩余的放现金。

        Excessive target postion (>100%) will raise an immediate error.  
        如果仓位超过100%，则会立即报错。

        The shares, in reponse to the target postion, 
        will be adjusted to round hundred by default.  
        默认将仓位调整到整百股数。

        Parameters
        ----------
        to : the target postion.  
        price : the price data.
            The price data must be congruent with the target position.
            Please double check if the target postion data contains 
            price data in the future.

        Examples
        --------
        ```
        >>> for day in pos.index:
        >>>     test.adjustPosition(to, price)
        >>>     test.updateStatus()
        ```
        '''
        warnings.simplefilter("ignore")

        self._inputExamination(to, price)
        self._updateHoldings(price)  # 用新一个tick的数据更新已有仓位的收益信息

        # 如果现有总资产少于initialCapital，则使用现有总资产；否则使用initialCapital
        # initialCapital由_compound_returns()函数负责更新
        if self.totalCapital[-1] < self.initialCapital:
            targetShare = self.totalCapital[-1] * to
        else:
            targetShare = self.initialCapital * to

        targetShare /= price
        targetShare = vfillna(targetShare)
        targetShare = vstandardizeDealAmount(targetShare)  # 近似到100股

        targetRecord = Record(self.totalCapital[-1], self.assetCapacity)
        # targetRecord.asset = self.asset
        targetRecord.share = targetShare
        # 可能总和会超过总资本，必须修正！！（用现金账户来作为修正？）
        targetRecord.balance = targetRecord.share * price

        # 新的现金 = 原有总资金 - 现有持仓总金额
        targetRecord.cash = self.balance[-self.assetCapacity:].sum() + \
            self.cash[-1] - targetRecord.balance.sum()
        # 扣掉手续费
        # fee = np.abs(self.balance[-self.assetCapacity:] - targetRecord.balance) * 0.001
        # print(fee.sum())
        # targetRecord.balance -= fee 
        # 新的总资金 = 现有持仓总金额 + 新的现金
        targetRecord.totalCapital = np.dot(
            targetRecord.share, price) + targetRecord.cash #- fee.sum()
        # 新的仓位 = 现有持仓 / 总资金
        targetRecord.position = targetRecord.balance / targetRecord.totalCapital

        self._addRecord(targetRecord)
        return

    def openPosition(self, ratio, price):
        '''
        套利策略开仓
        ----------

        输入两个方向的比例，进行交易。
        '''
        warnings.simplefilter("ignore")

        self._updateHoldings(price)  # 用新一个tick的数据更新已有仓位的收益信息

        # 按照比例
        targetShare = self.initialCapital * ratio

        targetShare /= price
        targetShare = vfillna(targetShare)
        targetShare = vstandardizeDealAmount(targetShare)  # 近似到100股

        targetRecord = Record(self.totalCapital[-1], self.assetCapacity)
        targetRecord.share

        self.balance
        return

    def closePosition(self, price):
        '''
        套利策略平仓
        ----------

        将仓位平掉
        '''
        self.balance
        return

    # def factorRecord(self, factorName, values, timeStamp=None):
    #     if len(values) != self.assetCapacity:
    #         raise ValueError("Length of factor values does not match!")
    #     self._factor[factorName] = np.append(self._factor.get(
    #         factorName, np.zeros(shape=(self.assetCapacity))), values)

    # def factorsRecord(self, factorNames, factorValues):
    #     '''多个因子一起录入
    #     '''
    #     if len(factorNames)!=len(factorValues):
    #         raise ValueError("Lengths of factor & values does not match!")


    #     for i in range(len(factorNames)):
    #         self.factorRecord(factorNames[i], factorValues[i])


class OptionBackTest(BackTest):
    '''The class for stock backtest
    '''

    def __init__(self, capital, assetCapacity, timeIndex=None, 
                 batch=True, batch_size=250, compound=0, **karg):
        super().__init__(capital=capital, assetCapacity=assetCapacity, timeIndex=timeIndex, 
                 batch=batch, batch_size=batch_size, compound=compound, **karg)


    def adjustPosition(self, to, price):
        '''Adjust the postion directly to a target.
        Often used when there are many kinds of assets (e.g. Index Enhancement)  
        直接将仓位调整到目标状态，用于资产数量较多时（例如做股票指数增强）。

        If the target postion is not 100% full, the rest capital will be 
        alocated to cash account.  
        如果仓位不满100%，则剩余的放现金。

        Excessive target postion (>100%) will raise an immediate error.  
        如果仓位超过100%，则会立即报错。

        The shares, in reponse to the target postion, 
        will be adjusted to round hundred by default.  
        默认将仓位调整到整百股数。

        Parameters
        ----------
        to : the target postion.  
        price : the price data.
            The price data must be congruent with the target position.
            Please double check if the target postion data contains 
            price data in the future.

        Examples
        --------
        ```
        >>> for day in pos.index:
        >>>     test.adjustPosition(to, price)
        >>>     test.updateStatus()
        ```
        '''
        warnings.simplefilter("ignore")

        self._inputExamination(to, price)
        self._updateHoldings(price)  # 用新一个tick的数据更新已有仓位的收益信息

        # 如果现有总资产少于initialCapital，则使用现有总资产；否则使用initialCapital
        # initialCapital由_compound_returns()函数负责更新
        if self.totalCapital[-1] < self.initialCapital:
            targetShare = self.totalCapital[-1] * to
        else:
            targetShare = self.initialCapital * to

        targetShare /= price
        targetShare = vfillna(targetShare)
        targetShare = vstandardizeDealAmount(targetShare)  # 近似到100股

        targetRecord = Record(self.totalCapital[-1], self.assetCapacity)
        # targetRecord.asset = self.asset
        targetRecord.share = targetShare
        # 可能总和会超过总资本，必须修正！！（用现金账户来作为修正？）
        targetRecord.balance = targetRecord.share * price

        # 新的现金 = 原有总资金 - 现有持仓总金额
        targetRecord.cash = self.balance[-self.assetCapacity:].sum() + \
            self.cash[-1] - targetRecord.balance.sum()
        # 扣掉手续费
        # fee = np.abs(self.balance[-self.assetCapacity:] - targetRecord.balance) * 0.001
        # print(fee.sum())
        # targetRecord.balance -= fee 
        # 新的总资金 = 现有持仓总金额 + 新的现金
        targetRecord.totalCapital = np.dot(
            targetRecord.share, price) + targetRecord.cash #- fee.sum()
        # 新的仓位 = 现有持仓 / 总资金
        targetRecord.position = targetRecord.balance / targetRecord.totalCapital

        self._addRecord(targetRecord)
        return

    def openPosition(self, ratio, price):
        '''
        套利策略开仓
        ----------

        输入两个方向的比例，进行交易。
        '''
        warnings.simplefilter("ignore")

        self._updateHoldings(price)  # 用新一个tick的数据更新已有仓位的收益信息

        # 按照比例
        targetShare = self.initialCapital * ratio

        targetShare /= price
        targetShare = vfillna(targetShare)
        targetShare = vstandardizeDealAmount(targetShare)  # 近似到100股

        targetRecord = Record(self.totalCapital[-1], self.assetCapacity)
        targetRecord.share

        self.balance
        return

    def closePosition(self, price):
        '''
        套利策略平仓
        ----------

        将仓位平掉
        '''
        self.balance
        return


