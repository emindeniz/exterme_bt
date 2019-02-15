import backtrader as bt
from strategies.SMACrossoverMulti import SMACrossoverMulti
import numpy as np
from comissions.comissions import StocksFixed

def getConfig():

    walkforward_input = {
        'strategy': SMACrossoverMulti,
        # 'strategy': PercentFollower,
        'datapath': 'C:\\ProgramData\\Kibot Agent\\Data\\30m\\',
        # 'datapath': 'C:\\TickDownloader\\tickdata\\',
        'outputpath': 'results\\',
        'start_date': '2006/01/01',
        'end_date': '2017/01/01',
        'n_splits': 2,
        # 'tickers': [['EURUSD','D1','UTC-5','00'],
        #             ['GBPUSD', 'D1', 'UTC-5', '00']],
        'tickers': [['EBAY'], ['AAPL'], ['JNJ']],
        'extension': 'txt',
        # 'extension': 'csv',
        'optimization_input': {
            # 'fast': 14,
            # 'slow': 200,
            'perc_change': np.arange(0.01, 0.1, 0.01),
            'before_period': 2,
            'after_period': 1,
            'trading_start': np.arange(9, 12, 0.5),
            'trading_length': 8,
            'filter_off': False,
            'stop_loss_on': True,
            'stop_loss': np.arange(0.01, 0.06, 0.01),
            'printlog': False},
        'broker_input': {
            'stdstats': False,
            'opreturn': False,
            'cash': 20000,
            'slippage_perc': 0.001,
            'comission': StocksFixed,
            'commvalue': 5,
            'sizer': bt.sizers.PercentSizer,
            'percents': 30
        }
    }
