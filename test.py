import pyback
import datetime
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import talib
# pylint: disable=E1101,E1103
# pylint: disable=W0212,W0231,W0703,W0622
TODAY = datetime.date.today().strftime('%Y-%m-%d')

# 获取数据


price = pd.read_hdf(r".\PriceData_1123.h5",'price')
dm = pyback.DataManager()
dm.muti_stock_close_day(price.columns, '20060101', '20181231')
price = dm.data[-1]
priceFill = price.fillna(method='ffill')
priceFill2 = priceFill.fillna(0).iloc[:,:]

#%% 
def 仓位计算和优化(arg=30, fast = False):
    global RSI_arg

    RSI_arg = arg
    RSI = priceFill2.apply(talib.RSI, args=(RSI_arg,))

    RSI[price.isna()] = 50
    分母=abs(RSI.T-50).sum()
    RSI_normalized = ((RSI.T-50)/分母).T
    RSI_normalized.fillna(0,inplace=True)
    pos = RSI_normalized[RSI_normalized>0]
    pos[pos.T.sum()<0.4] *= 0.8
    pos[pos.T.sum()<0.3] *= 0.5
    pos[pos.T.sum()>0.6] *= 1.1
    pos[pos.T.sum()>0.7] *= 1.1
    pos[pos.T.sum()>0.8] *= 1.1
    # 将总和超出1的仓位，除以总和，归为1
    pos[pos.T.sum()>1] = pos[pos.T.sum()>1].divide(pos.T.sum()[pos.T.sum()>1],axis=0)
    pos.fillna(0, inplace = True)

    return pos, RSI


posSlow, RSI_Slow = 仓位计算和优化(40)
posFast, RSI_Fast = 仓位计算和优化(10, fast=True)
posSlow[(posSlow.T.sum()<0.50) & (posSlow.T.sum()>0.05)] = posFast
posSlow[(posSlow.T.sum()>0.9) & (posFast.T.sum()<0.32)] = posFast


#%%
test = pyback.BackTest(1e6,300, compound=250)
test.timeIndex = priceFill.index
for day in posSlow.index:
    test.adjustPosition(to=posSlow.loc[day].values, price=priceFill2.loc[day].values)
    test.updateStatus()
s = pyback.Summary(test)
totalCapital, cash, balance, share, position, pnl, sum_pnl, sum_pct, nav = s.to_frame(columns=price.columns)
print("回测完毕")
s.info

#%% 因子IC计算
factor = RSI_Slow.resample('M').mean()
returns = priceFill2.resample('M').last()/priceFill2.resample('M').last().shift(1)-1
returns.fillna(0, inplace=True)
returns.replace(np.inf, 0, inplace=True)

year = '2018'
f, r = factor[year], returns[year]
month = 2
np.corrcoef(f.values[month-1], r.values[month-1])

