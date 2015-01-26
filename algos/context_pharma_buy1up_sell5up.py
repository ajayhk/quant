"""
    Trading Strategy using Fundamental Data
    
    1. Take list of only pharma stocks
    2. Finalize number of stocks to track and buy
    3. Buy the stock if it is showing potential of rising. Buy if it is 1% more than last 5 minute's price
    4. Sell the stock if it rises 5% above the cost price
    5. Dont buy if less than 10 stocks or other such conditions
    6. Performing slightly better than the benchmark which is RYH for pharma
"""

import pandas as pd
import numpy as np
import time
from pytz import timezone
import datetime
import pytz

def initialize(context):
    # give exception if stock not present
    #set_nodata_policy(NoDataPolicy.EXCEPTION)
    
    # Sector mappings
    context.sector_mappings = {
       20636: "Minor Pharma"
    }
    set_benchmark(symbol('RYH'))
    #set_commission(commission.PerTrade(cost=0.03))
    #set_slippage(slippage.VolumeShareSlippage(volume_limit=0.25, price_impact=0.1))

    context.num_of_stocks_to_track = 600
    context.no_of_stocks_to_buy = 20
    context.buy_time_hour = 9
    context.buy_time_minute = 15
    context.max = 100000
    context.mstar_group_code = 20636
    context.market_cap_max = 5000000000
    context.market_cap_min = 500000000
    context.days_to_sell = 1
    context.perc_incr_to_sell = 1.05
    context.perc_incr_to_buy = 1.01
    
    # Dictionaries
    context.buy_date = {}
    context.last_traded_date = {}
    context.prev_day_price = {}
    context.prev_min_price_1 = {}
    context.prev_min_price_2 = {}
    context.prev_min_price_3 = {}
    context.prev_min_price_4 = {}
    context.prev_min_price_5 = {}
    # Rebalance monthly on the first day of the month at market open
    schedule_function(monthstart,
                      date_rule=date_rules.month_start(),
                      time_rule=time_rules.market_open())

    schedule_function(dayend,
                      time_rule=time_rules.market_close())

def monthstart(context, data):
    for stock in context.portfolio.positions:
        if stock in context.fundamental_df:    
            #log.info("Stocks %s in positions" %(stock))
            pass

    for stock in context.fundamental_df:
        #log.info("Stocks %s in basket %s" 
        #             % (stock.symbol, 
        #                context.sector_mappings[context.fundamental_df[stock]['morningstar_industry_group_code']]))
        pass
    
    
def dayend(context, data):
    for stock in context.stocks:
        if stock in data:
            context.prev_day_price[stock] = data[stock].close_price        
        #log.info("Stock  %s price %s" %(stock, context.prev_day_price[stock]))
    
    
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
    if stock in context.last_traded_date:
        if(today == context.last_traded_date[stock]):
            return
    if (context.portfolio.positions[stock].amount == 0):
        amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks_to_buy))
    else :
        amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks_to_buy) - context.portfolio.positions[stock].amount*context.portfolio.positions[stock].cost_basis)
    # dont buy small quantities
    # If it is less than 0.1% of initial cash, dont buy
    if amount_to_buy*data[stock].price < context.max*.001:
            return
    # If it is less than 10 stocks, dont buy
    if amount_to_buy < 10:
            return
    context.order_id = order_value(stock, (amount_to_buy))
            
    # Check the order to make sure that it has bought.
    # Right now the filled below returns zero
    stock_order = get_order(context.order_id)
    # The check below shows if the object exists. Only if it exists, should you 
    # refer to it. Otherwise you will get a runtime error
    if stock_order:
        # update the date. This is used to make sure we trade only once a day
        context.last_traded_date[stock] = today
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
        context.last_traded_date[stock] = today
        # log the order amount and the amount that is filled  
        message = ',sell,sid={sid}.stocks={stock},amount={amount}'  
        message = message.format(sid=stock,amount=stock_order.amount, stock=stock_order.filled)  
        log.info(message)
        record(SELL=data[stock].price)
        del context.buy_date[stock]       
def handle_data(context, data):
    """
      Code logic to run during the trading day.
      handle_data() gets called every bar.
    """
    # Get if we have already traded for the day
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    today = exchange_time.day + exchange_time.month*30 + exchange_time.year*365
    curr_price = 0
    prev_min_price = 0
    for stock in context.stocks:
        if stock in data:
            if exchange_time.minute % 5 == 1:
                if stock in context.prev_min_price_1:
                    curr_price = data[stock].price
                    prev_min_price = context.prev_min_price_1[stock]
            if exchange_time.minute % 5 == 2:
                if stock in context.prev_min_price_2:
                    curr_price = data[stock].price
                    prev_min_price = context.prev_min_price_2[stock]
            if exchange_time.minute % 5 == 3:
                if stock in context.prev_min_price_3:
                    curr_price = data[stock].price
                    prev_min_price = context.prev_min_price_3[stock]
            if exchange_time.minute % 5 == 4:
                if stock in context.prev_min_price_4:
                    curr_price = data[stock].price
                    prev_min_price = context.prev_min_price_4[stock]
            if exchange_time.minute % 5 == 0:
                if stock in context.prev_min_price_5:
                    curr_price = data[stock].price
                    prev_min_price = context.prev_min_price_5[stock]

            if curr_price > context.perc_incr_to_buy*prev_min_price:
                #log.info("Price jump Stock  %s Prev price = %s Current price %s" %(stock, prev_min_price, curr_price))
                buy_stock(context, stock, data)
                context.buy_date[stock] = today
        
    # Two days have passed. Sell it
    for stock in context.stocks:
        if stock in data:
            if stock in context.buy_date:
                if today > context.buy_date[stock] + context.days_to_sell:
                    # dont sell the stock at a loss
                    if stock in context.last_traded_date:
                        if data[stock].price > context.perc_incr_to_sell*context.portfolio.positions[stock].cost_basis:
                            # sell it
                            sell_stock(context, stock, data)
    for stock in context.stocks:
        if stock in data:
            if exchange_time.minute % 5 == 1:
                context.prev_min_price_1[stock] = data[stock].price
            if exchange_time.minute % 5 == 2:
                context.prev_min_price_2[stock] = data[stock].price
            if exchange_time.minute % 5 == 3:
                context.prev_min_price_3[stock] = data[stock].price
            if exchange_time.minute % 5 == 4:
                context.prev_min_price_4[stock] = data[stock].price
            if exchange_time.minute % 5 == 0:
                context.prev_min_price_5[stock] = data[stock].price
    