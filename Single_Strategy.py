from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os.path  # To manage paths
import json
import logging
from SMA_Crossover import SMA_Crossover
from CCI import CCI
from RSI import RSI
from Utils import print_analysis
logging.basicConfig(level=logging.DEBUG)

import backtrader as bt
import backtrader.analyzers as btanalyzers
from Custom_Analyzers import trade_list
import backtrader.observers as btobservers
from tabulate import tabulate
from Data import Pandas_Data
import pandas as pd
from Utils import flatten_dict

if __name__ == '__main__':

    cerebro = bt.Cerebro(stdstats=True,
                         optreturn=False)

    cerebro.broker.setcash(10000.0)
    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.0004)
    cerebro.broker.set_slippage_perc(perc=0.0002)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=2000)

    data = Pandas_Data().get_feed()
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    cerebro.addanalyzer(btanalyzers.TradeAnalyzer,_name='trade_analysis')
    cerebro.addanalyzer(btanalyzers.DrawDown,_name='drawdown')
    cerebro.addanalyzer(btanalyzers.PyFolio,_name='pyfolio')
    cerebro.addanalyzer(trade_list,_name='trade_list')
    cerebro.addobserver(btobservers.DrawDown,plot=True,subplot=True)


    # Add a strategy
    strats = cerebro.addstrategy(SMA_Crossover,printlog=True)

    logging.info('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    res = cerebro.run(tradehistory=True)

    logging.info('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    print('Total time:',len(res[0].array))
    print_analysis(res[0],filename='result.csv')

    # Plot the result
    cerebro.plot(numfigs=1)