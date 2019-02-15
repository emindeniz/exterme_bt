import logging
from strategies.PercentFollower import PercentFollower
logging.basicConfig(level=logging.DEBUG)
import backtrader as bt
import pandas as pd
pd.set_option('display.max_columns', 100)
pd.set_option('display.precision',2)
from utils.data import Pandas_Data
import warnings; warnings.simplefilter('ignore')
from analyzers.trade_list_analyzer import trade_list_analyzer
from datetime import datetime
from strategies.SMACrossoverMulti import SMACrossoverMulti



if __name__ == '__main__':

    datapath = 'C:\\ProgramData\\Kibot Agent\\Data\\30m\\'
    pandas_data = Pandas_Data(datapath=datapath,suffixes=['EBAY'],extension='txt')

    param_input = {
        'perc_change': 0.01,
        'before_period': 1,
        'after_period': 1,
        'stop_loss': 0.02,
        'trading_start': 9,
        'trading_length': 8,
        'filter_off':False,
        'stop_loss_on': True,
        'printlog' : True
    }
    Strategy = PercentFollower


    tester = bt.Cerebro(stdstats=False, optreturn=False)
    tester.broker.set_cash(10000)
    tester.broker.setcommission(0.0002)
    tester.broker.set_slippage_perc(0.0003)
    tester.addsizer(bt.sizers.PercentSizer, percents=20)
    tester.addstrategy(Strategy,**param_input)
    tester.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analysis')
    tester.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
    tester.addanalyzer(trade_list_analyzer, _name='trade_list')
    tester.addobserver(bt.observers.Broker)
    tester.addobserver(bt.observers.BuySell)
    tester.addobserver(bt.observers.Trades)
    tester.adddata(pandas_data.get_feedbydate(fromdate=datetime(2016,10,1),
                                              todate=datetime(2017,1,1)))
    wf_res = tester.run(tradehistory=True)

    tester.plot()