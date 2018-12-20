import pandas as pd
"""
Functions in this module take a history of trades and perform a montecarlo
simulation, to calculate the distribution of maximum drawdowns.
"""

def calculate_drawdown(df_trade_history, pnl_col ='pnl%',
                       dur_col = 'nbars'):
    """
    calculate drawdown and duration
    Input:
        pnl, in $
    Returns:
        drawdown : vector of drawdwon values
        duration : vector of drawdown duration

    """
    pnl = df_trade_history[pnl_col]
    barlen = df_trade_history[dur_col]
    cumret = pnl.cumsum().tolist()

    highwatermark = [0]

    idx = range(pnl.shape[0])
    drawdown = pd.Series(index=idx)
    drawdowndur = pd.Series(index=idx)

    for t in range(0, pnl.shape[0]):
        highwatermark.append(max(highwatermark[t], cumret[t]))
        drawdown[t] = (highwatermark[t+1] - cumret[t])
        drawdowndur[t] = (0 if drawdown[t] == 0 else drawdowndur[t - 1] + barlen[t]
                          if t>0 else barlen[t])

    return drawdown,drawdowndur

def shuffle_trade_history(df_trade_history):
    max_drawdowns = []
    for i in range(100):
        df_sample = df_trade_history.sample(frac=1, replace=False, axis=0)
        drawdown, drawdowndur = calculate_drawdown(df_sample)
        df_sample['iteration'] = i
        max_drawdowns.append(drawdown.max())

    return max_drawdowns