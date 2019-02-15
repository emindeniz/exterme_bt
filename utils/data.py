import backtrader as bt
import os
import pandas as pd
from datetime import datetime


class Pandas_Data():

    def __init__(self,holdout=False,datapath=None, before=None,
                 suffixes = ['EURUSD','D1','UTC-5','00'],extension='txt'):


        modpath = os.path.dirname(datapath)
        datapath = os.path.join(modpath, '{}.{}'
                                .format('_'.join(suffixes),extension))


        dataframe = pd.read_csv(datapath,
                                parse_dates=False,
                                header=None)

        dataframe.columns = ['date','time','open','high','low','close','volume']

        dataframe['date'] = pd.to_datetime(dataframe['date']+' '+dataframe['time'])

        if not holdout:
            dataframe = dataframe[dataframe.date<datetime(2017,1,1)]

        if before is not None:
            dataframe = dataframe[dataframe.date < before]

        # TODO: Why is this date should be datetime
        self.dataframe = dataframe.set_index(['date'], drop=True)
        self.datapath = datapath
        self.name = suffixes[0]


    def get_feed(self,index=None):

        if index is None:
            feed = bt.feeds.PandasData(
                dataname=self.dataframe,
                name = self.name,
                open=1,
                high=2,
                low=3,
                close=4,
                volume=5)
        else:
            # Create a Data Feed
            feed = bt.feeds.PandasData(
                dataname=self.dataframe.iloc[index],
                name = self.name,
                open=1,
                high=2,
                low=3,
                close=4,
            volume=5)

        feed.csv = False

        return feed

    def get_feedbydate(self,fromdate,todate):

        feed = bt.feeds.PandasData(
                dataname=self.dataframe,
                name = self.name,
                fromdate = fromdate,
                todate = todate,
                open=1,
                high=2,
                low=3,
                close=4,
                volume=5)
        feed.csv = False

        return feed

    def get_start_date(self,index):

        return self.dataframe.iloc[index].index[0]

    def get_end_date(self, index):

        return self.dataframe.iloc[index].index[-1]

    def getBarSize(self):

        td = (self.dataframe.index[1]-self.dataframe.index[0]).total_seconds()

        return td

    def getBarSizeString(self):

        seconds_to_bar = {1800:'30m',
                          60:'1m',
                          86400:'D1',
                          3600:'H1',
                          300:'5m',
                          900:'15m'}

        barsize = self.getBarSize()

        return seconds_to_bar[int(barsize)]





def getPandasDatas(datapath=None, suffixes=None, extension='txt'):

    result = []

    for suffix in suffixes:

        result.append(Pandas_Data(datapath=datapath,
                                  suffixes=suffix,
                                  extension=extension))
    return result


# period = 'H1'
# currency = 'EURUSD'
#
# class CSV_Data():
#
#     def __init__(self,datapath=None):
#
#         if datapath is None:
#             modpath = os.path.dirname('C:\\TickDownloader\\tickdata\\')
#             datapath = os.path.join(modpath, '{}_{}_UTC-5_00.csv'
#                                     .format(currency,period))
#
#         # Create a Data Feed
#         self.feed = bt.feeds.GenericCSVData(
#             dataname=datapath, dtformat='%Y.%m.%d',
#             tmformat='%H:%M',
#             datetime=0,
#             time=1,
#             open=2,
#             high=3,
#             low=4,
#             close=5,
#             todate=datetime(2017,1,1),
#             reverse=False,csv=False)
#
#     def get_feed(self):
#         return self.feed



