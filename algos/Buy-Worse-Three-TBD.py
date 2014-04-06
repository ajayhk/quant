''' 
    This algorithm uses fetcher to fetch the worst three stocks of one day
    And then buys it exactly one week later (tunable parameter)
    Then sells it when it hits a 50% profit
    Make sure that the stock has a good volume of trade and a big enough market cap
'''
########### IMPORT THE LIBRARIES USED IN THE ALGORITHM ####################################
import datetime
import pytz
import pandas as pd
from zipline.utils.tradingcalendar import get_early_closes

########### INITIALZE() IS RUN ONCE (OR IN LIVE TRADING ONCE EACH DAY BEFORE TRADING) #####
def initialize(context):
    
    context.stock           = sid(42118)
    context.max = 10000
    context.min = 0
    context.profit = 0.01
    context.buy_and_hold_number = 0
    context.execute_once = 1
    context.lastbuymonth = 0
    context.lastbuyyear = 0

    set_commission(commission.PerShare(cost=0.005))
    set_slippage(slippage.FixedSlippage(spread=0.00)) 

########### HANDLE_DATA() IS RUN ONCE PER MINUTE #######################
def handle_data(context, data):
    
    # If the stock has not yet started trading, exit it
    if context.stock not in data:
        return
    
    # Get the current exchange time, in local timezone: 
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')

    if context.execute_once == 1:
        context.buy_and_hold_number = context.max/data[context.stock].price
        context.execute_once = 0
    
    record(PRICE=data[context.stock].price)
    
    record(PortfolioValue=context.portfolio.positions_value \
           + int(context.portfolio.cash))
    
    record(BuyAndHold=context.buy_and_hold_number * data[context.stock].price)

    
    record(InitialCapital=context.max)
    

    if data[context.stock].price < 0.7*data[context.stock].vwap(20) and \
    context.lastbuymonth != exchange_time.month and \
    context.lastbuyyear != exchange_time.year :
    
        # do all the buying here
        context.order_id = order_value(context.stock, 0.3*context.portfolio.cash)
        # Check the order to make sure that it has bought. Right now the filled below returns zero
        stock_order = get_order(context.order_id)
        # The check below shows if the object exists. Only if it exists, should you 
        # refer to it. Otherwise you will get a runtime error
        if stock_order:
            message = ',buy,price={price},amount={amount}'  
            message = message.format(amount=stock_order.amount, price=data[context.stock].price)  
            log.info(message)    
            record(BUY=data[context.stock].price)
            context.lastbuymonth = exchange_time.month 
            context.lastbuyyear = exchange_time.year 
            return
        
        return
    

