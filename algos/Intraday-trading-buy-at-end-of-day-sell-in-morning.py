# Buy in the evening and then sell next day in the morning
# 
# Buy again the next day
# repeat

# The idea
    # we should buy in 10% increments (tunable) towards the end of the day if the price is going up 
    # every buy should be around 10 mins apart (tunable)
    # Thus we have 10 sales, by eod
    # Sell each tranche when they generate 1% profit the next day morning
    
# How the algo performsa
# 
    
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
    stocks = [sid(21724), sid(22257), sid(18522), sid(351), sid(6295), sid(20914)]
    context.stocks = stocks
    context.no_of_stocks = 6
    context.max = 30000
    context.min = 0
    context.profit = 0.01

    set_commission(commission.PerShare(cost=0.005))
    set_slippage(slippage.FixedSlippage(spread=0.00)) 
    context.last_sold_date = 0
    context.last_bought_date = 0
    # This defines when we actually want to buy the stock
    context.buy_time_hour = 10
    context.buy_time_minute = 10
    context.sell_time_hour = 12
    context.sell_time_minute = 10
    context.increment_to_buy = 0.1
    context.time_diff_between_buys = 10 # minutes
    context.buy = [0]*context.no_of_stocks 
    context.buy_price = [0]*context.no_of_stocks 
    # context.all_sids = [sid(21724), sid(3951), sid(6295), sid(23709), sid(12959)]  # add some specific securities

    context.buy_and_hold_number = [0]*context.no_of_stocks
    context.run_once = 1
    context.last_bought_date = [0]*context.no_of_stocks
    context.last_sold_date = [0]*context.no_of_stocks
    context.last_bought_price = [0]*context.no_of_stocks

    set_commission(commission.PerShare(cost=0.005))
    set_slippage(slippage.FixedSlippage(spread=0.00)) 

########### HANDLE_DATA() IS RUN ONCE PER MINUTE #######################
def handle_data(context, data):
    
    # If the stock has not yet started trading, exit it
    for stock in context.stocks :
        if stock not in data:
            log.info(stock)
            continue
    
    # Get the current exchange time, in local timezone: 
    exchange_time = pd.Timestamp(get_datetime()).tz_convert('US/Eastern')
    today = exchange_time.day + exchange_time.month*30 + exchange_time.year*365

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
        record(PRICE=data[stock].price)
        # This is the value of the portfolio including current value of stock + cash we have
        record(PortfolioValue=context.portfolio.positions_value \
               + int(context.portfolio.cash))
        # this is the max of capital, to compare against the buy and hold value and portfolio values
        #record(InitialCapital=context.max)
        i = i + 1
    
    if exchange_time.hour < context.buy_time_hour :
        return

    # First buy
    if exchange_time.hour == context.buy_time_hour and \
    exchange_time.minute == context.buy_time_minute:

        i = -1
        for stock in context.stocks :
            i = i + 1
#            # do all the buying here
#            if (context.portfolio.positions[stock].amount == 0) :
#                amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks))
#            else :
#                amount_to_buy = min(context.portfolio.cash, \
#                                (context.max/context.no_of_stocks) - context.portfolio.positions[stock].amount*data[stock].price)
#            context.order_id = order_value(stock, 0.19*(amount_to_buy))
#            # Check the order to make sure that it has bought. Right now the filled below returns zero
#            stock_order = get_order(context.order_id)
#            # The check below shows if the object exists. Only if it exists, should you 
#            # refer to it. Otherwise you will get a runtime error
#            if stock_order:
#                message = ',buy,stock={stock},amount to buy={amount_to_buy},price={price},amount={amount}'  
#                message = message.format(stock=stock,amount=stock_order.amount, price=data[stock].price,amount_to_buy=amount_to_buy)  
#                log.info(message)    
#                record(BUY=data[stock].price)
            context.last_bought_price[i] = data[stock].price
