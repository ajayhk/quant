#!/usr/bin/env python
from zipline import TradingAlgorithm
from zipline.transforms import MovingAverage
from zipline.utils.factory import load_from_yahoo

from datetime import datetime
import pytz
import matplotlib.pyplot as plt

class DualMovingAverage(TradingAlgorithm):
    """Dual Moving Average Crossover algorithm.

    This algorithm buys apple once its short moving average crosses
    its long moving average (indicating upwards momentum) and sells
    its shares once the averages cross again (indicating downwards
    momentum).

    """
    def initialize(self, short_window=100, long_window=400):
        # Add 2 mavg transforms, one with a long window, one
        # with a short window.
        self.add_transform(MovingAverage, 'short_mavg', ['price'],
                           window_length=short_window)

        self.add_transform(MovingAverage, 'long_mavg', ['price'],
                           window_length=long_window)

        # To keep track of whether we invested in the stock or not
        self.invested = False

    def handle_data(self, data):
        short_mavg = data['AAPL'].short_mavg['price']
        long_mavg = data['AAPL'].long_mavg['price']
        buy = False
        sell = False

    # Has short mavg crossed long mavg?
        if short_mavg > long_mavg and not self.invested:
            self.order('AAPL', 100)
            self.invested = True
            buy = True
        elif short_mavg < long_mavg and self.invested:
            self.order('AAPL', -100)
            self.invested = False
            sell = True

    # Record state variables. A column for each
    # variable will be added to the performance
    # DataFrame returned by .run()
        self.record(short_mavg=short_mavg,
                    long_mavg=long_mavg,
                    buy=buy,
                    sell=sell)

# Load data
start = datetime(1990, 1, 1, 0, 0, 0, 0, pytz.utc)
end = datetime(2002, 1, 1, 0, 0, 0, 0, pytz.utc)
data = load_from_yahoo(stocks=['AAPL'], indexes={}, start=start,
                   end=end, adjusted=False)

# Run algorithm
dma = DualMovingAverage()
perf = dma.run(data)

# Plot results
fig = plt.figure()
ax1 = fig.add_subplot(211,  ylabel='Price in $')
data['AAPL'].plot(ax=ax1, color='r', lw=2.)
perf[['short_mavg', 'long_mavg']].plot(ax=ax1, lw=2.)

ax1.plot(perf.ix[perf.buy].index, perf.short_mavg[perf.buy],
         '^', markersize=10, color='m')
ax1.plot(perf.ix[perf.sell].index, perf.short_mavg[perf.sell],
         'v', markersize=10, color='k')

ax2 = fig.add_subplot(212, ylabel='Portfolio value in $')
perf.portfolio_value.plot(ax=ax2, lw=2.)

ax2.plot(perf.ix[perf.buy].index, perf.portfolio_value[perf.buy],
         '^', markersize=10, color='m')
ax2.plot(perf.ix[perf.sell].index, perf.portfolio_value[perf.sell],
         'v', markersize=10, color='k')
