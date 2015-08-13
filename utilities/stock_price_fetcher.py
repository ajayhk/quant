import pandas.io.data as stk_fetcher
import datetime as dt
from datetime import timedelta
from pandas.tseries.offsets import BDay


ticker = "YHOO"
data_source = 'yahoo'


def get_last_price(stk_ticker):
	start_date = dt.datetime.today()
	if start_date.weekday() == 5 or start_date.weekday() == 6:
		# Saturday or sunday 
		start_date = start_date - BDay(1)
	end_date = start_date
	stock_price = stk_fetcher.DataReader(stk_ticker, data_source, start_date, end_date)
	return stock_price


price = get_last_price(ticker)
print type(price)
print price['Adj Close']