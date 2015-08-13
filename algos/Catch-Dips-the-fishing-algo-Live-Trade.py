''' 
    This algorithm buys and keeps stocks when they suddenlly dip below a certain threshold
    For example, buy only when the stock dips 20% below the moving average (20)
    Sell happens when it is 2X of what we bought it at

    Performance:
    Works pretty well, mostly being higher than the buy and hold stragety or almost as good
    Not working when we do nasdaq 100 due to some runtime error
'''
########### IMPORT THE LIBRARIES USED IN THE ALGORITHM ####################################
import datetime
import pytz
import pandas as pd
from zipline.utils.tradingcalendar import get_early_closes

########### INITIALZE() IS RUN ONCE (OR IN LIVE TRADING ONCE EACH DAY BEFORE TRADING) #####
def initialize(context):
    
    # context.stock           = sid(21724)
    context.max = 10000
    context.min = 0
    context.profit = 0.01
    # stocks = [sid(8554), sid(3951), sid(24), sid(23709), sid(18522), sid(6295)]
    stocks = [sid(21724), sid(22257), sid(18522), sid(351), sid(6295), sid(20914)]
    # stocks =     [sid(24),    sid(114),   sid(122),   sid(630),   sid(67),  \
    #                      sid(20680), sid(328),   sid(14328), sid(368),   sid(16841), \
    #                      sid(9883),  sid(337),   sid(38650), sid(739),   sid(27533), \
    #                      sid(3806),  sid(18529), sid(1209),  sid(1406),  sid(1419),  \
    #                      sid(15101), sid(17632), sid(39095), sid(1637),  sid(1900),  \
    #                      sid(32301), sid(18870), sid(14014), sid(25317), sid(36930), \
    #                      sid(12652), sid(26111), sid(24819), sid(24482), sid(2618),  \
    #                      sid(2663),  sid(27543), sid(1787) , sid(2696),  sid(42950), \
    #                      sid(20208), sid(2853),  sid(8816),  sid(12213), sid(3212),  \
    #                      sid(9736),  sid(23906), sid(26578), sid(22316), sid(13862), \
    #                      sid(3951),  sid(8655),  sid(25339), sid(4246),  sid(43405), \
    #                      sid(27357), sid(32046), sid(4485),  sid(43919), sid(4668),  \
    #                      sid(8677),  sid(22802), sid(3450),  sid(5061),  sid(5121),  \
    #                      sid(5149),  sid(5166),  sid(23709), sid(13905), sid(19926), \
    #                      sid(19725), sid(8857),  sid(5767),  sid(5787),  sid(19917), \
    #                      sid(6295),  sid(6413),  sid(6546),  sid(20281), sid(6683),  \
    #                      sid(26169), sid(6872),  sid(11901), sid(13940), sid(7061),  \
    #                      sid(15581), sid(24518), sid(7272),  sid(39840), sid(7671),  \
    #                      sid(27872), sid(8017),  sid(38817), sid(8045),  sid(8132),  \
    #                      sid(8158),  sid(24124), sid(8344),  sid(8352),  sid(14848)]
    context.stocks = stocks  # add some specific securities    
    context.no_of_stocks = 6

    context.buy_and_hold_number = [0]*context.no_of_stocks
    context.run_once = 1
    context.lastbuymonth = [0]*context.no_of_stocks
    context.lastbuyyear = [0]*context.no_of_stocks
    context.last_bought_date = [0]*context.no_of_stocks
    context.last_sold_date = [0]*context.no_of_stocks

    
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
    

    i = -1
    for stock in context.stocks :
        i = i + 1
        if data[stock].price < 0.8*data[stock].vwap(20) and \
        (int(today) > int(context.last_bought_date[i]) + 5) :
            # do all the buying here
            # amount to buy is lesser of the current cash we have and the 
            # money remaining of the total value we allocate for this stock
#            amount_to_buy = min(context.portfolio.cash, \
#                                (context.max/context.no_of_stocks - context.portfolio.positions[stock].amount*data[stock].price))
            if (context.portfolio.positions[stock].amount == 0) :
                amount_to_buy = min(context.portfolio.cash, (context.max/context.no_of_stocks))
            else :
                amount_to_buy = min(context.portfolio.cash, \
                                (context.max/context.no_of_stocks) - context.portfolio.positions[stock].amount*data[stock].price)
            context.order_id = order_value(stock, 0.3*(amount_to_buy))
            # Check the order to make sure that it has bought. Right now the filled below returns zero
            stock_order = get_order(context.order_id)
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                message = ',buy,stock={stock},amount to buy={amount_to_buy},price={price},amount={amount}'  
                message = message.format(stock=stock,amount=stock_order.amount, price=data[stock].price,amount_to_buy=amount_to_buy)  
                log.info(message)    
                record(BUY=data[stock].price)
                context.last_bought_date[i] = today 
                continue
        
            continue
# This doesnt give as good returns as the below except when we put the value to sell when three times
            
#    i = 0
#    for stock in context.stocks :
#        if data[stock].price > 3*context.portfolio.positions[stock].cost_basis and \
#        (int(today) > int(context.last_bought_date[i]) + 5) :
#            # do all the selling here
#            context.order_id = order(stock, -0.4*(context.portfolio.positions[stock].amount))
#            # Check the order to make sure that it has bought. Right now the filled below returns zero
#            stock_order = get_order(context.order_id)
#            # The check below shows if the object exists. Only if it exists, should you 
#            # refer to it. Otherwise you will get a runtime error
#            if stock_order:
#                message = ',sell,stock={stock},price={price},amount={amount}'  
#                message = message.format(stock=stock,amount=stock_order.amount, price=data[stock].price)  
#                log.info(message)    
#                #record(SELL=data[stock].price)
#                context.last_sold_date[i] = today 
#                continue
#        
#            continue
#        i = i + 1
   
    
    i = 0
    for stock in context.stocks :
        if data[stock].price > 2*context.portfolio.positions[stock].cost_basis :
            context.order_id = order(stock, -0.4*(context.portfolio.positions[stock].amount))
            # update the date. This is used to make sure we trade only once a day
            # Check the order to make sure that it has bought.
            # Right now the filled below returns zero
            stock_order = get_order(context.order_id)
            # The check below shows if the object exists. Only if it exists, should you 
            # refer to it. Otherwise you will get a runtime error
            if stock_order:
                # log the order amount and the amount that is filled  
                context.last_sold_date[i] = today 
                message = ',sell,sid={sid}.stocks={stock},amount={amount}'  
                message = message.format(sid=stock,amount=stock_order.amount, stock=stock_order.filled)  
                log.info(message)
                record(SELL=data[stock].price)
        i = i + 1

