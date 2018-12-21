from TimeSeriesSplit import TimeSeriesSplitImproved
import numpy as np
from IPython import embed
import backtrader as bt
import pandas as pd
pd.set_option('display.max_columns', 100)
from SMA_Crossover import SMA_Crossover
from copy import deepcopy
import json
from Utils import flatten_multiple_stra
from Data import Pandas_Data

if __name__ == '__main__':

    pandas_data = Pandas_Data()
    tscv = TimeSeriesSplitImproved(3)
    split = list(tscv.split(pandas_data.dataframe, fixed_length=False, train_splits=1))

    optimum_params = {}
    # Optimize the parameters for each training split
    for train, test in split:
        # print indicies for understanding
        print(pandas_data.dataframe.shape,train.shape,test.shape)
        print('train indicies',min(train),max(train))
        print('test indicies',min(test),max(test))
        train_data = pandas_data.get_feed(train)
        test_start_date = pandas_data.get_start_date(test)
        test_end_date = pandas_data.get_end_date(test)
        # TRAINING

        trainer = bt.Cerebro(stdstats=False,optreturn=False)
        trainer.broker.set_cash(10000)
        trainer.broker.setcommission(0.0002)

        short_param = np.arange(1,60,20)
        long_param = np.arange(40,200,50)

        trainer.optstrategy(
            SMA_Crossover,
        short=short_param,
        long=long_param)

        trainer.adddata(train_data)
        res = trainer.run()
        # Get optimal combination
        st0 = [s[0] for s in res]    # Get the element 0 (there was only 1 strategy in each run) of each optimization

        # Get the period, value and cash in text format comma separated in a list from each strategy
        periodcashvalues = [(s.p.short, s.p.long, s.thevalue) for s in st0]
        opt_short,opt_long,opt_value = max(periodcashvalues,
                                              key=lambda x:x[2])
        optimum_params[test[0]] ={'start_date': test_start_date,
                           'end_date':test_end_date,
                           'short':opt_short,
                           'long':opt_long,
                            'printlog':True}
        print(periodcashvalues)
        print(opt_long,opt_short,opt_value)

    tester = bt.Cerebro(stdstats=True, optreturn=False)
    tester.broker.set_cash(10000)
    tester.broker.setcommission(0.0002)
    for train, test in split:
        tester.addstrategy(SMA_Crossover, **optimum_params[test[0]])

    tester.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analysis')
    tester.adddata(pandas_data.get_feed())
    res = tester.run(tradehistory=True)

    print(flatten_multiple_stra(res))
