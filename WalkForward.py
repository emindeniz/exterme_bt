from TimeSeriesSplit import TimeSeriesSplitImproved
import numpy as np

import backtrader as bt
import pandas as pd
from SMA_Crossover import SMA_Crossover
from copy import deepcopy
import json
from Data import Pandas_Data

if __name__ == '__main__':

    pandas_data = Pandas_Data()
    tscv = TimeSeriesSplitImproved(3)
    split = tscv.split(pandas_data.dataframe, fixed_length=False, train_splits=1)


    walk_forward_results = list()
    # Be prepared: this will take a while
    for train, test in split:
        # print indicies for understanding
        print(pandas_data.dataframe.shape,train.shape,test.shape)
        print('train indicies',min(train),max(train))
        print('test indicies',min(test),max(test))
        # TRAINING

        trainer = bt.Cerebro(stdstats=False,optreturn=False)
        trainer.broker.set_cash(10000)
        trainer.broker.setcommission(0.0002)
        tester = deepcopy(trainer)

        short_param = np.arange(1,60,20)
        long_param = np.arange(40,200,50)

        trainer.optstrategy(
            SMA_Crossover,
        short=short_param,
        long=long_param)

        trainer.adddata(pandas_data.get_feed(train))
        res = trainer.run()
        # Get optimal combination
        st0 = [s[0] for s in res]    # Get the element 0 (there was only 1 strategy in each run) of each optimization

        # Get the period, value and cash in text format comma separated in a list from each strategy
        periodcashvalues = [(s.p.short, s.p.long, s.thevalue) for s in st0]
        opt_short,opt_long,opt_value = max(periodcashvalues,
                                              key=lambda x:x[2])
        print(periodcashvalues)
        print(opt_long,opt_short,opt_value)
        # TESTING
        tester.addstrategy(SMA_Crossover, short=opt_short,long=opt_long)  # Test with optimal combination
        tester.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analysis')
        tester.adddata(pandas_data.get_feed(test))

        res = tester.run(tradehistory=True)
        walk_forward_results.append(res[0].analyzers.trade_analysis.get_analysis())

    for fold in walk_forward_results:
        print(json.dumps(fold,indent=4))