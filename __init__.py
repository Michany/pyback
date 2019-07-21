

# Let users know if they're missing any of our hard dependencies
hard_dependencies = ("pandas", "numpy", "matplotlib")
missing_dependencies = []

for dependency in hard_dependencies:
    try:
        __import__(dependency)
    except ImportError as e:
        missing_dependencies.append(dependency)

if missing_dependencies:
    raise ImportError(
        "Missing required dependencies {0}".format(missing_dependencies))
del hard_dependencies, dependency, missing_dependencies

try:
    from pyback.core.data import DataManager
    from pyback.core.data import concat_op_info, empty_check    
except ImportError:
    pass
from pyback.core.backtest import Record, BackTest, StockBackTest, OptionBackTest
from pyback.summation.summary import Summary
 
# module level doc-string
__doc__ = """
Pyback - an experimental module to perform backtests for Python
===============================================================

Main Features
-------------
Here are something this backtest framework can do:

RSI

Updated in 2018/9/6
"""
