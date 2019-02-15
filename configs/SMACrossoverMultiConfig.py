import backtrader as bt
from strategies.SMACrossoverMulti import SMACrossoverMulti
import numpy as np
from comissions.comissions import StocksFixed,StocksPerc
from sizers.PercentReverser import PercentReverser


def getConfig():

    walkforward_input = {
        'strategy': SMACrossoverMulti,
        'datapath': 'C:\\TickDownloader\\tickdata\\',
        'outputpath': 'results\\',
        'start_date': '2006/01/01',
        'end_date': '2017/01/01',
        'n_splits': 2,
        'tickers': [
            # ['EURUSD','D1','UTC-5','00'],
            # ['GBPUSD', 'D1', 'UTC-5', '00'],
            # ['USDJPY', 'D1', 'UTC-5', '00'],

             ['NZDUSD', 'D1', 'UTC-5', '00'],
            # ['USDCAD', 'D1', 'UTC-5', '00'],
            # ['USDCHF', 'D1', 'UTC-5', '00']
            ],
        'extension': 'csv',
        'optimization_input': {
            'fast': 1, # np.arange(1,40,2),
            'slow': 20, # np.arange(30,200,10),
            'trading_start': 9,
            'trading_length': 8,
            'filter_off': True,
            'stop_loss_on': False, # True,
            'stop_loss': 1, # np.arange(0.01,0.06,0.01),
            'printlog': True
        },

        'broker_input': {
            'stdstats': False,
            'opreturn': False,
            'cash': 10000,
            'slippage_perc': 0,
            'comission': StocksPerc,
            'commvalue':0,
            'sizer': bt.sizers.PercentSizer,
            'percents': 85
        }
    }

    return walkforward_input
