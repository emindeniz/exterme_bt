from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
from strategies.SMA_Crossover import SMA_Crossover
from utils.utils import print_analysis
logging.basicConfig(level=logging.DEBUG)

import backtrader as bt
import backtrader.analyzers as btanalyzers
from utils.data import Pandas_Data

if __name__ == '__main__':

    cerebro = bt.Cerebro(stdstats=True,
                         optreturn=False)

    cerebro.broker.setcash(10000.0)
    # Set the commission - 0.1% ... divide by 100 to remove the %
    cerebro.broker.setcommission(commission=0.0004)
    cerebro.broker.set_slippage_perc(perc=0.0002)

    # Add a FixedSize sizer according to the stake
    cerebro.addsizer(bt.sizers.FixedSize, stake=1000)

    data = Pandas_Data().get_feed()
    # Add the Data Feed to Cerebro
    cerebro.adddata(data)

    cerebro.addanalyzer(btanalyzers.TradeAnalyzer,_name='trade_analysis')
    cerebro.addanalyzer(btanalyzers.DrawDown,_name='drawdown')

    # Add a strategy
    strats = cerebro.addstrategy(SMA_Crossover,printlog=True)

    logging.info('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    res = cerebro.run()

    logging.info('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    print('Total time:',len(res[0].array))
    print_analysis(res[0],filename='result.csv')

    # Plot the result
    #cerebro.plot(numfigs=1)