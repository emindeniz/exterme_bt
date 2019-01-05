import pandas as pd
import numpy as np
from datetime import timedelta
from functools import wraps
from time import time

pd.set_option('display.max_columns', 100)
"""
Functions in this module take a history of trades and perform a montecarlo
simulation, to calculate the distribution of maximum drawdowns.
"""

def timeit(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print('Elapsed time: {}'.format(end-start))
        return result
    return wrapper


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
    barlen = df_trade_history[dur_col]
    equity = df_trade_history[pnl_col].tolist()

    highwatermark = [equity[0]]

    idx = range(len(equity))
    drawdown = pd.Series(index=idx)
    drawdown_perc = pd.Series(index=idx)
    drawdowndur = pd.Series(index=idx)

    for t in range(0, len(equity)):
        highwatermark.append(max(highwatermark[t], equity[t]))
        drawdown[t] = (highwatermark[t+1] - equity[t])
        drawdown_perc[t] = drawdown[t]/highwatermark[t+1]*100
        drawdowndur[t] = (0 if drawdown[t] == 0
                          else drawdowndur.iloc[t - 1] + barlen.iloc[t]
                          if t>0 else barlen.iloc[t])

    return drawdown,drawdown_perc,drawdowndur

def monte_carlo(df_trade_history, equity=10000,
                margin_req=0.5, iterations=1000,
                contract_size=1, contract_value=1000):

    # Profits and losses are multiplied by contract size
    # Trade results are assumed to be from a single contract
    total_length = (pd.to_datetime(df_trade_history.iloc[0]['datein'])-
                    pd.to_datetime(df_trade_history.iloc[-1]['dateout']))\
                   //timedelta(days=365.24)
    total_length = abs(total_length)

    current_return = np.zeros(iterations)
    ruin = np.zeros(iterations)
    max_drawdown = np.zeros(iterations)
    max_drawdown_dur = np.zeros(iterations)
    max_drawdown_perc = np.zeros(iterations)
    equity_end = np.zeros(iterations)

    for i in range(iterations):
        df_sample = df_trade_history.sample(frac=1,
                                            replace=True,
                                            axis=0)

        df_sample['pnl'] = df_sample['pnl'] * contract_size
        pnl_line = df_sample['pnl'].cumsum().values
        ruin[i] = np.any(
            (equity + pnl_line) <
            (contract_size*contract_value*margin_req)
        )
        current_return[i] = (pnl_line[-1]) / equity / total_length * 100
        df_sample['equity_line'] = equity + pnl_line
        drawdown, drawdown_perc, drawdowndur = \
            calculate_drawdown(df_sample,pnl_col='equity_line')
        max_drawdown[i] = drawdown.max()
        max_drawdown_dur[i] = drawdowndur.max()
        max_drawdown_perc[i] = drawdown_perc.max()
        equity_end[i] = pnl_line[-1]+equity



    results = pd.DataFrame({
        'ret_perc':current_return,
        'ruin':ruin,
        'max_dd':max_drawdown,
        'max_dd_perc':max_drawdown_perc,
        'max_dd_dur': max_drawdown_dur,
    'equity_end':equity_end})

    return results

def monte_carlo_equity(df_trade_history,starting_equity=1000,
                       margin_req=0.02,iterations=1000,
                       contract_size=1,contract_value=1000,
                       ending_equity=2000,increment=100):
    results = pd.DataFrame()
    for equity in range(starting_equity,ending_equity,increment):

        temp = monte_carlo(df_trade_history,equity=equity,
                       margin_req=margin_req,iterations=iterations,
                       contract_size=contract_size,contract_value=contract_value)

        risk_of_ruin = temp['ruin'].mean()
        temp = temp[temp['ruin']==False]
        temp = temp.median()
        temp['ruin'] = risk_of_ruin
        temp['equity'] = equity

        results = results.append(pd.DataFrame(temp).T)

    print(results)
    return

def monte_carlo_ff_sizing(df_trade_history, equity=10000,
                       margin_req=0.1, iterations=1000,
                       contract_value=1000,start_sizing=0.01,
                       end_sizing=0.3, increment=0.02,
                          max_drawdown = 300):

    results = pd.DataFrame()

    for fixed_ratio in np.arange(start_sizing,end_sizing,increment):

        contract_size = int(fixed_ratio * equity / max_drawdown)

        temp = monte_carlo(df_trade_history,equity=equity,
                       margin_req=margin_req,iterations=iterations,
                       contract_size=contract_size,contract_value=contract_value)

        risk_of_ruin = temp['ruin'].mean()
        temp = temp[temp['ruin']==False]
        temp = temp.median()
        temp['ruin'] = risk_of_ruin
        temp['cont_size'] = contract_size
        temp['sizing'] = fixed_ratio

        results = results.append(pd.DataFrame(temp).T)
    print(results)
    return

def monte_carlo_mdd_sizing(df_trade_history, equity=10000,
                       margin_req=0.1, iterations=1000,
                       contract_value=1000,max_drawdown=500):

    results = pd.DataFrame()

    contract_size = np.floor(equity/((max_drawdown+contract_value*margin_req)*1.5))

    temp = monte_carlo(df_trade_history,equity=equity,
                   margin_req=margin_req,iterations=iterations,
                   contract_size=contract_size,contract_value=contract_value)

    risk_of_ruin = temp['ruin'].mean()
    temp = temp[temp['ruin']==False]
    temp = temp.median()
    temp['ruin'] = risk_of_ruin
    temp['cont_size'] = contract_size

    results = results.append(pd.DataFrame(temp).T)
    print(results)
    return

if __name__ == '__main__':

    # It is always assumed that trade history results
    # are due to single contract
    df_trade_history = pd.read_csv('trades.csv')

    monte_carlo_ff_sizing(df_trade_history, equity=10000,
                       margin_req=0.05, iterations=100,
                       contract_value=1000,start_sizing=1,
                       end_sizing=5, increment = 1,
                          max_drawdown=300)

    monte_carlo_mdd_sizing(df_trade_history, equity=10000,
                       margin_req=0.05, iterations=100,
                       contract_value=1000,max_drawdown=300)

    monte_carlo_equity(df_trade_history, starting_equity=10000,
                       margin_req=0.05, iterations=100,
                       contract_size=50, contract_value=1000,
                       ending_equity=20000, increment=1000)