"""
# Buy when the price is below vwap or mvag 
# Sell the moment we get 2% profit after commission
# Buy again when the price is below vwap 60 or it is above vwap 20.
# The first is for the reason 
# This is because we dont want to buy it at a high and be stuck with it for ever
# repeat
# Good:
# This seems to be a good algo for stocks like Intel which dont rise much in real life. 
# In those cases, it gives decent 30% return for 0% increase in actual stock
# It works ok for arna so is able to catch some rises but more importantly, doesnt take huge losses
# Bad
# It works bad for stocks like aapl and ddd which rise spectacularly
# In those high rising stocks, it is not able to rise as fast, so it rises say 1000% if stock rises 2000% 
# And these stocks havent fallen much, 
# Conclusion:
# This works well for stocks that rise and fall (spectacularly or even gradually) but works bad for stocks that just go up

Returns:
    Algo=INTC
    2011 Algo 25.5 SPY 0.67 
    2012 Algo -15.2 SPY 13.2
    2013 till may 2014 Algo  17 SPY 31 
"""
import time
from pytz import timezone
import datetime
import pytz
import pandas as pd
import numpy as np
# Put any initialization logic here.  The context object will be passed to
# the other methods in your algorithm.

def initialize(context):
    # context.stock = sid(3951) # add some specific securities    
    context.stock = sid(3951) # add some specific securities    
    context.max = 10000
    context.min = 0
    context.profit = 0.02
    set_commission(commission.PerShare(cost=0.005))
    set_slippage(slippage.FixedSlippage(spread=0.00)) 
    context.last_sold_date = 0
    context.last_bought_date = 0
    context.run_once = 1
    context.buy_and_hold_number = 0
    # context.all_sids = [sid(21724), sid(3951), sid(6295), sid(23709), sid(12959)]  # add some specific securities

# Will be called on every trade event for the securities you specify. 
def handle_data(context, data):
    # If the stock has not yet started trading, exit it
    if context.stock not in data:
        return
    # This is to compare against the buy and hold strategy
    # So buy the first time when the algo runs, and then never sell
    if context.run_once == 1:
        context.buy_and_hold_number = context.max/data[context.stock].price
        log.info(context.stock)
        log.info(context.buy_and_hold_number)
        context.run_once = 0

    total_buy_and_hold = context.buy_and_hold_number * data[context.stock].price
    
    # This is the graph of what would happen if we had just bought and kept
    record(BuyAndHold=total_buy_and_hold)

    record(PortfolioValue=context.portfolio.positions_value \
               + int(context.portfolio.cash))

        
    record(INTC=data[context.stock].price)
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    today = exchange_time.day + exchange_time.month*30 + exchange_time.year*365

    # If the price is greater than what we bought earlier by X%, then sell
    # Make sure that we do have some stocks
    if (context.portfolio.positions[context.stock].amount != 0) and \
    (data[context.stock].price > (1+context.profit)*context.portfolio.positions[context.stock].cost_basis) and \
    data[context.stock].price < data[context.stock].vwap(20) :
        context.order_id = order(context.stock, -context.portfolio.positions[context.stock].amount)
        # Check the order to make sure that it has bought.
        # Right now the filled below returns zero
        stock_order = get_order(context.order_id)
        # The check below shows if the object exists. Only if it exists, should you 
        # refer to it. Otherwise you will get a runtime error
        if stock_order:
            # log the order amount and the amount that is filled  
            # TODO: Make sure to fix the filled field!!!!!!!!!!!!!
            context.last_sold_date = today
            message = ',sell,price={price},amount={amount}'  
            message = message.format(amount=stock_order.amount, price=data[context.stock].price)  
            log.info(message)
            record(SELL=data[context.stock].price)
            return
        
   
    # Buy again only when the price is below vwap 60 (this is for the case where you buy when the price is low
    # Or buy when the price is greater than vwap 20, This is for the case where the price just keeps rising 
    # The first case misses the part where the price keeps rising. We dont want to miss that price rise
    if data[context.stock].price < data[context.stock].vwap(60) or \
    data[context.stock].price > data[context.stock].vwap(20):
        # Need to make sure that you buy only once a day for this algo. 
        context.order_id = order_value(context.stock, context.portfolio.cash)
        # Check the order to make sure that it has bought. Right now the filled below returns zero
        stock_order = get_order(context.order_id)
        # The check below shows if the object exists. Only if it exists, should you 
        # refer to it. Otherwise you will get a runtime error
        if stock_order:
            # log the order amount and the amount that is filled  
            context.last_bought_date = today
            message = ',buy,price={price},amount={amount}'  
            message = message.format(amount=stock_order.amount, price=data[context.stock].price)  
            log.info(message)    
            record(BUY=data[context.stock].price)
            return

    # if we pass 30 days and price is 80% of current price then sell it
    if (int(today) > int(context.last_bought_date) + 30) and \
    (data[context.stock].price > (0.8*context.portfolio.positions[context.stock].cost_basis)) :
    # if (data[context.stock].price < (1-(context.profit*3))*context.portfolio.positions[context.stock].cost_basis):
    # then sell
        context.order_id = order(context.stock, -context.portfolio.positions[context.stock].amount)
        # Check the order to make sure that it has bought.
        # Right now the filled below returns zero
        stock_order = get_order(context.order_id)
        # The check below shows if the object exists. Only if it exists, should you 
        # refer to it. Otherwise you will get a runtime error
        if stock_order:
            # log the order amount and the amount that is filled  
            # TODO: Make sure to fix the filled field!!!!!!!!!!!!!
            context.last_sold_date = today
            message = ',sell,price={price},amount={amount}'  
            message = message.format(amount=stock_order.amount, price=data[context.stock].price)  
            log.info(message)
            record(SELL=data[context.stock].price)
            return

