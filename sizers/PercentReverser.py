import backtrader as bt

class PercentReverser(bt.Sizer):
    '''This sizer return percents of available cash

    Params:
      - ``percents`` (default: ``20``)
    '''

    params = (
        ('percents', 20),
    )

    def __init__(self):
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        position = self.broker.getposition(data)
        if not position:
            size = cash / data.close[0] * (self.params.percents / 100)
        elif not ((position.size>0)^isbuy):
            size = 0
        else:
            size = position.size * 2
        print(size)
        return size