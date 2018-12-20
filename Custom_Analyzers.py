# Trade list similar to Amibroker output
import backtrader as bt
import pandas as pd
import numpy as np
import sys

class trade_list(bt.Analyzer):

    def get_analysis(self):

        return pd.DataFrame(self.trades)


    def __init__(self):

        self.trades = []
        self.cumprofit = 0.0
        self.cumprofitpcnt = 0.0
        self.highwatermark = 0.0


    def notify_trade(self, trade):

        if trade.isclosed:

            brokervalue = self.strategy.broker.getvalue()

            dir = 'short'
            if trade.history[0].event.size > 0: dir = 'long'

            pricein = trade.history[len(trade.history)-1].status.price
            priceout = trade.history[len(trade.history)-1].event.price
            datein = bt.num2date(trade.history[0].status.dt)
            dateout = bt.num2date(trade.history[len(trade.history)-1].status.dt)
            if trade.data._timeframe >= bt.TimeFrame.Days:
                datein = datein.date()
                dateout = dateout.date()

            pcntchange = 100 * priceout / pricein - 100
            pnl = trade.history[len(trade.history)-1].status.pnlcomm
            pnlpcnt = 100 * pnl / brokervalue
            barlen = trade.history[len(trade.history)-1].status.barlen
            pbar = pnl / (barlen + sys.float_info.epsilon)
            self.cumprofit += pnl
            self.cumprofitpcnt +=pnlpcnt

            size = value = 0.0
            for record in trade.history:
                if abs(size) < abs(record.status.size):
                    size = record.status.size
                    value = record.status.value

            highest_in_trade = max(trade.data.high.get(ago=0, size=barlen+1))
            lowest_in_trade = min(trade.data.low.get(ago=0, size=barlen+1))
            hp = 100 * (highest_in_trade - pricein) / pricein
            lp = 100 * (lowest_in_trade - pricein) / pricein
            if dir == 'long':
                mfe = hp
                mae = lp
            if dir == 'short':
                mfe = -lp
                mae = -hp

            self.trades.append({'ref': trade.ref, 'ticker': trade.data._name[:5],
                                'dir': dir,'datein': datein,
                                'pricein': pricein, 'dateout': dateout,
                                'priceout': priceout,'chng%': round(pcntchange, 2),
                                'pnl': pnl, 'pnl%': round(pnlpcnt, 2),
                                'size': size, 'value': value, 'cumpnl': self.cumprofit,
                                'nbars': barlen, 'pnl/bar': round(pbar, 2),
                                'mfe%': round(mfe, 2), 'mae%': round(mae, 2)})