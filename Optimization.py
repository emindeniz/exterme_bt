from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import time
import logging
import numpy as np
from SMA_Crossover import SMA_Crossover
logging.basicConfig(level=logging.DEBUG)

import backtrader as bt
import backtrader.analyzers as btanalyzers
import pandas as pd
pd.set_option('display.max_columns', 100)
from Plots import countour_plot,heatmap
from Data import Pandas_Data, CSV_Data
from Custom_Analyzers import trade_list
from Utils import print_optimization,flatten_optimization

if __name__ == '__main__':

    short_param = np.arange(1,50,5)
    long_param = np.arange(40,200,10)
    trading_start = np.arange(0,24,1)
    trading_length = np.arange(0,24,3)
    trail_perc = np.arange(0.01,0.1,0.01)


    cerebro = bt.Cerebro(stdstats=False,optreturn=True,optdatas=True)
    cerebro.broker.setcash(10000.0)
    cerebro.broker.setcommission(commission=0.0004)
    cerebro.broker.set_slippage_perc(perc=0.0002)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)

    # Add the Data Feed to Cerebro
    cerebro.adddata(Pandas_Data().get_feed())

    cerebro.addanalyzer(btanalyzers.TradeAnalyzer,_name='trades')
    cerebro.addanalyzer(btanalyzers.DrawDown,_name='drawdown')

    strats = cerebro.optstrategy(
        SMA_Crossover,
    short=short_param,
    long=long_param)

    start_time = time.time()
    res = cerebro.run()
    print('It took', (time.time() - start_time) / 3600)

    optimization_df = flatten_optimization(res)
    optimization_df.to_csv('result.csv')

    print(optimization_df[['short','long','trades_pnl_net_total','drawdown_max_drawdown']])
    countour_plot(optimization_df,X='short',Y='long',Z='trades_pnl_net_total')
    heatmap(optimization_df,X='short',Y='long',Z='trades_pnl_net_total')