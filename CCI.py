from __future__ import (absolute_import, division, print_function,
                        unicode_literals)
import logging
logging.basicConfig(level=logging.DEBUG)
import backtrader as bt

class CCI(bt.Strategy):
    params = (
        ('period', 20),
        ('printlog', False),
        ('trading_start',9),
        ('trading_length',3),
        ('stop_loss',0.03)
    )

    def log(self, txt, dt=None, doprint=False):
        ''' Logging function fot this strategy'''
        if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # Add a MovingAverageSimple indicator
        self.cci = bt.indicators.CommodityChannelIndex(period=self.params.period)


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

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.4f' % self.dataclose[0])
        trading_hour = self.datas[0].datetime.time(0).hour
        trading_filter = ((trading_hour>=self.params.trading_start)&
        (trading_hour<=self.params.trading_start+self.params.trading_length))
        # if self.position:
        # GO LONG if ...
        if self.cci[0] <= -100  and \
                self.cci[-1] > -100 and trading_filter:
            # BUY, BUY, BUY!!! (with all possible default parameters)
            for order in list(self.broker.pending):
                self.cancel(order)
            if self.position:
                self.close()
                self.log('BUY CREATE, %.4f' % self.dataclose[0])
            self.buy()
            self.sell(exectype=bt.Order.Stop,price=self.dataclose[0]*(1-self.params.stop_loss))

        # GO SHORT IF:
        if self.cci[0] >= 100  and \
                self.cci[-1] < 100 and trading_filter:
            # SELL, SELL, SELL!!! (with all possible default parameters)
            self.log('SELL CREATE, %.4f' % self.dataclose[0])
            # Keep track of the created order to avoid a 2nd order
            for order in list(self.broker.pending):
                self.cancel(order)
            if self.position:
                self.close()
            self.sell()
            self.buy(exectype=bt.Order.Stop,price=self.dataclose[0]*(1+self.params.stop_loss))

    def stop(self):
        self.thevalue = self.broker.get_value()
        self.thecash = self.broker.get_cash()
        self.log('Ending Value %.4f' %
                 self.broker.getvalue(), doprint=True)