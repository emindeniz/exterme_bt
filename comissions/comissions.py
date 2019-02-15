import backtrader as bt

class StocksFixed(bt.CommInfoBase):
    
    params = (
      ('commvalue', 0),
      ('commtype', bt.CommInfoBase.COMM_FIXED))


    def _getcommission(self, size, price, pseudoexec):

        return self.params.commvalue


class StocksPerc(bt.CommInfoBase):
    params = (
        ('commvalue', 0),
        ('commtype', bt.CommInfoBase.COMM_PERC))

    def _getcommission(self, size, price, pseudoexec):
        return size*price*self.params.commvalue
