import numpy as np
import statsmodels.api as sm
from sklearn.linear_model import LinearRegression

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


def LinearRegreesionModel(y_col, x_col, data):
    r'''
    `P_t^A) = \alpha + \beta P_t^A + \epsilon_t`
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
