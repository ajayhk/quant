# Momentum trading
# Trade only once a day
# Buy if the price is less than vwap 20. That means the price is low
# Sell if the price is less than vwap 20 as the price is going down
# Doesnt go too down or too up like the stock does, so is a dampner.
# Safe algo to trade, less returns but less loss


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
    context.stock = sid(24) # add some specific securities    
    context.max = 10000
    context.min = 0
    context.last_traded_date = 0
    set_commission(commission.PerShare(cost=0.005))
    set_slippage(slippage.FixedSlippage(spread=0.00)) 
    # context.all_sids = [sid(21724), sid(3951), sid(6295), sid(23709), sid(12959)]  # add some specific securities

# Will be called on every trade event for the securities you specify. 
def handle_data(context, data):
    # If the stock has not yet started trading, exit it
    if context.stock not in data:
        return
    # Get if we have already traded for the day
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    if(exchange_time.day == context.last_traded_date) :
        return
    # Firstly calculate what your total value is. 
    # It is your total cash + portfolio positions
    value = context.portfolio.cash + context.portfolio.positions_value
    logmsg = ',daily,Cash={cash},portfolio={portVal}'
    log.info(logmsg.format(cash=context.portfolio.cash, portVal=value))
    #yday_close_price = history(2, '1d', 'close_price')  
    #print yday_close_price[data[3951]].values[0] 
    
    # If the price is greater that vwap 20, then buy.
    # This shows that price is moving up. So buy at upward momentum
    if data[context.stock].price < data[context.stock].vwap(20) or \
    data[context.stock].price > data[context.stock].vwap(20) :
        # Buy 10% of the cash you have. 
        # Need to make sure that you buy only once a day for this algo. 
        context.order_id = order_value(context.stock, context.portfolio.cash*0.1)
        # Check the order to make sure that it has bought.
        # Right now the filled below returns zero
        stock_order = get_order(context.order_id)
        # update the date. This is used to make sure we trade only once a day
        context.last_traded_date = exchange_time.day
        # The check below shows if the object exists. Only if it exists, should you 
        # refer to it. Otherwise you will get a runtime error
        if stock_order:
            # log the order amount and the amount that is filled  
            message = ',buy,sid={sid}.stocks={stock},amount={amount}'  
            message = message.format(sid=context.stock,amount=stock_order.amount, stock=stock_order.filled) #cash=context.portfolio.cash)  
            log.info(message)    
            record(BUY=data[context.stock].price)
    # Else check if the price is less that last 20 days
    # If so, it is going down. Time to sell it
    # Maybe we should reduce it to less than 20 days so that we catch the momentum
    if data[context.stock].price > data[context.stock].vwap(10) :
        context.order_id = order_value(context.stock, -context.portfolio.positions_value*0.3)
        # update the date. This is used to make sure we trade only once a day
        context.last_traded_date = exchange_time.day
        # Check the order to make sure that it has bought.
        # Right now the filled below returns zero
        stock_order = get_order(context.order_id)
        # The check below shows if the object exists. Only if it exists, should you 
        # refer to it. Otherwise you will get a runtime error
        if stock_order:
            # log the order amount and the amount that is filled  
            message = ',sell,sid={sid}.stocks={stock},amount={amount}'  
            message = message.format(sid=context.stock,amount=stock_order.amount, stock=stock_order.filled)  
            log.info(message)
            record(SELL=data[context.stock].price)

    
    record(ARNA=data[context.stock].price)
