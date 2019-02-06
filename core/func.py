import numpy as np

def fillna(x):
    return 0 if np.isnan(x) else x

vfillna = np.vectorize(fillna)

def standardizeDealAmount(x):
    return round(x/100)*100
    
vstandardizeDealAmount = np.vectorize(standardizeDealAmount)
