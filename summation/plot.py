import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

def _generate_profit_curve(timeIndex, NAV, daily_pnl, fig_size=(15, 10), save_path=None):
    fig = plt.figure()
    fig.set_size_inches(*fig_size)

    ax = fig.add_subplot(211)
    ax.plot(timeIndex, NAV, linewidth=2, label='策略净值')
    ax.fill_between(timeIndex, y1=NAV, y2=1,
                    where=(NAV < np.roll(NAV, 1)) |
                    ((NAV > np.roll(NAV, -1)) & (NAV >= np.roll(NAV, 1))),
                    facecolor='grey', alpha=0.3)
    # 最大回撤标注
    ax.legend(fontsize=15)
    plt.grid()

    bx = fig.add_subplot(212)
    def positive(x):
        return x if x>0 else np.nan
    def negative(x):
        return x if x<0 else np.nan
    vp, vn = np.vectorize(positive), np.vectorize(negative)
    
    bx.bar(timeIndex, vp(daily_pnl),
           2, label='当日盈亏+', color='red', alpha=0.8)
    bx.bar(timeIndex, vn(daily_pnl),
           2, label='当日盈亏-', color='green', alpha=0.8)
    bx.legend(fontsize=15)
    plt.grid()

    if not (save_path is None):
        fig.savefig(save_path, dpi=144, bbox_inches='tight')


def _autocorrelation_graph(timeIndex, NAV, fig_size=(6, 4)):
    # 输出自相关系数曲线并保存
    plt.figure(figsize=fig_size)

    nav_chg = pd.Series(NAV, index=timeIndex).pct_change().dropna()
    return pd.plotting.autocorrelation_plot(nav_chg, c='r').get_figure()
