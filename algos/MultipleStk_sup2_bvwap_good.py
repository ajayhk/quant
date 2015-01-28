"""
Buy when the price is below vwap or mvag 
Sell the moment we get 2% profit after commission
Buy again when the price is below vwap 60 or it is above vwap 20.
The first is for the reason 
This is because we dont want to buy it at a high and be stuck with it for ever
repeat

Good:
This seems to be a good algo for stocks like Intel which dont rise much in real life. 
In those cases, it gives decent 30% return for 0% increase in actual stock
It works ok for arna so is able to catch some rises but more importantly, doesnt take huge losses

Bad
It works bad for stocks like aapl and ddd which rise spectacularly
In those high rising stocks, it is not able to rise as fast, so it rises say 1000% if stock rises 2000% 
And these stocks havent fallen much, 

Conclusion:
This works well for stocks that rise and fall (spectacularly or even gradually) but works bad for stocks that just go up

Returns:
    2011 Algo  13.3 RYH 5.9
    2012 Algo  10 RYH 17.7
    2013 Algo  RYH 
    2014 Algo  RYH 
    2015 Algo  RYH 
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
    set_benchmark(symbol('RYH'))

    context.num_of_stocks_to_track = 600
    context.no_of_stocks_to_buy = 20
    context.max = 100000
    context.min = 0
    context.profit = 0.02
    context.market_cap_max = 5000000000
    context.market_cap_min = 500000000
    context.distress_sale_value = 0.5
    context.run_once = 1
    context.mstar_group_code = 20636

    context.last_sold_date = {}
    context.last_bought_date = {}


def before_trading_start(context): 
    """
      Called before the start of each trading day. 
      It updates our universe with the
      securities and values found from get_fundamentals.
    """
    
    
    # Setup SQLAlchemy query to screen stocks based on PE ration
    # and industry sector. Then filter results based on 
    # market cap and shares outstanding.
    # We limit the number of results to num_stocks and return the data
    # in descending order.
    fundamental_df = get_fundamentals(
        query(
            # put your query in here by typing "fundamentals."
            fundamentals.valuation_ratios.pe_ratio,
            fundamentals.valuation.market_cap,
            fundamentals.asset_classification.morningstar_sector_code,
            fundamentals.asset_classification.morningstar_industry_group_code
        )
        .filter(fundamentals.valuation.market_cap != None)
        .filter(fundamentals.valuation.shares_outstanding != None)
        .filter(fundamentals.asset_classification.morningstar_industry_group_code == context.mstar_group_code)
        .filter(fundamentals.valuation.market_cap < context.market_cap_max)
        .filter(fundamentals.valuation.market_cap > context.market_cap_min)
        .order_by(fundamentals.valuation.market_cap.desc())
        .limit(context.num_of_stocks_to_track)
    )

    for stock in fundamental_df:
        #sector = fundamental_df[stock]['morningstar_sector_code']
        market_cap = fundamental_df[stock]['market_cap']
        group_code = fundamental_df[stock]['morningstar_industry_group_code']
        #log.info("Stock  %s and market cap %s and group code %s" %(stock, market_cap, group_code))
        
    # Filter out only stocks with that particular sector
    context.stocks = [stock for stock in fundamental_df]
    
    # Update context.fundamental_df with the securities
    context.fundamental_df = fundamental_df[context.stocks]

    update_universe(context.fundamental_df.columns.values)   
    
    
def buy_stock(context, stock, data):
    # Get if we have already traded for the day
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    today = exchange_time.day + exchange_time.month*30 + exchange_time.year*365
    # Dont buy on same date that you bought/sold
    if stock in context.last_bought_date:
        if(today == context.last_bought_date[stock]):
            return
    if (context.portfolio.positions[stock].amount == 0):
        amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks_to_buy))
    else :
        amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks_to_buy) - context.portfolio.positions[stock].amount*context.portfolio.positions[stock].cost_basis)
    # dont buy small quantities
    # If it is less than 0.1% of initial cash, dont buy
    if amount_to_buy < context.max*.001:
            return
    # If it is less than 10 stocks, dont buy
    if amount_to_buy/data[stock].price < 10:
            return
    context.order_id = order_value(stock, (amount_to_buy))
            
    # Check the order to make sure that it has bought.
    # Right now the filled below returns zero
    stock_order = get_order(context.order_id)
    # The check below shows if the object exists. Only if it exists, should you 
    # refer to it. Otherwise you will get a runtime error
    if stock_order:
        # update the date. This is used to make sure we trade only once a day
        context.last_bought_date[stock] = today
        # log the order amount and the amount that is filled  
        message = ',buy,sid={sid}.stk={stk},amt={amt},portv={portv}, posv={posv}'  
        message = message.format(sid=stock,amt=stock_order.amount, stk=stock_order.filled, portv=context.portfolio.portfolio_value, posv=context.portfolio.positions_value)  
        log.info(message)    
        record(BUY=data[stock].price)

        
        
def sell_stock(context, stock, data):        
    # No stocks to sell. Return
    if(context.portfolio.positions[stock] == 0):
        return
    # Get if we have already traded for the day
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    today = exchange_time.day + exchange_time.month*30 + exchange_time.year*365
    # Sell all stocks
    context.order_id = order_target(stock, 0)
    # Check the order to make sure that it has bought.
    # Right now the filled below returns zero
    stock_order = get_order(context.order_id)
    # The check below shows if the object exists. Only if it exists, should you 
    # refer to it. Otherwise you will get a runtime error
    if stock_order:
        # update the date. This is used to make sure we trade only once a day
        context.last_sold_date[stock] = today
        # log the order amount and the amount that is filled  
        message = ',sell,sid={sid}.stocks={stock},amount={amount}'  
        message = message.format(sid=stock,amount=stock_order.amount, stock=stock_order.filled)  
        log.info(message)
        record(SELL=data[stock].price)
        #del context.last_bought_date[stock] 
        
# Will be called on every trade event for the securities you specify. 
def handle_data(context, data):
    
    record(PortfolioValue=context.portfolio.positions_value \
               + int(context.portfolio.cash))
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    today = exchange_time.day + exchange_time.month*30 + exchange_time.year*365

    # If the price is greater than what we bought earlier by X%, then sell
    # Make sure that we do have some stocks     '
    for stock in context.stocks:
        if stock in data:
            if (context.portfolio.positions[stock].amount != 0) and \
    (data[stock].price > (1+context.profit)*context.portfolio.positions[stock].cost_basis) and \
    data[stock].price < data[stock].vwap(20) :
                sell_stock(context, stock, data)
                
   
    # Buy again only when the price is below vwap 60 (this is for the case where you buy when the price is low
    # Or buy when the price is greater than vwap 20, This is for the case where the price just keeps rising 
    # The first case misses the part where the price keeps rising. We dont want to miss that price rise
    for stock in context.stocks:
        if stock in data:
            if data[stock].price < data[stock].vwap(60) or \
                data[stock].price > data[stock].vwap(20):
                buy_stock(context, stock, data)
        

    # if we pass 30 days and price is 80% of current price then sell it
    for stock in context.stocks:
        if stock in data:
            if stock in context.last_bought_date:
                if (today > context.last_bought_date[stock] + 30) and \
                    (data[stock].price > (context.distress_sale_value*context.portfolio.positions[stock].cost_basis)) :
                    sell_stock(context, stock, data)
