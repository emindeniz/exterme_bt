from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging
logging.basicConfig(level=logging.INFO)
import backtrader as bt
from datetime import datetime

class SMA_Crossover(bt.Strategy):
    params = (
        ('short', 1),
        ('long',40),
        ('printlog', False),
        ('trading_start',9),
        ('trading_length',6),
        ('filter_off',True),
        ('stop_loss', 0.03),
        ('stop_loss_on',False),
        ('trail_perc',0.05),
        ('trail_perc_on',False),
        # TODO change this parameter name to wf_start
        ('start_date',datetime(1900,1,1)),
        ('end_date',datetime(2100,1,1)),
        ('end_value',0)
    )

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Add a MovingAverageSimple indicator
        self.short_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.short)
        self.long_sma = bt.indicators.SimpleMovingAverage(
            self.datas[0].close, period=self.params.long)

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.4f' % self.dataclose[0])

        # Trading filter to limit times of the day to trade
        trading_hour = self.datas[0].datetime.time(0).hour

        trading_filter = self.params.filter_off or ((trading_hour>=self.params.trading_start)&
        (trading_hour<=(self.params.trading_start+self.params.trading_length)//24))

        walk_forward_filter = ((self.datas[0].datetime.date() >= self.params.start_date.date()) &
                               (self.datas[0].datetime.date() <= self.params.end_date.date()))

        wf_just_finished = ((self.datas[0].datetime.date() > self.params.end_date.date()) &
                               (self.datas[0].datetime.date(-1) <= self.params.end_date.date()))

        # GO LONG if ...
        if self.short_sma[0] > self.long_sma[0] and \
                self.short_sma[-1]<=self.long_sma[-1] and \
            trading_filter and walk_forward_filter:
            # BUY, BUY, BUY!!! (with all possible default parameters)
            for order in list(self.broker.pending):
                self.cancel(order)

            if self.position:
                self.close()

            self.buy(exectype=bt.Order.Market)
            if self.params.trail_perc_on:
                self.sell(exectype=bt.Order.StopTrail,
                          trailpercent=self.params.trail_perc)
            elif self.params.stop_loss_on:
                self.sell(exectype=bt.Order.StopLimit,
                          price=self.dataclose[0] * (1 - self.params.stop_loss))

            self.log('Order submitted by {} {}'.format(self.params.start_date,
                                                       self.params.end_date))

        # GO SHORT IF:
        if self.short_sma[0] < self.long_sma[0] and \
                self.short_sma[-1] >= self.long_sma[-1] and \
                trading_filter and walk_forward_filter:

            # SELL, SELL, SELL!!! (with all possible default parameters)
            for order in list(self.broker.pending):
                self.cancel(order)
            if self.position:
                self.close()

            self.sell()
            if self.params.trail_perc_on:
                self.buy(exectype=bt.Order.StopTrail,
                         trailpercent=self.params.trail_perc)
            elif self.params.stop_loss_on:
                self.buy(exectype=bt.Order.StopTrail,
                         price=self.dataclose[0]*(1+self.params.stop_loss))

        # If we are walking forward we have to close once the period is over
        if wf_just_finished:
            if self.position:
                print('closed')
                self.close()

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - Nothing to do
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED, Price: %.4f, Cost: %.2f, Comm %.2f' %
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  # Sell
                self.log('SELL EXECUTED, Price: %.4f, Cost: %.2f, Comm %.2f' %
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled/Margin/Rejected')

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        self.log('OPERATION PROFIT, GROSS %.4f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def stop(self):
        self.params.end_value = self.broker.get_value()
        self.log('Ending Value %.4f' %
                 self.broker.getvalue(),doprint=True)

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

