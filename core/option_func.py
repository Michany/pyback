from scipy import stats
import pandas as pd
import numpy as np
import math


#bs期权定价公式
def blsprice (s, k, t, v, rf, div, type):
    """ Price an option using the Black-Scholes model.
    s: initial stock price
    k: strike price
    t: expiration time,year
    v: volatility
    rf: risk-free rate
    div: dividend
    cp: +1/-1 for call/put
    """
    if type in ['call','Call','认购','C']:
        cp = 1
    elif type in ['put','Put','认沽','P']:
        cp = -1
               
    d1 = (math.log(s/k)+(rf-div+0.5*math.pow(v,2))*t)/(v*math.sqrt(t+0.0001))
    d2 = d1 - v*math.sqrt(t)
    optprice = (cp*s*math.exp(-div*t)*stats.norm.cdf(cp*d1)) - (cp*k*math.exp(-rf*t)*stats.norm.cdf(cp*d2))
    
    return optprice


#根据bs公式算delta,数值解
def blsdelta (s, k, t, v, rf, div, type):
    s0 = s
    s1 = s*1.0001
    p0 = blsprice(s0, k, t, v, rf, div, type)
    p1 = blsprice(s1, k, t, v, rf, div, type)
    delta = (p1 - p0)/(s1 - s0)
    
    return delta

#根据bs公式算imvol,数值二分逼近
def blsimvol (p, s, k, t, rf, div, type):
    vol_up = 1
    vol_down = 0.001
    vol = vol_down
    p_v = blsprice(s, k, t, vol, rf, div, type)
    if blsprice(s, k, t, vol_down, rf, div, type)>=p:
        return vol_down
    elif blsprice(s, k, t, vol_up, rf, div, type)<=p:
        return vol_up
    while abs(p_v - p)>1e-6:
        vol = 1/2*(vol_up+vol_down)
        p_v = blsprice(s, k, t, vol, rf, div, type)
        if p_v - p > 0:
            vol_up = vol
        else:
            vol_down = vol            
    return vol


def greeks(Time_n,etf_price,code):
    r=0.04
    OData=option_info(Time_n,code)
    K=OData['EXE_PRICE']
    sigma=OData['US_IMPLIEDVOL']
    T=OData['PTMTRADEDAY']/252
    d1=(np.log(etf_price/K)+(r+sigma**2/2))*T/(sigma*np.sqrt(T))
    d2=d1-sigma*np.sqrt(T)
    if OData['EXE_MODE']=='认购':
        delta=stats.norm.cdf(d1)
        theta=(-etf_price*stats.norm.pdf(d1)*sigma/(2*np.sqrt(T))-r*K*np.exp(-r*T)*stats.norm.cdf(d2))
    if OData['EXE_MODE']=='认沽':
        delta=stats.norm.cdf(d1)-1
        theta=(-etf_price*stats.norm.pdf(d1)*sigma/(2*np.sqrt(T))+r*K*np.exp(-r*T)*stats.norm.cdf(-d2))
    gamma=stats.norm.pdf(d1)/(etf_price*sigma*np.sqrt(T))
    vega=etf_price*stats.norm.pdf(d1)*np.sqrt(T)
    vomma=etf_price*stats.norm.pdf(d1)*np.sqrt(T)*d1*d2/sigma
    vanna=-stats.norm.pdf(d1)*d2/sigma
    veta=etf_price*stats.norm.pdf(d1)*np.sqrt(T)*(r*d1/(sigma*np.sqrt(T))-(1+d1*d2)/(2*T))                              
    charm=-stats.norm.pdf(d1)*(2*r*T-d2*sigma*np.sqrt(T))/(2*T*sigma*np.sqrt(T))
    return delta,gamma,theta,vega,vomma,vanna,veta,charm                            


#根据bs公式算gamma,数值解
def blsgamma (s, k, t, v, rf, div, type):
    s0 = s
    s1 = s*1.0001
    d0 = blsdelta (s0, k, t, v, rf, div, type)
    d1 = blsdelta (s1, k, t, v, rf, div, type)
    gamma = (d1 - d0)/(s1 - s0)
    
    return gamma

#根据bs公式算vega,数值解
def blsvega (s, k, t, v, rf, div, type):
    v0 = v
    v1 = v*1.0001
    p0 = blsprice(s, k, t, v0, rf, div, type)
    p1 = blsprice(s, k, t, v1, rf, div, type)
    vega = (p1 - p0)/(v1 - v0)
    
    return vega

#根据bs公式算theta,数值解
def blstheta (s, k, t, v, rf, div, type):
    t0 = t
    t1 = t*0.99999
    p0 = blsprice(s, k, t0, v, rf, div, type)
    p1 = blsprice(s, k, t1, v, rf, div, type)
    theta = -(p1 - p0)/(t1 - t0)   
    return theta


#根据bs公式算delta,wind版
def blsdelta_w (s, k, t, v, rf, div, type):
    d1 = (math.log(s/k)+(rf-div+0.5*math.pow(v,2))*t)/(v*math.sqrt(t))
           
    if type in ['call','Call','认购']:
        delta = stats.norm.cdf(d1)
    elif type in ['put','Put','认沽']:
        delta = stats.norm.cdf(d1) - 1
    
    return delta

#根据bs公式算gamma,wind版
def blsgamma_w (s, k, t, v, rf, div, type):
    d1 = (math.log(s/k)+(rf-div+0.5*math.pow(v,2))*t)/(v*math.sqrt(t))    
    gamma = 1/math.sqrt(2*np.pi)*math.exp(-d1**2/2)/(s*v*math.sqrt(t))
    
    return gamma

#根据bs公式算vega,wind版
def blsvega_w (s, k, t, v, rf, div, type):
    d1 = (math.log(s/k)+(rf-div+0.5*math.pow(v,2))*t)/(v*math.sqrt(t))
    vega = s*math.sqrt(t)/math.sqrt(2*np.pi)*math.exp(-d1**2/2)*0.01
    
    return vega

#根据bs公式算theta,wind版
def blstheta_w (s, k, t, v, rf, div, type):
    
    d1 = (math.log(s/k)+(rf-div+0.5*math.pow(v,2))*t)/(v*math.sqrt(t))    
    d2 = d1 - v*math.sqrt(t)
    if type in ['call','Call','认购']:
        theta = (-s/math.sqrt(2*np.pi)*math.exp(-d1**2/2)*v/(2*math.sqrt(t))-rf*k*math.exp(-rf*t)*stats.norm.cdf(d2))/252
    elif type in ['put','Put','认沽']:
        theta = (-s/math.sqrt(2*np.pi)*math.exp(-d1**2/2)*v/(2*math.sqrt(t))+rf*k*math.exp(-rf*t)*stats.norm.cdf(-d2))/252
    
    return theta

    