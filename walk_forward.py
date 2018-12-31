from utils.timeSeriesSplit import TimeSeriesSplitImproved
import numpy as np
import backtrader as bt
import pandas as pd
pd.set_option('display.max_columns', 100)
from strategies.SMA_Crossover import SMA_Crossover
from utils.utils import flatten_multiple_stra
from utils.data import Pandas_Data

def run_walk_forward():

    pandas_data = Pandas_Data()
    tscv = TimeSeriesSplitImproved(2)
    split = list(tscv.split(pandas_data.dataframe, fixed_length=False, train_splits=1))

    optimum_params = {}
    # Optimize the parameters for each training split
    for train, test in split:

        # Get the training data and start and end dates for test data
        train_data = pandas_data.get_feed(train)
        test_start_date = pandas_data.get_start_date(test)
        test_end_date = pandas_data.get_end_date(test)

        # TRAINING
        trainer = bt.Cerebro(stdstats=False,optreturn=False)
        trainer.broker.set_cash(10000)
        trainer.broker.setcommission(0.0003)
        trainer.broker.set_slippage_perc(0.0003)
        trainer.addsizer(bt.sizers.FixedSize, stake=1000)

        optimization_input = {
            'short' : np.arange(1,60,10),
            'long' : np.arange(40,200,20)
        }

        trainer.optstrategy(SMA_Crossover,**optimization_input)
        trainer.adddata(train_data)
        res = trainer.run()

        # Get optimal combination, strategy with highest ending value
        st0 = [s[0] for s in res]    # Get the element 0 (there was only 1 strategy in each run) of each optimization
        all_params = [s.params.__dict__ for s in st0]
        optimum_params[test[0]] =max(all_params,key=lambda x: x['end_value'])
        optimum_params[test[0]]['start_date'] = test_start_date
        optimum_params[test[0]]['end_date'] = test_end_date


    tester = bt.Cerebro(stdstats=True, optreturn=False)
    tester.broker.set_cash(10000)
    tester.broker.setcommission(0.0002)
    tester.broker.set_slippage_perc(0.0003)
    tester.addsizer(bt.sizers.FixedSize, stake=1000)

    for train, test in split:
        tester.addstrategy(SMA_Crossover, **optimum_params[test[0]])

    tester.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analysis')
    tester.addanalyzer(bt.analyzers.DrawDown,_name='drawdown')
    tester.addobserver(bt.observers.DrawDown)
    tester.adddata(pandas_data.get_feed())
    res = tester.run(tradehistory=True)
    tester.plot()
    print(flatten_multiple_stra(res))

if __name__ == '__main__':
    run_walk_forward()
