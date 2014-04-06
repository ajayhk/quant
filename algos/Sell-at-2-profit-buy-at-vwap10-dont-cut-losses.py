# Buy when the price is below vwap or mvag 
# Sell the moment we get 2% profit after commission
# Buy again when the price is below vwap 
# Dont cut losses. Intc will continue to swing, so will reach the buy price some day. In the meanwhile, reap the dividend
# repeat

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

    # context.all_sids = [sid(21724), sid(3951), sid(6295), sid(23709), sid(12959)]  # add some specific securities

# Will be called on every trade event for the securities you specify. 
def handle_data(context, data):
    # If the stock has not yet started trading, exit it
    if context.stock not in data:
        return
    record(INTC=data[context.stock].price)
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    today = exchange_time.day + exchange_time.month*30 + exchange_time.year*365

    # If the price is greater than what we bought earlier by X%, then sell
    # Make sure that we do have some stocks
    if (context.portfolio.positions[context.stock].amount != 0) and \
    (data[context.stock].price > (1+context.profit)*context.portfolio.positions[context.stock].cost_basis) and \
    data[context.stock].price < data[context.stock].vwap(5) :
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
        
   
    # Buy again only when the price is below vwap and we have passed 10 days
    if data[context.stock].price < data[context.stock].vwap(10) :
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


