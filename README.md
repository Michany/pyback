# PyBack
__An experimental module to perform backtests for Python__

TODO List
---------
- [x] 加快回测速度 
- [ ] 验证adjustPosition等交易的正确性
- [ ] 增加手续费

- [ ] 套利策略test完成
- [ ] 套利函数正确性的验证
- [ ] 套利滑点


Branch
------

- Master  
  主分支
  
- batch_record_faster
  批处理分支
  
  I found that the bottleneck of `pyback.BackTest` lies in `numpy.append()` (the concatenation process of exsiting records and the new record).  
  研究发现，`pyback.BackTest`的性能瓶颈在于`numpy.append()`拼合时。即便是拼合一条新纪录，也会需要重新构建整个数组，当记录太多的时候容易造成速度慢的问题。

  To address this problem, this branch introduce a batching method. That is, in order to accelerate the concatenation process, using small batches to store the records and concatenate these small batches at the end.  
  为解决这个问题，此branch版本将记录分批，加快拼合速度。

  Besides, you can define a parameter called `compound` to adjust the cycle of compound returns.  
  另外，这个版本中，可以自定义复利周期。

- Arbitrage
  套利分支

  In this branch, `pyback` will be able to perform backtest for arbitrage strategies.  
  在这个分支中，`pyback`将能够为统计套利策略进行回测。

  Meanwhile, there are some basic functions and strategies, useful in arbitrage, stored in `pyback.strategy` module.  
  同时，在strategy子库中，存放了一些套利所需基础函数和策略。


Examples
--------    
```python
test = pyback.BackTest(1e6,300)
test.timeIndex = price.index

for day in posSlow.index:
    test.adjustPosition(to, price)
    test.updateStatus()

s = pyback.Summary(test)
totalCapital, cash, balance, share, position, pnl, sum_pnl, sum_pct, nav = s.to_frame(columns=price.columns)
s.info
```