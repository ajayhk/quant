from datetime import datetime
import pytz

from zipline import TradingAlgorithm
from zipline.utils.factory import load_from_yahoo

from zipline.api import order


def initialize(context):
    context.test = 10


def handle_date(context, data):
    order('AAPL', 10)
    print(context.test)


if __name__ == '__main__':
    import pylab as pl
    start = datetime(2008, 1, 1, 0, 0, 0, 0, pytz.utc)
    end = datetime(2010, 1, 1, 0, 0, 0, 0, pytz.utc)
    data = load_from_yahoo(stocks=['AAPL'], indexes={}, start=start,
                           end=end)
    data = data.dropna()
    algo = TradingAlgorithm(initialize=initialize,
                            handle_data=handle_date)
    results = algo.run(data)
    results.portfolio_value.plot()
    pl.show()
