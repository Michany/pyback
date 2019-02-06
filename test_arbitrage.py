#%% import
import pyback
import numpy as np
import pandas as pd 
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression
#%% Data Preparation
data = pd.read_excel(r"E:\大三上\固定收益证券分析\Fintech\Data\BTC1812.xlsx", header=1)
data.columns = ['date','dopen','dclose','BTC_open','BTCf_open','BTC','BTCf']
data.set_index('date',inplace = True)
#data=data[:'2018-10']


pairs = [['BTC_open','BTCf_open'],['BTC','BTCf']]

#%% 协整检验
def cointegerated_test(pair, data):
    #data.dropna(inplace=True)
    temp = data[pair].dropna() #去除这两列 去0
    #print(temp)
    result = sm.tsa.stattools.coint(temp[pair[0]], temp[pair[1]])
    pValue = result[1]
    print(*pair, pValue, end='')
    if pValue < 0.05:
        print("[cointegerated!]",end='')
    print()
for p in pairs:
    cointegerated_test(p, data)
#%% Generate Signal
def regreesionModel(y_col, x_col, data):
    r'''
    `ln(P_t^A) = \alpha + \beta ln(P_t^A) + \epsilon_t`
    '''
    reg = LinearRegression()
    x = np.log(data[x_col].values).reshape((-1,1))
    y = np.log(data[y_col].values).reshape((-1,1))
    reg.fit(x, y)
    beta = reg.coef_
    print("beta = ", beta)
    alpha = reg.intercept_
    error = y-reg.predict(x)
    spread = pd.DataFrame(error, index=data.index, columns=['error'])
    return beta, alpha, error, spread
# 期现套利线性回归
def LinearRegreesionModel(y_col, x_col, data):
    r'''
    `ln(P_t^A) = \alpha + \beta ln(P_t^A) + \epsilon_t`
    '''
    reg = LinearRegression()
    x =(data[x_col].values).reshape((-1,1))
    y = (data[y_col].values).reshape((-1,1))
    reg.fit(x, y)
    beta = reg.coef_
    print("beta = ", beta)
    alpha = reg.intercept_
    error = y-reg.predict(x)
    spread = pd.DataFrame(error, index=data.index, columns=['error'])
    return beta, alpha, error, spread
#产生信号
def generateSignal(spread, lamda = 2, close_lamda = 0.5):
    
    sigma = spread.std()[0]
    signal = pd.DataFrame(index=spread.index)
    signal['high'] = ((spread > lamda * sigma) & (spread.shift(1) < lamda * sigma))
    signal['low'] = ((spread < -lamda * sigma) & (spread.shift(1) > -lamda * sigma))
    # 平仓线（close）:价差向均值回归到一定程度时平仓获利。
    signal['close4high'] = ((spread < close_lamda * sigma) & (spread.shift(1) > close_lamda * sigma))
    signal['close4low'] = ((spread > close_lamda * sigma) & (spread.shift(1) < close_lamda * sigma))
    return signal

#%% Perform Backtest
def backtest(signal, alpha, beta, data):
    pos = pd.DataFrame(0,index=signal.index, columns=pair)
    daily_pnl = pd.DataFrame(0,index=signal.index, columns=pair)
    fee = pd.DataFrame(0,index=signal.index, columns=pair)
    for tick, sig in signal[1:].iterrows():
        # 当期收益 = （当期价格-上期价格）*上期仓位
        daily_pnl.loc[tick] = (data.loc[tick]-data.shift(1).loc[tick]) * pos.shift(1).loc[tick]
        if sig['high']:
            print(tick, '做空价差')
            if True:#是否需要加上对当前仓位的判断？
                pos.loc[tick, pair[0]] -= 1
                pos.loc[tick, pair[1]] += beta
            fee.loc[tick] = data.loc[tick] * pos.diff().abs().loc[tick] * 0.001
        elif sig['low']:
            print(tick, '做多价差')
            if True:
                pos.loc[tick, pair[0]] += 1
                pos.loc[tick, pair[1]] -= beta
            fee.loc[tick] = data.loc[tick] * pos.diff().abs().loc[tick] * 0.001
        elif sig['close4high']:
            if pos.shift(1).loc[tick, pair[0]] < 0: #如果原来有空头
                print(tick, "平仓")
                pos.loc[tick] = 0 #平仓
                fee.loc[tick] = data.loc[tick] * pos.diff().abs().loc[tick] * 0.001
        elif sig['close4low']:
            if pos.shift(1).loc[tick, pair[0]] > 0: #如果原来有空头
                print(tick, "平仓")
                pos.loc[tick] = 0 #平仓
                fee.loc[tick] = data.loc[tick] * pos.diff().abs().loc[tick] * 0.001
        else:
            pos.loc[tick] = pos.shift(1).loc[tick]
            fee.loc[tick] = 0
    
    #daily_pnl.cumsum().plot()
    #(daily_pnl-fee).cumsum().plot()
    (daily_pnl-fee).T.sum().cumsum().plot()
    return pos, daily_pnl, fee
#%% 回测
for pair in pairs[:1]:
    print(pair)
    beta, alpha, error, spread = regreesionModel(*pair, data.dropna(subset=pair))
    spread.plot()
    signal = generateSignal(spread, 2, 1)
    pos, daily_pnl, fee = backtest(signal, alpha, beta, data[pair])
