import numpy as np

def fillna(x):
    return 0 if np.isnan(x) else x

vfillna = np.vectorize(fillna)

def standardizeDealAmount(x):
    return round(x/100)*100
    
vstandardizeDealAmount = np.vectorize(standardizeDealAmount)

def progress_pretty_print(progress):
    print("\r[Backtest Progress {:.1%}] [{}]".format(
        progress, '='*int(progress*30)+'>'+' '*(29-int(progress*30))), end='')
progress_pretty_print