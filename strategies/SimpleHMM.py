from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging
logging.basicConfig(level=logging.INFO)
import backtrader as bt
from datetime import datetime
import numpy as np

class SimpleHMM(bt.Strategy):
    params = (
        ('name','SimpleHMM'),
        ('no_no', 0.5),
        ('no_long', 0.5),
        ('long_no',0.5),
        ('long_long', 0.5),
        ('no_short', 0.5),
        ('short_no', 0.5),
        ('short_short', 0.5),
        ('short_long', 0.5),
        ('long_short', 0.5),
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
        self.state = 'no'


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

        if self.state=='no':
            p= [self.params.no_long,self.params.no_no,self.params.no_short]
            p = np.array(p)/np.sum(p)
            action=np.random.choice(['long','none','short'],p=p)
        elif self.state=='long':
            p = [self.params.long_long, self.params.long_no, self.params.long_short]
            p = np.array(p) / np.sum(p)
            action = np.random.choice(['none', 'no', 'short'])
        elif self.state=='short':
            p = [self.params.short_long, self.params.short_no, self.params.short_short]
            p = np.array(p) / np.sum(p)
            action = np.random.choice(['long', 'no', 'none'])

        # GO LONG if ...
        if action=='long' and \
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

            self.state = 'long'

        # GO SHORT IF:
        elif action=='sell' and \
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
                self.buy(exectype=bt.Order.StopLimit,
                         price=self.dataclose[0]*(1+self.params.stop_loss))

            self.state='short'

        # GO SHORT IF:
        elif action=='no' and \
                trading_filter and walk_forward_filter:

            # SELL, SELL, SELL!!! (with all possible default parameters)
            for order in list(self.broker.pending):
                self.cancel(order)
            if self.position:
                self.close()

            self.state='no'


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

