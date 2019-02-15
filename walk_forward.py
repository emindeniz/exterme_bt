from utils.timeSeriesSplit import TimeSeriesSplitImproved
import backtrader as bt
import pandas as pd
pd.set_option('display.max_columns', 100)
from utils.utils import flatten_wf_multiple_stra,flatten_wf_trade_list
from utils.plots import plot_observer
from analyzers.trade_list_analyzer import trade_list_analyzer
from functools import wraps
from time import time
from utils.data import Pandas_Data,getPandasDatas
from comissions.comissions import StocksFixed
import os
from utils.plots import heatmap,plot_mae,plot_mfe,plot_bokeh_dates_vs_values
from datetime import datetime
import inspect
from pygments import highlight
from pygments.lexers.python import PythonLexer
from pygments.formatters.html import HtmlFormatter
import pprint
from copy import deepcopy
import numpy as np
from matplotlib.dates import num2date

def timeit(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        start = time()
        result = f(*args, **kwargs)
        end = time()
        print('Elapsed time: {}'.format(end-start))
        return result
    return wrapper

@timeit
def run_walk_forward(**kwargs):

    Strategy = kwargs.get('strategy',None)
    optimization_input = kwargs.get('optimization_input',None)
    broker_input = kwargs.get('broker_input',None)
    start_date = kwargs.get('start_date',None)
    end_date = kwargs.get('end_date',None)
    n_splits = kwargs.get('n_splits',2)
    outputpath = kwargs.get('outputpath',None)
    save = kwargs.get('save',True)
    datapath = kwargs.get('datapath',None)
    tickers = kwargs.get('tickers',None)
    extension = kwargs.get('extension','txt')

    pandas_datas = getPandasDatas(datapath=datapath,
                                  suffixes=tickers,
                                  extension=extension)

    daterange = pd.DataFrame(pd.date_range(start_date, end_date, freq='D'),
                             columns=['date'])
    daterange = daterange.set_index('date',drop=True)
    tscv = TimeSeriesSplitImproved(n_splits)
    split = list(tscv.split(daterange, fixed_length=False))

    optimum_params = {}
    params_space = pd.DataFrame()
    # Optimize the parameters for each training split
    for train, test in split:

        # Get the training data and start and end dates for test data
        train_start_date = daterange.iloc[train].index[0]
        train_end_date = daterange.iloc[train].index[-1]
        test_start_date = daterange.iloc[test].index[0]
        test_end_date = daterange.iloc[test].index[-1]

        trainer = getBroker(**broker_input)
        trainer.optstrategy(Strategy,**optimization_input)
        for data in pandas_datas:
            trainer.adddata(data.get_feedbydate(fromdate=train_start_date,
                                                todate=train_end_date))
        res = trainer.run()

        # Get optimal combination, strategy with highest ending value
        st0 = [s[0] for s in res]    # Get the element 0 (there was only 1 strategy in each run) of each optimization
        all_params = [s.params.__dict__ for s in st0]
        params_space = params_space.append(pd.DataFrame(all_params))
        optimum_params[test[0]] =max(all_params,key=lambda x: x['end_value'])
        optimum_params[test[0]]['start_date'] = test_start_date
        optimum_params[test[0]]['end_date'] = test_end_date

    tester = getBroker(**broker_input)
    for train, test in split:
        tester.addstrategy(Strategy, **optimum_params[test[0]])

    tester.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trade_analysis')
    tester.addanalyzer(bt.analyzers.DrawDown,_name='drawdown')
    tester.addanalyzer(trade_list_analyzer, _name='trade_list')
    tester.addobserver(bt.observers.Broker)
    tester.addobserver(bt.observers.BuySell)
    tester.addobserver(bt.observers.Trades)
    for data in pandas_datas:
        tester.adddata(data.get_feedbydate(daterange.index[0],
                                           daterange.index[-1]))
    wf_res = tester.run(tradehistory=True)

    walkforwarddto = create_wf_analysis(wf_res,params_space)
    walkforwarddto.strategy = Strategy
    walkforwarddto.walkforward_input = kwargs
    walkforwarddto.equity_line = getLine(wf_res[0])

    if save:
        dt_string = datetime.today().strftime("%Y_%m_%d_%H_%M")
        filename = '{}_{}_{}.html'.format(Strategy.__name__,
                                       pandas_datas[0].getBarSizeString(),
                                     dt_string)
    else:
        filename = 'analysis.html'

    walkforward_repo(walkforwarddto, outputpath,filename)

    return walkforwarddto


def getLine(strategy,alias='value'):

    for observer in strategy.getobservers():
        linealias = observer.lines._getlinealias(1)
        if linealias ==alias:
            dates = np.array(strategy.datetime.plot())
            ydata = np.array(observer.lines[1].plot())
            dates = num2date(dates)


    return dates,ydata


def getBroker(stdstats=False,opreturn=False,cash=10000,slippage_perc=0.001,
              comission=StocksFixed,
              commvalue=5,
              sizer=bt.sizers.PercentSizer,percents=10,
              commperc=0.01,stake=1000):

    broker = bt.Cerebro(stdstats=stdstats, optreturn=opreturn)
    broker.broker.set_cash(cash)
    comissioninfo = comission(commvalue=commvalue)
    broker.broker.addcommissioninfo(comissioninfo)
    broker.broker.set_slippage_perc(slippage_perc)
    if sizer==bt.sizers.FixedSize:
        broker.addsizer(sizer,stake=stake)
    else:
        broker.addsizer(sizer, percents=percents)

    return broker


def create_wf_analysis(wf_res,param_space):


    df_long_analysis = flatten_wf_multiple_stra(wf_res)

    df_long_analysis['profit_factor']=df_long_analysis['trade_analysis_won_pnl_total']/ \
                            -df_long_analysis['trade_analysis_lost_pnl_total']

    df_analysis_mean = df_long_analysis.mean(numeric_only=True).apply(lambda x: '%.3f' % x)

    df_analysis_sum = df_long_analysis.sum(numeric_only=True).apply(lambda x: '%.3f' % x)


    df_short_analysis = df_analysis_mean[['drawdown_max_drawdown',
                                          'drawdown_max_moneydown',
                                          'trade_analysis_pnl_net_average',
                                          'profit_factor']]
    df_short_analysis = df_short_analysis.append(
        df_analysis_sum[['trade_analysis_total_closed',
                         'trade_analysis_pnl_net_total']])

    df_short_analysis = df_short_analysis.append(
        df_long_analysis['ticker'])

    df_short_analysis = pd.DataFrame(df_short_analysis).T

    wf_trade_list = flatten_wf_trade_list(wf_res)

    walkforwarddto = WalkforwardDto(df_long_analysis=df_long_analysis,
                                    df_short_analysis=df_short_analysis,
                                    wf_trade_list=wf_trade_list,
                                    param_space=param_space)

    return walkforwarddto


class WalkforwardDto():
    def __init__(self,df_long_analysis=pd.DataFrame(),
                 df_short_analysis=pd.DataFrame(),
                 wf_trade_list=pd.DataFrame(),
                 param_space=pd.DataFrame(),
                 strategy=None,
                 walkforward_input=None,
                 equity_line=None):
        self.df_long_analysis = df_long_analysis
        self.df_short_analysis = df_short_analysis
        self.wf_trade_list = wf_trade_list
        self.param_space = param_space
        self.strategy = strategy
        self.walkforward_input = walkforward_input
        self.equity_line = equity_line



def walkforward_repo(walkforwarddto,output_path,filename):


    df_long_analysis = walkforwarddto.df_long_analysis
    df_short_analysis = walkforwarddto.df_short_analysis
    wf_trade_list = walkforwarddto.wf_trade_list
    param_space = walkforwarddto.param_space
    equity_line = walkforwarddto.equity_line
    strategy = walkforwarddto.strategy
    walkforward_params = walkforwarddto.walkforward_input


    df_short_analysis.to_csv(output_path+'analysis.csv',index=False)
    df_long_analysis.to_csv(output_path+'long.csv',index=False)
    wf_trade_list.to_csv(output_path+'trades.csv',index=False)
    param_space.to_csv(output_path+'params.csv',index=False)

    ht = '<h2> %s </h3>\n' % 'Value Observer'
    ht += plot_bokeh_dates_vs_values(equity_line[0],equity_line[1])
    ht += to_html_pretty(df_short_analysis,'short')
    ht += '<pre>' + pprint.pformat(walkforward_params) + '</pre>'
    ht += '<h3> %s </h3>\n' % 'MAE'
    ht += plot_mae(wf_trade_list, notebook=False)
    ht += '<h3> %s </h3>\n' % 'MFE'
    ht += plot_mfe(wf_trade_list, notebook=False)
    ht += to_html_pretty(wf_trade_list, 'trades')
    ht += to_html_pretty(df_long_analysis.T,'long')
    ht += to_html_pretty(param_space.T, 'param_space')
    source_code = inspect.getsourcelines(strategy)[0]
    source_code = ' '.join(source_code)
    ht += highlight(source_code, PythonLexer(),
                    HtmlFormatter(full=True,style='colorful'))


    with open(output_path+filename, 'w') as f:
         f.write(HTML_TEMPLATE1 + ht + HTML_TEMPLATE2)

    os.system('start '+output_path+filename)





def run_walk_forward_multi(**kwargs):

    tickers = kwargs.get('tickers', None)
    outputpath = kwargs.get('outputpath', None)
    walkforwarddto = WalkforwardDto()
    equity_lines = []
    for ticker in tickers:
        print('Working on {}'.format(ticker))
        wfinput = deepcopy(kwargs)
        wfinput['tickers'] = [ticker]
        wf_current = run_walk_forward(**wfinput)
        walkforwarddto.df_long_analysis = \
            walkforwarddto.df_long_analysis.append(wf_current.df_long_analysis)
        walkforwarddto.df_short_analysis = \
            walkforwarddto.df_short_analysis.append(wf_current.df_short_analysis)
        walkforwarddto.wf_trade_list = \
            walkforwarddto.wf_trade_list.append(wf_current.wf_trade_list)
        walkforwarddto.param_space = \
            walkforwarddto.param_space.append(wf_current.param_space)
        equity_lines.append(wf_current.equity_line[1])


    walkforwarddto.strategy = wf_current.strategy
    walkforwarddto.walkforward_input = wf_current.walkforward_input
    walkforwarddto.equity_line = (wf_current.equity_line[0],
                                  np.sum(equity_lines,axis=0))

    dt_string = datetime.today().strftime("%Y_%m_%d_%H_%M")
    filename = '{}_{}.html'.format(walkforwarddto.strategy.__name__,
                                      dt_string)

    walkforward_repo(walkforwarddto,outputpath,filename)



# This is the table pretty printer used above:

def to_html_pretty(df, title=''):
    '''
    Write an entire dataframe to an HTML file
    with nice formatting.
    Thanks to @stackoverflowuser2010 for the
    pretty printer see https://stackoverflow.com/a/47723330/362951
    '''
    ht = ''
    if title != '':
        ht += '<h2> %s </h3>\n' % title
    ht += df.to_html(classes='wide', escape=False)

    return ht

HTML_TEMPLATE1 = '''
<html>
<head>
<style>
  h2 {
    text-align: center;
    font-family: Helvetica, Arial, sans-serif;
  }
  table { 
    margin-left: auto;
    margin-right: auto;
  }
  table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
  }
  th, td {
    padding: 5px;
    text-align: center;
    font-family: Helvetica, Arial, sans-serif;
    font-size: 90%;
  }
  table tbody tr:hover {
    background-color: #dddddd;
  }
  .wide {
    width: 90%; 
  }
</style>
</head>
<body>
'''

HTML_TEMPLATE2 = '''
</body>
</html>
'''