#                continue
            continue
    
    # Second buy
    i = -1
    for stock in context.stocks :
        i = i + 1
        if exchange_time.hour == context.buy_time_hour and \
        exchange_time.minute == context.buy_time_minute + 10 and \
        data[stock].price > context.last_bought_price[i] :
            # do all the buying here
            if (context.portfolio.positions[stock].amount == 0) :
                amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks))
            else :
                amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks) - context.portfolio.positions[stock].amount*data[stock].price)
            context.order_id = order_value(stock, 0.39*(amount_to_buy))
            # Check the order to make sure that it has bought. Right now the filled below returns zero
            stock_order = get_order(context.order_id)
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                message = ',buy,stock={stock},amount to buy={amount_to_buy},price={price},amount={amount}'  
                message = message.format(stock=stock,amount=stock_order.amount, price=data[stock].price,amount_to_buy=amount_to_buy)  
                log.info(message)    
                record(BUY=data[stock].price)
                context.last_bought_price[i] = data[stock].price
                continue
            continue

            
    # Third buy
    i = -1
    for stock in context.stocks :
        i = i + 1
        if exchange_time.hour == context.buy_time_hour and \
        exchange_time.minute == context.buy_time_minute + 20 and \
        data[stock].price > context.last_bought_price[i] :
            # do all the buying here
            if (context.portfolio.positions[stock].amount == 0) :
                amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks))
            else :
                amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks) - context.portfolio.positions[stock].amount*data[stock].price)
            context.order_id = order_value(stock, 0.59*(amount_to_buy))
            # Check the order to make sure that it has bought. Right now the filled below returns zero
            stock_order = get_order(context.order_id)
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                message = ',buy,stock={stock},amount to buy={amount_to_buy},price={price},amount={amount}'  
                message = message.format(stock=stock,amount=stock_order.amount, price=data[stock].price,amount_to_buy=amount_to_buy)  
                log.info(message)    
                record(BUY=data[stock].price)
                context.last_bought_price[i] = data[stock].price
                continue
            continue

    # Fourth buy
    i = -1
    for stock in context.stocks :
        i = i + 1
        if exchange_time.hour == context.buy_time_hour and \
        exchange_time.minute == context.buy_time_minute + 30 and \
        data[stock].price > context.last_bought_price[i] :
            # do all the buying here
            if (context.portfolio.positions[stock].amount == 0) :
                amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks))
            else :
                amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks) - context.portfolio.positions[stock].amount*data[stock].price)
            context.order_id = order_value(stock, 0.79*(amount_to_buy))
            # Check the order to make sure that it has bought. Right now the filled below returns zero
            stock_order = get_order(context.order_id)
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                message = ',buy,stock={stock},amount to buy={amount_to_buy},price={price},amount={amount}'  
                message = message.format(stock=stock,amount=stock_order.amount, price=data[stock].price,amount_to_buy=amount_to_buy)  
                log.info(message)    
                record(BUY=data[stock].price)
                context.last_bought_price[i] = data[stock].price
                continue
            continue

            

    # Fifth buy
    i = -1
    for stock in context.stocks :
        i = i + 1
        if exchange_time.hour == context.buy_time_hour and \
        exchange_time.minute == context.buy_time_minute + 40 and \
        data[stock].price > context.last_bought_price[i] :
            # do all the buying here
            if (context.portfolio.positions[stock].amount == 0) :
                amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks))
            else :
                amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks) - context.portfolio.positions[stock].amount*data[stock].price)
            context.order_id = order_value(stock, 0.94*(amount_to_buy))
            # Check the order to make sure that it has bought. Right now the filled below returns zero
            stock_order = get_order(context.order_id)
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                message = ',buy,stock={stock},amount to buy={amount_to_buy},price={price},amount={amount}'  
                message = message.format(stock=stock,amount=stock_order.amount, price=data[stock].price,amount_to_buy=amount_to_buy)  
                log.info(message)    
                record(BUY=data[stock].price)
                context.last_bought_price[i] = data[stock].price
                continue
            continue

            

            
    if exchange_time.hour == context.sell_time_hour and \
    exchange_time.minute == context.sell_time_minute:
        i = 0
        for stock in context.stocks :
            context.order_id = order(stock, -context.portfolio.positions[stock].amount)
            stock_order = get_order(context.order_id)
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                # log the order amount and the amount that is filled  
                message = ',sell,stock={stock},amount to sell={amount_to_sell},price={price},amount={amount}'  
                message = message.format(stock=stock,amount=stock_order.amount, price=data[stock].price,amount_to_sell=stock_order.amount*data[stock].price)  
                log.info(message)    
                record(SELL=data[stock].price)
        i = i + 1

