import logging
import numpy as np
from strategies.SMACrossover import SMACrossover
logging.basicConfig(level=logging.DEBUG)
import pandas as pd
pd.set_option('display.max_columns', 100)
pd.set_option('display.precision',2)
from utils.plots import heatmap,plot_mae,plot_mfe
import warnings; warnings.simplefilter('ignore')

if __name__ == '__main__':
    from walk_forward import run_walk_forward_multi

    files = ['C:\\TickDownloader\\tickdata\\GBPUSD_D1_UTC-5_00.csv',
             'C:\\TickDownloader\\tickdata\\EURUSD_D1_UTC-5_00.csv']

    optimization_input = {
        'short': np.arange(1, 60, 20),
        'long': np.arange(40, 200, 20),
        'rsi_period': np.arange(14, 15, 14),
        'rsi_value': np.arange(50, 51, 10),
        'stop_loss_on': True,
        'stop_loss': 0.04
    }
    (df_long_analysis, df_short_analysis, wf_trade_list), param_space = \
        run_walk_forward_multi(Strategy=SMACrossover,
                               optimization_input=optimization_input,
                               files=files,
                               notebook=True,
                               n_splits=3)

    print(df_short_analysis)
    print(df_long_analysis)
    print(wf_trade_list)

    plot_mae(wf_trade_list, notebook=True)
    plot_mfe(wf_trade_list, notebook=True)
    param_space = pd.DataFrame(param_space).groupby(param_space.index).mean()
    param_space.head()
    heatmap(param_space, 'short', 'long', 'end_value')