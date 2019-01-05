from utils.timeSeriesSplit import TimeSeriesSplitImproved
import numpy as np
import backtrader as bt
import pandas as pd
pd.set_option('display.max_columns', 100)
from strategies.SMA_Crossover import SMA_Crossover
from utils.utils import flatten_wf_multiple_stra,flatten_wf_trade_list
from utils.data import Pandas_Data
from utils.plots import plot_observer
from analyzers.trade_list_analyzer import trade_list_analyzer



def run_walk_forward(Strategy=None, optimization_input=None,
                     notebook=True):

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
        trainer.optstrategy(Strategy,**optimization_input)
        trainer.adddata(train_data)
        res = trainer.run()

        # Get optimal combination, strategy with highest ending value
        st0 = [s[0] for s in res]    # Get the element 0 (there was only 1 strategy in each run) of each optimization
        all_params = [s.params.__dict__ for s in st0]
        optimum_params[test[0]] =max(all_params,key=lambda x: x['end_value'])
        optimum_params[test[0]]['start_date'] = test_start_date
        optimum_params[test[0]]['end_date'] = test_end_date


    tester = bt.Cerebro(stdstats=False, optreturn=False)
    tester.broker.set_cash(10000)
    tester.broker.setcommission(0.0002)
    tester.broker.set_slippage_perc(0.0003)
    tester.addsizer(bt.sizers.FixedSize, stake=1000)
    for train, test in split:
        tester.addstrategy(Strategy, **optimum_params[test[0]])

    tester.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analysis')
    tester.addanalyzer(bt.analyzers.DrawDown,_name='drawdown')
    tester.addanalyzer(trade_list_analyzer, _name='trade_list')
    tester.addobserver(bt.observers.Value,plot=False)
    tester.addobserver(bt.observers.BuySell)
    tester.addobserver(bt.observers.Trades)
    tester.adddata(pandas_data.get_feed())
    res = tester.run(tradehistory=True)

    # Plots containing indicators and buysell observers
    plot_observer(tester.runstrats[0][0],notebook=notebook)
    tester.plot(iplot=notebook)

    return create_wf_analysis(res)


def create_wf_analysis(res):

    df_long_analysis = flatten_wf_multiple_stra(res)

    df_long_analysis['profit_factor']=df_long_analysis['trade_analysis_won_pnl_total']/ \
                            -df_long_analysis['trade_analysis_lost_pnl_total']

    df_analysis_mean = df_long_analysis.mean().apply(lambda x: '%.3f' % x)

    df_analysis_sum = df_long_analysis.sum().apply(lambda x: '%.3f' % x)


    df_short_analysis = df_analysis_mean[['drawdown_max_drawdown',
                                          'drawdown_max_moneydown',
                                          'trade_analysis_pnl_net_average',
                                          'profit_factor']]
    df_short_analysis = df_short_analysis.append(
        df_analysis_sum[['trade_analysis_total_closed',
                         'trade_analysis_pnl_net_total']])

    wf_trade_list = flatten_wf_trade_list(res)

    return df_long_analysis,df_short_analysis,wf_trade_list

if __name__ == '__main__':

    optimization_input = {
        'short': np.arange(1, 60, 20),
        'long': np.arange(40, 200, 20)
    }
    df_long_analysis, df_short_analysis, wf_trade_list = \
        run_walk_forward(Strategy=SMA_Crossover,
                         optimization_input=optimization_input,
                         notebook=False)

    print(df_long_analysis)
    print(wf_trade_list)
    print(df_short_analysis)
    wf_trade_list.to_csv('trades.csv',index=False)
