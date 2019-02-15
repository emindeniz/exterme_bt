from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging

logging.basicConfig(level=logging.INFO)
import backtrader as bt
from datetime import datetime
import numpy as np


class SMACrossoverMulti(bt.Strategy):
    params = (
        ('fast', 0.05),
        ('slow', 2),
        ('printlog', False),
        ('trading_start', 9),
        ('trading_length', 6),
        ('filter_off', True),
        ('stop_loss', 0.03),
        ('stop_loss_on', False),
        ('trail_perc', 0.05),
        ('trail_perc_on', False),
        ('start_date', datetime(1900, 1, 1)),
        ('end_date', datetime(2100, 1, 1)),
        ('end_value', 0),
        ('training_end_value', 0),
    )

    def __init__(self):

        self.fastma = dict()
        self.slowma = dict()
        self.regime = dict()

        for d in self.getdatanames():
            # The moving averages
            self.fastma[d] = bt.indicators.SimpleMovingAverage(self.getdatabyname(d).close,  # The symbol for the moving average
                                                       period=self.params.fast,  # Fast moving average
                                                       plotname="FastMA: " + d)
            self.slowma[d] = bt.indicators.SimpleMovingAverage(self.getdatabyname(d).close,  # The symbol for the moving average
                                                       period=self.params.slow,  # Slow moving average
                                                       plotname="SlowMA: " + d)

            # Get the regime
            self.regime[d] = self.fastma[d] - self.slowma[d]  # Positive when bullish


        self.params.training_end_value = self.params.end_value

    def next(self):

        for name in self.getdatanames():

            data = self.getdatabyname(name)

            # Trading filter to limit times of the day to trade
            trading_hour = data.datetime.time(0).hour

            trading_filter = self.gettradingfilter(trading_hour)

            walk_forward_filter = ((data.datetime.date() >= self.params.start_date.date()) &
                                   (data.datetime.date() <= self.params.end_date.date()))

            wf_just_finished = ((data.datetime.date(-1) > self.params.end_date.date()) &
                                (data.datetime.date(-2) <= self.params.end_date.date()))


            buy_signal = self.regime[name][0] >0 and self.regime[name][-1]<=0
            sell_signal = self.regime[name][0] <0 and self.regime[name][-1]>=0

            if buy_signal and trading_filter and walk_forward_filter:
                self.buybyname(name=name)

            elif sell_signal and trading_filter and walk_forward_filter:
                self.sellbyname(name=name)

            # If we are walking forward we have to close once the period is over
            if wf_just_finished:
                if self.getpositionbyname(name):
                    print('closed')
                    self.close(data=data,exectype=bt.Order.Market)

    def gettradingfilter(self,trading_hour):

        trading_filter = self.params.filter_off or \
                         ((trading_hour >= self.params.trading_start) &
        (trading_hour <= ((self.params.trading_start + self.params.trading_length) % 24)))

        return trading_filter

    def getendofday(self,data):
        try:
            return data.datetime.date(0) < data.datetime.date(3)
        except:
            return True

    def getOrderType(self,order):
        exectypes = {bt.Order.Stop:'stop',
                     bt.Order.Market:'market',
                     bt.Order.StopLimit:'stoplimit',
                     bt.Order.StopTrail:'stoptrail'}
        return exectypes[order.params.exectype]


    def buybyname(self,name):

        data = self.getdatabyname(name=name)

        # BUY, BUY, BUY!!! (with all possible default parameters)
        for order in list(self.broker.pending):
            if order.params.data._name==name:
                self.cancel(order)

        self.buy(exectype=bt.Order.Market,data=data)
        if self.params.trail_perc_on:
            self.sell(exectype=bt.Order.StopTrail,
                      trailpercent=self.params.trail_perc,
                      data=data)

        elif self.params.stop_loss_on:
            self.sell(exectype=bt.Order.Stop,
                      price=data.close[0] * (1 - self.params.stop_loss),
                      data=data)

        self.log('Order submitted by {} {} {}'.format(self.params.start_date,
                                                   self.params.end_date,
                                                      name))

    def sellbyname(self,name):

        data = self.getdatabyname(name=name)

        # SELL, SELL, SELL!!! (with all possible default parameters)
        for order in list(self.broker.pending):
            if order.params.data._name == name:
                self.cancel(order)

        self.sell(exectype=bt.Order.Market,data=data)
        if self.params.trail_perc_on:
            self.buy(exectype=bt.Order.StopTrail,
                     trailpercent=self.params.trail_perc,
                     data=data)
        elif self.params.stop_loss_on:
            self.buy(exectype=bt.Order.Stop,
                     price=data.close[0] * (1 + self.params.stop_loss),
                     data=data)

        self.log('Order submitted by {} {} {}'.format(self.params.start_date,
                                                   self.params.end_date,
                                                      name))

    def notify_order(self, order):

        if order.status in [order.Submitted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log('Order Submitted {}-{}'.
                     format(order.params.data._name,
                     self.getOrderType(order)))
            return

        if order.status in [order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            self.log('Order Accepted {}-{}'.
                     format(order.params.data._name,
                     self.getOrderType(order)))
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: {:.4f}, Size: {:.4f}, '
                    'Comm:{:.4f}, Ticker:{} OrderType:{} Position:{}'.format
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm,
                     order.params.data._name,
                     self.getOrderType(order),
                     self.getpositionbyname(order.params.data._name)))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: {:.4f}, '
                         'Size: {:.4f}, Comm:{:.4f},'
                         'Ticker:{}, OrderType:{} Position {}'.format
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm,
                          order.params.data._name,
                          self.getOrderType(order),
                          self.getpositionbyname(order.params.data._name)))

            self.bar_executed = len(self)

        if order.status in [order.Margin]:
            self.log('Order Margin {}'.format(order.params.data._name))
        if order.status in [order.Canceled]:
            self.log('Order Canceled {}'.format(order.params.data._name))
        if order.status in [order.Rejected]:
            self.log('Order Rejected {}'.format(order.params.data._name))

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS {:.2f}, NET {:.2f} '
                 'ticker {} Existing position {}'.
                 format(trade.pnl, trade.pnlcomm,trade.data._name,
                        trade.price, self.getpositionbyname(trade.data._name)) )

    def stop(self):
        self.params.end_value = self.broker.get_value()
        self.log('Ending Value %.4f' %
                 self.broker.getvalue(),doprint=True)

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:

            dt = dt or self.datas[0].datetime.datetime(0)
            print('%s, %s' % (dt.isoformat(), txt))