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
    context.max = 10000
    context.min = 0
    set_commission(commission.PerShare(cost=0.005))
    set_slippage(slippage.FixedSlippage(spread=0.00)) 
    stocks = [sid(21724), sid(22257), sid(18522), sid(351), sid(6295), sid(20914)]
    context.stocks = stocks # add some specific securities    
    context.no_of_stocks = 6

    context.buy_and_hold_number = [0]*context.no_of_stocks
    context.run_once = 1
    context.last_traded_date = [0]*context.no_of_stocks
    context.lastbuymonth = [0]*context.no_of_stocks
    context.lastbuyyear = [0]*context.no_of_stocks
    context.last_bought_date = [0]*context.no_of_stocks
    context.last_sold_date = [0]*context.no_of_stocks


# Will be called on every trade event for the securities you specify. 
def handle_data(context, data):
    # If the stock has not yet started trading, exit it

    # Get if we have already traded for the day
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')

    today = exchange_time.day + exchange_time.month*30 + exchange_time.year*365

    
    
    #### Begin buy and hold recording ####
    # This is to compare against the buy and hold strategy
    # So buy the first time when the algo runs, and then never sell
    if context.run_once == 1:
        i = 0
        for stock in context.stocks :
            context.buy_and_hold_number[i] = (context.max/context.no_of_stocks)/data[stock].price
            log.info(stock)
            log.info(context.buy_and_hold_number[i])
            context.run_once = 0
            i = i + 1
    
    i = 0
    total_buy_and_hold = 0
    for stock in context.stocks :
        # This is the graph of what would happen if we had just bought and kept
        total_buy_and_hold = total_buy_and_hold + context.buy_and_hold_number[i] * data[stock].price
        i = i + 1
    
    # This is the graph of what would happen if we had just bought and kept
    record(BuyAndHold=total_buy_and_hold)
    # All the records
    i = 0
    for stock in context.stocks :
        # This is the Price of the stock today
        # record(PRICE=data[stock].price)
        # This is the value of the portfolio including current value of stock + cash we have
        record(PortfolioValue=context.portfolio.positions_value \
               + int(context.portfolio.cash))
        # this is the max of capital, to compare against the buy and hold value and portfolio values
        #record(InitialCapital=context.max)
        i = i + 1
    #### End of buy and hold recording ####
    
    
    #### BUY ####
    i = -1
    for stock in context.stocks :
        i = i + 1
        if stock not in data:
            log.info(stock)
            continue
        if(exchange_time.day == context.last_traded_date[i]) :
            continue
        # If the price is greater that vwap 20, then buy.
        # This shows that price is moving up. So buy at upward momentum
        if data[stock].price < data[stock].vwap(20) or \
        data[stock].price > data[stock].vwap(20) :
            # Buy 10% of the cash you have. 
            # Need to make sure that you buy only once a day for this algo. 
            if (context.portfolio.positions[stock].amount == 0) :
                amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks))
            else :
                amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks) - context.portfolio.positions[stock].amount*context.portfolio.positions[stock].cost_basis)
            context.order_id = order_value(stock, 0.1*(amount_to_buy))
            
            # Check the order to make sure that it has bought.
            # Right now the filled below returns zero
            stock_order = get_order(context.order_id)
            # update the date. This is used to make sure we trade only once a day
            context.last_traded_date[i] = exchange_time.day
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                # log the order amount and the amount that is filled  
                message = ',buy,sid={sid}.stocks={stock},amount={amount}'  
                message = message.format(sid=stock,amount=stock_order.amount, stock=stock_order.filled) #cash=context.portfolio.cash)  
                log.info(message)    
                record(BUY=data[stock].price)

    #### END BUY ####
                
                
    #### SELL ####
                
    # Else check if the price is less that last 20 days
    # If so, it is going down. Time to sell it
    i = -1
    for stock in context.stocks :
        i = i + 1
        if stock not in data:
            log.info(stock)
            continue
        if(exchange_time.day == context.last_traded_date[i]) :
        #    continue
        # Maybe we should reduce it to less than 20 days so that we catch the momentum
        if data[stock].price > data[stock].vwap(10) :
            if (context.portfolio.positions[stock].amount == 0) :
                amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks))
            else :
                amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks) - context.portfolio.positions[stock].amount*context.portfolio.positions[stock].cost_basis)
            context.order_id = order_value(stock, -context.portfolio.positions[stock].amount*0.3)
            # Check the order to make sure that it has bought.
            # Right now the filled below returns zero
            stock_order = get_order(context.order_id)
            # update the date. This is used to make sure we trade only once a day
            context.last_traded_date[i] = exchange_time.day
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                # log the order amount and the amount that is filled  
                message = ',sell,sid={sid}.stocks={stock},amount={amount}'  
                message = message.format(sid=stock,amount=stock_order.amount, stock=stock_order.filled)  
                log.info(message)
                record(SELL=data[stock].price)

    
    
    
    #### END SELL ####

